import random, re, os
from flask import app, render_template, request, send_from_directory, session, redirect, url_for, current_app,Blueprint,jsonify,flash
from werkzeug.security import generate_password_hash,check_password_hash
from app.models.skills import Skills
from app.utils.file_handler import save_file
from slugify import slugify

from flask_login import current_user
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func
from app.models.jobApplication import JobApplication
from app.models.job_post import Job
from app.models.video_resume import VideoResume
from app.routes.video_resume import allowed_file
from app.services.email_service import send_otp_email, send_welcome_email, send_job_mail
from app.models import Students, EngineeringCollege, Company, student
from app.extensions.db import db
from flask_login import LoginManager



student_bp = Blueprint("student", __name__)

# ================= LOGIN ROUTE =================
@student_bp.route("/student-login", methods=["GET", "POST"])
def student_login():
    errors = []
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Find student by email
        student = Students.query.filter_by(email=email).first()

        # CORRECT WAY: Use check_password_hash for secure comparison
        if student and check_password_hash(student.password, password):
            session.clear() # Clear any old session data
            session["student_id"] = student.id
            session["full_name"] = student.full_name
            return redirect(url_for("student.student_dashboard"))
        else:
            errors.append("Invalid email or password")

    return render_template("student/student_auth/student_login.html", errors=errors)


@student_bp.route("/student-register", methods=["GET", "POST"])
def student_register():

    # 🔹 Load colleges always
    colleges = EngineeringCollege.query.order_by(
        EngineeringCollege.college_name
    ).all()

    engineering_branches = [
        "CE (Civil Engineering)",
        "CSE (Computer Science Engineering)",
        "IT (Information Technology)",
        "ME (Mechanical Engineering)",
        "EE (Electrical Engineering)",
        "ECE (Electronics & Communication)",
        "AI & DS",
        "Cyber Security"
    ]

    step = session.get("step", "email")
    errors = []

    if request.method == "POST":

        # ================= STEP 1 : SEND OTP =================
        if "send_otp" in request.form:
            email = request.form.get("email", "").strip()

            if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                errors.append("Enter a valid email")
                return render_template(
                    "student/student_auth/student_register.html",
                    step="email",
                    errors=errors,
                    colleges=colleges
                )
            print("EMAIL FROM SESSION:", email)

            # ❗ Prevent duplicate registration
            if Students.query.filter_by(email=email).first():
                errors.append("Email already registered")
                return render_template(
                    "student/student_auth/student_register.html",
                    step="email",
                    errors=errors,
                    colleges=colleges
                )

            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            session["email"] = email
            session["step"] = "otp"

            send_otp_email(email, otp)

            return render_template(
                "student/student_auth/student_register.html",
                step="otp",
                colleges=colleges
            )

        # ================= STEP 2 : VERIFY OTP =================
        if "verify_otp" in request.form:
            user_otp = request.form.get("otp", "").strip()

            if user_otp != session.get("otp"):
                return render_template(
                    "student/student_auth/student_register.html",
                    step="otp",
                    errors=["Invalid OTP"],
                    colleges=colleges
                )

            session.pop("otp")      # ✅ clear OTP
            session["step"] = "details"

            return render_template(
                "student/student_auth/student_register.html",
                step="details",
                branches=engineering_branches,
                colleges=colleges
            )

        # ================= STEP 3 : REGISTER =================
    if "register" in request.form:

        full_name = request.form.get("full_name", "").strip()
        mobile_no = request.form.get("mobile_no", "").strip()
        password = request.form.get("password", "")
        field = request.form.get("field")
        specialization = request.form.get("specialization")
        college_id = request.form.get("college_id")
        start_year = request.form.get("start_year")
        end_year = request.form.get("end_year")

        # ✅ get skills as list from form
        skills_list = request.form.getlist("skills")

        email = session.get("email")

        # ---------- VALIDATIONS ----------
        if not full_name:
            errors.append("Full name is required")

        if not mobile_no.isdigit() or len(mobile_no) != 10:
            errors.append("Mobile number must be 10 digits")

        password_pattern = re.compile(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
        )

        if not password_pattern.match(password):
            errors.append(
                "Password must contain uppercase, lowercase, number & special character"
            )

        if not college_id:
            errors.append("Please select a college")

        if errors:
            return render_template(
                "student/student_auth/student_register.html",
                step="details",
                errors=errors,
                branches=engineering_branches,
                colleges=colleges,
                selected_skills=skills_list
            )

        # ---------- SAVE ----------
        if not email:
            session.clear()
            return redirect(url_for("student.student_register"))
        slug = slugify(f"{full_name}-{mobile_no}")

        try:
            # ✅ FIRST create student (WITHOUT skills)
            student = Students(
                full_name=full_name,
                email=email,
                mobile_no=mobile_no,
                password=generate_password_hash(password),
                field=field,
                specialization=specialization,
                college_id=int(college_id),
                start_year=start_year,
                end_year=end_year,
                slug=slug
            )

            db.session.add(student)
            db.session.flush()   # 🔥 gets student.id before commit

            # ✅ NOW add skills properly (relationship-safe)
            for s in skills_list:
                if s.strip():
                    skill = Skills(
                        name=s.strip(),
                        student_id=student.id
                    )
                    db.session.add(skill)

            db.session.commit()

            print("✅ STUDENT SAVED:", student.id)

            send_welcome_email(email, full_name)

            # Clear temporary registration keys but keep the user logged in
            session.pop("otp", None)
            session.pop("email", None)
            session.pop("step", None)

            session["student_id"] = student.id
            session["full_name"] = student.full_name

            return redirect(url_for("student.student_dashboard"))

        except IntegrityError as e:
            db.session.rollback()
            print("❌ DB ERROR:", e.orig)

        return render_template(
            "student/student_auth/student_register.html",
            step="details",
            errors=["Email / mobile already exists or invalid college"],
            branches=engineering_branches,
            colleges=colleges
        )

        # ================= GET / FALLBACK =================
    return render_template(
            "student/student_auth/student_register.html",
            step=step,
            branches=engineering_branches,
            colleges=colleges
        )

@student_bp.route("/student-dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("home.login"))

    student_id = session["student_id"]

    # Get logged in student
    student = Students.query.get_or_404(student_id)

    # ✅ Count applied jobs
    applied_jobs_count = JobApplication.query.filter_by(
        student_id=student_id
    ).count()
    offers_count = JobApplication.query.filter(
        JobApplication.student_id == student_id,
        func.lower(JobApplication.status).in_(["approved", "selected"])
    ).count()
    active_students_count = Students.query.count()
    hiring_companies_count = Company.query.count()
    active_job_postings_count = Job.query.filter_by(status="ACTIVE").count()

    # ✅ Profile Completion Logic

    basic_info = 100 if (
        student.full_name and
        student.email and
        student.mobile_no and
        student.field
    ) else 0

    objective = 100 if student.objective else 0

    social_links = 100 if (
        student.github or
        student.linkedin or
        student.portfolio
    ) else 0

    resume = 100 if student.resume_file else 0
    video = 100 if student.video_resume else 0

    projects = 100 if len(student.projects) > 0 else 0
    skills = 100 if len(student.skills) > 0 else 0
    certificates = 100 if len(student.certificate) > 0 else 0

    profile_data = [
        basic_info,
        objective,
        social_links,
        resume,
        video,
        projects,
        skills,
        certificates
    ]

    total_score = sum(profile_data) // len(profile_data)

    # Recommended jobs based on student skill overlap
    student_skills = {
        skill.name.strip().lower()
        for skill in student.skills
        if skill.name and skill.name.strip()
    }

    active_jobs = Job.query.filter_by(status="ACTIVE").order_by(Job.created_at.desc()).all()
    scored_jobs = []

    for job in active_jobs:
        job_skills = {
            s.strip().lower()
            for s in (job.skills or "").split(",")
            if s.strip()
        }

        if not student_skills or not job_skills:
            continue

        overlap_count = len(student_skills & job_skills)
        if overlap_count == 0:
            continue

        match_score = int((overlap_count / len(job_skills)) * 100)
        scored_jobs.append((match_score, job))

    scored_jobs.sort(key=lambda item: item[0], reverse=True)
    recommended_jobs = [
        {"job": job, "match_score": score}
        for score, job in scored_jobs[:4]
    ]

    # Fallback to latest active jobs if there are no skill matches
    if not recommended_jobs:
        recommended_jobs = [
            {"job": job, "match_score": None}
            for job in active_jobs[:4]
        ]

    return render_template(
        "student/student_auth/studentPage.html",
        applied_jobs_count=applied_jobs_count,
        offers_count=offers_count,
        active_students_count=active_students_count,
        hiring_companies_count=hiring_companies_count,
        active_job_postings_count=active_job_postings_count,
        recommended_jobs=recommended_jobs,
        profile_data=profile_data,
        total_score=total_score,
        student=student
    )
@student_bp.route("/student-analytics/<int:total_score>")
def student_analytics(total_score):
    if "student_id" not in session:
        return redirect(url_for("home.login"))

    student = Students.query.get_or_404(session["student_id"])

    basic_info = 100 if (
        student.full_name and
        student.email and
        student.mobile_no and
        student.field
    ) else 0
    objective = 100 if student.objective else 0
    social_links = 100 if (student.github or student.linkedin or student.portfolio) else 0
    resume = 100 if student.resume_file else 0
    video = 100 if student.video_resume else 0
    projects = 100 if len(student.projects) > 0 else 0
    skills = 100 if len(student.skills) > 0 else 0
    certificates = 100 if len(student.certificate) > 0 else 0

    profile_data = [
        basic_info,
        objective,
        social_links,
        resume,
        video,
        projects,
        skills,
        certificates
    ]
    total_score = sum(profile_data) // len(profile_data)

    return render_template(
        "student/student_auth/profileAnalysis.html",
        student=student,
        total_score=total_score,
        profile_data=profile_data
    )
  
from app.models.job_post import Job
@student_bp.route("/student-jobs")
def student_job():

    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("student.student_login"))

    student = Students.query.get(student_id)

    if not student:
        return redirect(url_for("student.student_login"))

    applied_jobs_count = JobApplication.query.filter_by(
        student_id=student_id
    ).count()
    active_jobs_count = Job.query.filter_by(status="ACTIVE").count()

    student_skills = {
        skill.name.strip().lower()
        for skill in student.skills
        if skill.name
    }

    q = (request.args.get("q") or "").strip()
    job_type = (request.args.get("job_type") or "").strip()
    experience = (request.args.get("experience") or "").strip()
    work_mode = (request.args.get("work_mode") or "").strip()
    salary_range = (request.args.get("salary_range") or "").strip()
    sort = ((request.args.get("sort") or "recent").strip().lower())

    if sort not in {"recent", "relevant", "salary", "trending"}:
        sort = "recent"

    query = Job.query.filter_by(status="ACTIVE").outerjoin(Company)

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Job.job_title.ilike(like_q),
                Job.skills.ilike(like_q),
                Job.location.ilike(like_q),
                Job.description.ilike(like_q),
                Company.company_name.ilike(like_q)
            )
        )

    if job_type:
        query = query.filter(Job.job_type == job_type)

    if experience:
        query = query.filter(Job.experience == experience)

    jobs = query.all()

    if work_mode:
        def normalize_mode(value):
            return re.sub(r"[^a-z]", "", (value or "").lower())

        selected_mode = normalize_mode(work_mode)
        jobs = [
            job for job in jobs
            if normalize_mode(job.work_mode) == selected_mode
        ]

    def parse_salary_lpa(salary_text):
        if not salary_text:
            return None
        nums = re.findall(r"\d+(?:\.\d+)?", salary_text)
        if not nums:
            return None
        values = [float(n) for n in nums]
        if "k" in salary_text.lower() and "lpa" not in salary_text.lower():
            return max(values) / 100.0
        return max(values)

    def compute_match_score(job):
        job_skills = {
            s.strip().lower()
            for s in (job.skills or "").split(",")
            if s.strip()
        }
        if not student_skills or not job_skills:
            return 0
        overlap = len(student_skills & job_skills)
        if overlap == 0:
            return 0
        return int((overlap / len(job_skills)) * 100)

    matched_jobs = []
    for job in jobs:
        match_score = compute_match_score(job)
        salary_lpa = parse_salary_lpa(job.salary)
        trend_score = match_score + min((job.openings or 0) * 5, 30)
        matched_jobs.append(
            {
                "job": job,
                "match_score": match_score,
                "salary_lpa": salary_lpa,
                "trend_score": trend_score
            }
        )

    if salary_range:
        def in_salary_range(item):
            salary_val = item["salary_lpa"]
            if salary_val is None:
                return False
            if salary_range == "0-3 LPA":
                return 0 <= salary_val <= 3
            if salary_range == "3-6 LPA":
                return 3 < salary_val <= 6
            if salary_range == "6-10 LPA":
                return 6 < salary_val <= 10
            if salary_range == "10+ LPA":
                return salary_val > 10
            return True

        matched_jobs = [item for item in matched_jobs if in_salary_range(item)]

    has_filters = any([q, job_type, experience, work_mode, salary_range])
    if not has_filters:
        skill_matched = [item for item in matched_jobs if item["match_score"] > 0]
        if skill_matched:
            matched_jobs = skill_matched

    if sort == "relevant":
        matched_jobs.sort(
            key=lambda item: (item["match_score"], item["job"].created_at or ""),
            reverse=True
        )
    elif sort == "salary":
        matched_jobs.sort(
            key=lambda item: (item["salary_lpa"] is not None, item["salary_lpa"] or 0),
            reverse=True
        )
    elif sort == "trending":
        matched_jobs.sort(
            key=lambda item: (item["trend_score"], item["job"].created_at or ""),
            reverse=True
        )
    else:
        matched_jobs.sort(
            key=lambda item: item["job"].created_at or "",
            reverse=True
        )

    return render_template(
        "student/student_job/student_job.html",
        matched_jobs=matched_jobs,
        student=student,
        applied_jobs_count=applied_jobs_count,
        active_jobs_count=active_jobs_count,
        filter_values={
            "q": q,
            "job_type": job_type,
            "experience": experience,
            "work_mode": work_mode,
            "salary_range": salary_range,
            "sort": sort
        }
    )
@student_bp.route("/job/<int:job_id>")
def job_details(job_id):
    """View detailed information about a specific job"""
    if "student_id" not in session:
        return redirect(url_for("student.student_login"))

    job = Job.query.get_or_404(job_id)
    student = Students.query.get_or_404(session["student_id"])
    
    # Check if student has already applied
    applied = JobApplication.query.filter_by(
        student_id=student.id,
        job_id=job_id
    ).first()

    return render_template(
        "student/student_job/job_details.html",
        job=job,
        student=student,
        applied=applied
    )

@student_bp.route("/apply-job/<int:job_id>", methods=["POST"])
def apply_job(job_id):

    if "student_id" not in session:
        flash("Login required", "danger")
        return redirect(url_for("home.login"))

    student = Students.query.get_or_404(session["student_id"])

    # ✅ Check job exists
    job = Job.query.get_or_404(job_id)

    application = JobApplication(
        student_id=student.id,
        job_id=job.id,
        student_email=student.email,
        resume=student.resume_file,
        video_resume=student.video_resume
    )

    try:
        db.session.add(application)
        db.session.commit()
        try:
            send_job_mail(student, job)
        except Exception as mail_error:
            print("Job mail error:", mail_error)
    except Exception as e:
        db.session.rollback()
        print("❌ DB ERROR:", e)
        flash("Something went wrong", "danger")
        return redirect(url_for("student.student_job"))

    flash("✅ Job applied successfully", "success")
    return redirect(url_for("student.my_application"))



@student_bp.route("/profile")
def view_profile():
    if "student_id" not in session:
        flash("Login required", "danger")
        return redirect(url_for("home.login"))

    student = Students.query.get(session["student_id"])

    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("home.login"))

    return render_template("profile/view_profile.html", student=student)

@student_bp.route("/profile/update", methods=["GET", "POST"])

def update_profile():
    if "student_id" not in session:
        return redirect(url_for("home.login"))

    student = Students.query.get_or_404(session["student_id"])

    if request.method == "POST":

        # ---------------- BASIC DETAILS ----------------
        student.full_name = request.form.get("full_name")
        student.mobile_no = request.form.get("mobile_no")
        student.field = request.form.get("field")
        student.specialization = request.form.get("specialization")
        student.start_year = request.form.get("start_year")
        student.end_year = request.form.get("end_year")

        # ---------------- PROFILE DETAILS ----------------
        student.objective = request.form.get("objective")
        # Skills relationship must be updated as a collection, not assigned a string.
        skills_list = request.form.getlist("skills")
        student.internship = request.form.get("internship")
        student.certifications = request.form.get("certifications")

        # Replace existing skills with submitted ones
        student.skills.clear()
        for s in skills_list:
            s = (s or "").strip()
            if s:
                from app.models.skills import Skills
                student.skills.append(Skills(name=s))


        student.github = request.form.get("github")
        student.linkedin = request.form.get("linkedin")
        student.languages = request.form.get("languages")
        student.portfolio = request.form.get("portfolio")

        # ---------------- RESUME UPLOAD ----------------
        if "resume_file" in request.files:
            file = request.files["resume_file"]
            if file and file.filename:
                student.resume_file = save_file(file, "resumes")

        # ---------------- VIDEO RESUME UPLOAD ----------------
        if "video_resume" in request.files:
            file = request.files["video_resume"]
            if file and file.filename:
                student.video_resume = save_file(file, "videos")

        # ---------------- MANDATORY VALIDATION ----------------
        if not student.resume_file:
            flash("Please upload your Resume (PDF)", "danger")
            return redirect(url_for("student.view_profile"))

        if not student.video_resume:
            flash("Please upload your Video Resume", "danger")
            return redirect(url_for("student.view_profile"))

        if not student.portfolio:
            flash("Please add your Portfolio link", "danger")
            return redirect(url_for("student.view_profile"))

          # 🔥 FIX PROJECTS
        from app.models.project import Projects

        projects_text = request.form.get("projects")
        student.projects.clear()

        if projects_text:
            project = Projects(
            title="Project",
            description=projects_text
        )
        student.projects.append(project)
        # ---------------- SAVE ----------------
        db.session.commit()
        flash("✅ Profile updated successfully", "success")
        return redirect(url_for("student.student_dashboard"))

    # ---------------- GET REQUEST ----------------
    return render_template(
        "profile/update_profile.html",
        student=student
    )
def is_profile_complete(self):
    return all([
        self.full_name,
        self.email,
        self.mobile_no,
        self.education,
        bool(self.skills)
    ])

@student_bp.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply_job_page(job_id):

    if "student_id" not in session:
        return redirect(url_for("home.login"))

    student_id = session["student_id"]

    student = Students.query.get_or_404(student_id)
    job = Job.query.get_or_404(job_id)

    # Check if already applied
    existing_application = JobApplication.query.filter_by(
        student_id=student_id,
        job_id=job_id
    ).first()

    if request.method == "POST":

        if existing_application:
            flash("You have already applied for this job.", "warning")
            return redirect(url_for("student.student_dashboard"))

        # Create new application (include student contact/profile fields)
        new_application = JobApplication(
            student_id=student_id,
            job_id=job_id,
            student_email=student.email,
            resume=student.resume_file,
            video_resume=student.video_resume,
            portfolio_link=student.portfolio
        )

        db.session.add(new_application)
        db.session.commit()
        try:
            send_job_mail(student, job)
        except Exception as mail_error:
            print("Job mail error:", mail_error)

        flash("Application submitted successfully!", "success")
        return redirect(url_for("student.my_application"))

    return render_template(
        "student/student_job/apply_job.html",
        job=job,
        student=student,
        already_applied=bool(existing_application)
    )


@student_bp.route("/student/logout", methods=["POST"])
def student_logout():

    if "student_id" not in session:
        return redirect(url_for("home.login"))

    # Clear session
    session.clear()

    flash("Logged out successfully.", "success")
    return redirect(url_for("home.login"))

@student_bp.route("/my-applications", methods=["GET"])
def my_application():
    """Display all job applications for the current student"""
    
    if "student_id" not in session:
        return redirect(url_for("student.student_login"))

    applications = JobApplication.query.filter_by(
        student_id=session["student_id"]
    ).order_by(JobApplication.applied_at.desc()).all()

    return render_template(
        "student/student_job/my_application.html",
        applications=applications
    )
@student_bp.route("/view-applications", methods=["GET"])
def view_application():
    """View all job applications and their status"""
    
    if "student_id" not in session:
        return redirect(url_for("student.student_login"))

    student = Students.query.get_or_404(session["student_id"])
    applications = JobApplication.query.filter_by(
        student_id=session["student_id"]
    ).order_by(JobApplication.applied_at.desc()).all()

    return render_template(
        "student/student_job/my_application.html",
        student=student,
        applications=applications
    )

