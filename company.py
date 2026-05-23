import random, re
from flask import (
    render_template, request, session,
    redirect, url_for, Blueprint, flash
)
from sqlalchemy import func
from app.models.jobApplication import JobApplication
from app.models.job_post import Job
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from app.extensions.db import db
from app.services.email_service import send_otp_email, send_approval_email
from app.models import Company

# ================= BLUEPRINT =================
company_bp = Blueprint(
    "company",
    __name__,
    url_prefix="/company"
)

# ================= INDUSTRIES =================
INDUSTRIES = [
    "Information Technology",
    "Finance",
    "Healthcare",
    "Education",
    "Manufacturing",
    "Marketing",
    "Consulting",
    "E-Commerce",
    "Startup",
    "Other"
]

# ================= REGISTER + LOGIN (SAME PAGE) =================
@company_bp.route("/register", methods=["GET", "POST"])
def company_register():

    step = session.get("step", "email")
    error = None

    if request.method == "POST":

        # ---------- STEP 1 : SEND OTP ----------
        if "send_otp" in request.form:
            email = request.form.get("email")

            if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                error = "Enter a valid email address"
                return render_template(
        "company/company_register.html",
        step="email",
        error=error
    )

            # check if company already exists
            if Company.query.filter_by(email=email).first():
                session["login_email"] = email
                session["step"] = "login"
                return render_template(
                    "company/company_register.html",
                    step="login"
                )

            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            session["email"] = email
            session["step"] = "otp"

            send_otp_email(email, otp)

            return render_template(
                "company/company_register.html",
                step="otp"
            )

        # ---------- STEP 2 : VERIFY OTP ----------
        if "verify_otp" in request.form:
            if request.form.get("otp") != session.get("otp"):
                return render_template(
                    "company/company_register.html",
                    step="otp",
                    error="Invalid OTP"
                )

            session["step"] = "details"
            return render_template(
                "company/company_register.html",
                step="details",
                industries=INDUSTRIES
            )

        # ---------- STEP 3 : REGISTER ----------
        if "register_company" in request.form:
            company_name = request.form.get("company_name")
            hr_name = request.form.get("hr_name")
            mobile_no = request.form.get("mobile_no")
            industry_type = request.form.get("industry_type")
            website = request.form.get("website")
            password = request.form.get("password")
            email = session.get("email")

            if not all([company_name, hr_name, mobile_no, password]):
                error = "All fields are required"
            elif not mobile_no.isdigit() or len(mobile_no) != 10:
                error = "Mobile number must be 10 digits"
            elif industry_type not in INDUSTRIES:
                error = "Invalid industry selected"
            elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
                error = "Password must contain uppercase, lowercase & number"

            if error:
                print("Validation error:", error)
                return render_template(
                    "company/company_register.html",
                    step="details",
                    error=error,
                    industries=INDUSTRIES
                )

            try:
                company = Company(
                    company_name=company_name,
                    hr_name=hr_name,
                    email=email,
                    mobile_no=mobile_no,
                    industry_type=industry_type,
                    website=website,
                    password=generate_password_hash(password),
                    is_verified=True
                )

                db.session.add(company)
                db.session.commit()

                session.clear()
                session["company_id"] = company.id
                return redirect(url_for("company.company_dashboard"))

            except IntegrityError:
                db.session.rollback()
                return render_template(
                    "company/company_register.html",
                    step="details",
                    error="Company already registered",
                    industries=INDUSTRIES
                )

        # ---------- LOGIN (SAME PAGE) ----------
        if "login_company" in request.form:
            email = session.get("login_email")
            password = request.form.get("password")

            company = Company.query.filter_by(email=email).first()

            if not company or not check_password_hash(company.password, password):
                return render_template(
                    "company/company_register.html",
                    step="login",
                    error="Invalid password"
                )

            session.clear()
            session["company_id"] = company.id
            return redirect(url_for("company.company_dashboard"))

    # ---------- GET ----------
    return render_template(
        "company/company_register.html",
        step=step,
        industries=INDUSTRIES
    )

# ================= DASHBOARD =================

@company_bp.route("/dashboard")
def company_dashboard():

    # 🔐 Check Login
    if "company_id" not in session:
        return redirect(url_for("company.login"))

    company_id = session["company_id"]

    # 🔹 Active Jobs
    active_jobs = Job.query.filter_by(
        company_id=company_id,
        status="ACTIVE"
    ).count()

    # 🔹 Total Applications
    total_applications = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id)\
        .scalar()

    total_applicants = db.session.query(func.count(func.distinct(JobApplication.student_id)))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id)\
        .scalar()

    # 🔹 Application Status Analytics
    approved_count = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id,
                func.lower(JobApplication.status) == "approved")\
        .scalar()

    rejected_count = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id,
                func.lower(JobApplication.status) == "rejected")\
        .scalar()

    pending_count = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id,
                func.lower(JobApplication.status) == "pending")\
        .scalar()

    # Job performance: top jobs by application volume
    job_performance_rows = (
        db.session.query(
            Job,
            func.count(JobApplication.id).label("application_count")
        )
        .outerjoin(JobApplication, JobApplication.job_id == Job.id)
        .filter(Job.company_id == company_id)
        .group_by(Job.id)
        .order_by(func.count(JobApplication.id).desc(), Job.created_at.desc())
        .limit(6)
        .all()
    )

    max_apps = max([row.application_count for row in job_performance_rows], default=1)
    job_performance = []
    for row in job_performance_rows:
        percent = int((row.application_count / max_apps) * 100) if max_apps else 0
        job_performance.append({
            "job_id": row.Job.id,
            "job_title": row.Job.job_title,
            "status": row.Job.status or "N/A",
            "application_count": row.application_count,
            "progress": max(8, percent)
        })

    # Recent applications across all jobs of current company
    recent_applications = (
        JobApplication.query
        .join(Job, Job.id == JobApplication.job_id)
        .filter(Job.company_id == company_id)
        .order_by(JobApplication.applied_at.desc())
        .limit(8)
        .all()
    )

    company = Company.query.get(company_id)

    return render_template(
        "company/companyPage.html",
        company=company,
        active_jobs=active_jobs,
        total_applications=total_applications,
        total_applicants=total_applicants,
        approved_count=approved_count,
        rejected_count=rejected_count,
        pending_count=pending_count,
        job_performance=job_performance,
        recent_applications=recent_applications
    )

# ================= LOGOUT =================
@company_bp.route("/logout", methods=["GET", "POST"])
def company_logout():
    # Get company info before clearing for logging
    company_id = session.get("company_id")
    company_name = session.get("company_name")

    # Clear session
    session.clear()

    # Log logout action if company was logged in
    if company_id:
        print(f"✅ Company logged out: ID {company_id}, Name: {company_name}")
        flash("Logged out successfully. See you soon!", "success")
    else:
        flash("You were already logged out.", "info")

    return redirect(url_for("home.login"))




@company_bp.route("/job-post", methods=["GET", "POST"])

def post_job():
    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    if request.method == "POST":

        # ✅ Required field
        job_title = request.form.get("job_title", "").strip()
        if not job_title:
            return render_template(
                "company/job_post.html",
                error="Job title is required"
            )

        # ✅ Handle deadline BEFORE creating Job
        deadline_str = request.form.get("deadline", "").strip()
        if not deadline_str:
            return render_template(
                "company/job_post.html",
                error="Application deadline is required."
            )

        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except ValueError:
            return render_template(
                "company/job_post.html",
                error="Invalid deadline format."
            )

        if deadline < date.today():
            return render_template(
                "company/job_post.html",
                error="Deadline cannot be in the past."
            )

        # ✅ Create Job object
        job = Job(
            company_id=session["company_id"],
            job_title=job_title,
            job_type=request.form.get("job_type", "").strip(),
            work_mode=request.form.get("work_mode", "").strip(),
            location=request.form.get("location", "").strip(),
            experience=request.form.get("experience", "").strip(),
            education=request.form.get("education", "").strip(),

            # ✅ string (not tuple)
            skills=request.form.get("skills", "").strip(),

            description=request.form.get("description", "").strip(),
            salary=request.form.get("salary", "").strip(),
            openings=request.form.get("openings", "").strip(),
            selection_process=request.form.get("selection_process", "").strip(),

            deadline=deadline,
            created_at=datetime.utcnow(),
            status="ACTIVE"
        )

        try:
            db.session.add(job)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("❌ DB ERROR:", e)
            return render_template(
                "company/job_post.html",
                error="Something went wrong while posting the job"
            )

        flash("Job posted successfully.", "success")
        return redirect(url_for("company.company_my_jobs"))

    # ✅ GET request
    return render_template("company/job_post.html")
 # ================= DEDICATED LOGIN ROUTE =================
@company_bp.route("/login", methods=["GET", "POST"])
def company_login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        company = Company.query.filter_by(email=email).first()
        print("Company found:", company)

        if not company:
            error = "Company not registered"
        elif not check_password_hash(company.password, password):
            error = "Invalid password"
        else:
            session.clear()
            session["company_id"] = company.id
            session["company_name"] = company.company_name
            print(f"✅ Company logged in: ID {company.id}, Name: {company.company_name}")
            return redirect(url_for("company.company_dashboard"))

    return render_template("company/company_login.html", error=error, industries=INDUSTRIES)

@company_bp.route("/jobs")
def all_jobs():
    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    company_id = session["company_id"]
    jobs = (
        Job.query
        .filter_by(company_id=company_id, status="ACTIVE")
        .order_by(Job.created_at.desc())
        .all()
    )
    return render_template("student/student_job/jobs.html", jobs=jobs)

@company_bp.route("/company/my-jobs")
def company_my_jobs():

    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    company_id = session["company_id"]

    jobs = Job.query.filter_by(company_id=company_id).order_by(Job.created_at.desc()).all()

    return render_template(
        "company/my_jobs.html",
        jobs=jobs
    )

@company_bp.route("/company/job/<int:job_id>/applications")
def view_job_applications(job_id):

    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    company_id = session["company_id"]

    # 🔒 Security Check – Job must belong to this company
    job = Job.query.filter_by(
        id=job_id,
        company_id=company_id
    ).first_or_404()

    # Get all applications for this job
    applications = JobApplication.query.filter_by(
        job_id=job.id
    ).order_by(JobApplication.applied_at.desc()).all()

    active_applications = []
    decided_applications = []
    for application in applications:
        current_status = (application.status or "").strip().lower()
        if current_status in ("approved", "selected", "rejected"):
            decided_applications.append(application)
        else:
            active_applications.append(application)

    return render_template(
        "company/job_applications.html",
        job=job,
        applications=active_applications,
        decided_applications=decided_applications
    )


@company_bp.route("/company/applications/<int:application_id>/status", methods=["POST"])
def update_application_status(application_id):
    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    company_id = session["company_id"]
    new_status = (request.form.get("status") or "").strip().lower()
    allowed_status = {"approved": "Approved", "rejected": "Rejected"}

    if new_status not in allowed_status:
        flash("Invalid application status.", "danger")
        return redirect(url_for("company.company_my_jobs"))

    application = (
        JobApplication.query
        .join(Job, Job.id == JobApplication.job_id)
        .filter(
            JobApplication.id == application_id,
            Job.company_id == company_id
        )
        .first_or_404()
    )

    application.status = allowed_status[new_status]
    db.session.commit()

    try:
        send_approval_email(
            student_email=application.student_email,
            student_name=application.student.full_name if application.student else "Student",
            job_title=application.job.job_title if application.job else "Job",
            company_name=application.job.company.company_name if application.job and application.job.company else "Company",
            status=application.status
        )
    except Exception as mail_error:
        print("Approval mail error:", mail_error)

    flash(f"Application marked as {application.status}.", "success")
    return redirect(url_for("company.view_job_applications", job_id=application.job_id))


@company_bp.route("/company/applications/<int:application_id>/approve", methods=["POST"])
def approve_application(application_id):
    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    company_id = session["company_id"]
    application = (
        JobApplication.query
        .join(Job, Job.id == JobApplication.job_id)
        .filter(
            JobApplication.id == application_id,
            Job.company_id == company_id
        )
        .first_or_404()
    )

    application.status = "Approved"
    db.session.commit()

    try:
        send_approval_email(
            student_email=application.student_email,
            student_name=application.student.full_name if application.student else "Student",
            job_title=application.job.job_title if application.job else "Job",
            company_name=application.job.company.company_name if application.job and application.job.company else "Company",
            status=application.status
        )
    except Exception as mail_error:
        print("Approval mail error:", mail_error)

    flash("Application approved and email sent.", "success")
    return redirect(url_for("company.view_job_applications", job_id=application.job_id))


@company_bp.route("/company/applications/<int:application_id>/reject", methods=["POST"])
def reject_application(application_id):
    if "company_id" not in session:
        return redirect(url_for("company.company_login"))

    company_id = session["company_id"]
    application = (
        JobApplication.query
        .join(Job, Job.id == JobApplication.job_id)
        .filter(
            JobApplication.id == application_id,
            Job.company_id == company_id
        )
        .first_or_404()
    )

    application.status = "Rejected"
    db.session.commit()

    flash("Application rejected.", "warning")
    return redirect(url_for("company.view_job_applications", job_id=application.job_id))

@company_bp.route("/analytics")
def company_analytics():

    # 🔐 Login Check
    if "company_id" not in session:
        return redirect(url_for("company.login"))

    company_id = session["company_id"]

    # 🔹 Total Jobs
    total_jobs = Job.query.filter_by(company_id=company_id).count()

    # 🔹 Active Jobs
    active_jobs = Job.query.filter_by(
        company_id=company_id,
        status="open"
    ).count()

    # 🔹 Total Applications
    total_applications = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id)\
        .scalar()

    # 🔹 Status Based Counts
    approved = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id,
                JobApplication.status == "approved")\
        .scalar()

    rejected = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id,
                JobApplication.status == "rejected")\
        .scalar()

    pending = db.session.query(func.count(JobApplication.id))\
        .join(Job, Job.id == JobApplication.job_id)\
        .filter(Job.company_id == company_id,
                JobApplication.status == "pending")\
        .scalar()

    return render_template(
        "company/company_analytics.html",
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        approved=approved,
        rejected=rejected,
        pending=pending
    )

