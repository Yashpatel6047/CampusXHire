import os
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_
from functools import wraps
from app.models import Company, Job, Students
from app.models.jobApplication import JobApplication

auth_bp = Blueprint("auth", __name__)

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please login as admin to continue.", "warning")
            return redirect(url_for("auth.admin_login"))
        return view_func(*args, **kwargs)
    return wrapper
@auth_bp.route("/admin")
@admin_required
def admin_dashboard1():
    return render_template("admin/dashboard.html")


@auth_bp.route("/")
def home():
    return render_template("Start/Home.html")


@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("auth.admin_dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        admin_email = os.getenv("ADMIN_EMAIL", "admin@campusxhire.com").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123").strip()

        if email == admin_email and password == admin_password:
            session["is_admin"] = True
            session["admin_email"] = admin_email
            flash("Welcome to admin panel.", "success")
            return redirect(url_for("auth.admin_dashboard"))

        flash("Invalid admin credentials.", "danger")

    return render_template("admin/admin_login.html")


@auth_bp.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_email", None)
    flash("Admin logged out.", "success")
    return redirect(url_for("home.login"))


@auth_bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    total_students = Students.query.count()
    total_companies = Company.query.count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(status="ACTIVE").count()
    total_applications = JobApplication.query.count()

    pending_applications = JobApplication.query.filter_by(status="Applied").count()
    approved_applications = JobApplication.query.filter_by(status="Approved").count()
    rejected_applications = JobApplication.query.filter_by(status="Rejected").count()

    recent_students = Students.query.order_by(Students.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_applications = JobApplication.query.order_by(JobApplication.applied_at.desc()).limit(8).all()

    return render_template(
        "admin/admin_dashboard.html",
        total_students=total_students,
        total_companies=total_companies,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        pending_applications=pending_applications,
        approved_applications=approved_applications,
        rejected_applications=rejected_applications,
        recent_students=recent_students,
        recent_jobs=recent_jobs,
        recent_applications=recent_applications,
    )


@auth_bp.route("/admin/students")
@admin_required
def admin_students():
    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = Students.query
    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Students.full_name.ilike(like_q),
                Students.email.ilike(like_q),
                Students.mobile_no.ilike(like_q),
                Students.field.ilike(like_q),
            )
        )

    pagination = query.order_by(Students.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/admin_students.html", pagination=pagination, students=pagination.items, q=q)


@auth_bp.route("/admin/companies")
@admin_required
def admin_companies():
    q = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = Company.query
    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Company.company_name.ilike(like_q),
                Company.email.ilike(like_q),
                Company.hr_name.ilike(like_q),
                Company.industry_type.ilike(like_q),
            )
        )

    pagination = query.order_by(Company.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/admin_companies.html", pagination=pagination, companies=pagination.items, q=q)


@auth_bp.route("/admin/jobs")
@admin_required
def admin_jobs():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = Job.query.outerjoin(Company)
    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Job.job_title.ilike(like_q),
                Job.location.ilike(like_q),
                Job.skills.ilike(like_q),
                Company.company_name.ilike(like_q),
            )
        )
    if status:
        query = query.filter(Job.status == status)

    pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template(
        "admin/admin_jobs.html",
        pagination=pagination,
        jobs=pagination.items,
        q=q,
        status=status,
    )


@auth_bp.route("/admin/applications")
@admin_required
def admin_applications():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)

    query = JobApplication.query.join(Students).join(Job).outerjoin(Company)
    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                Students.full_name.ilike(like_q),
                Students.email.ilike(like_q),
                Job.job_title.ilike(like_q),
                Company.company_name.ilike(like_q),
            )
        )
    if status:
        query = query.filter(JobApplication.status == status)

    pagination = query.order_by(JobApplication.applied_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template(
        "admin/admin_applications.html",
        pagination=pagination,
        applications=pagination.items,
        q=q,
        status=status,
    )
