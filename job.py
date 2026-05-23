from tkinter import Message
from flask import Flask,Blueprint, flash, redirect, render_template, session, url_for
from app.utils.emails import send_approval_email,send_rejection_email

from app.extensions import db, mail
from app.models import jobApplication
from app.models.jobApplication import JobApplication
# from app.models.job_post import Jobs
from app.models.job_post import Job
from app.models.student import Students
job_bp = Blueprint('job',__name__)

@job_bp.route("/my-applications")
def my_applications(job_id):

    # 🔒 Login check (student side)
    if "student_id" not in session:
        flash("Login required", "danger")
        return redirect(url_for("auth.login"))

    student_id = session["student_id"]

    applications = (
        JobApplication.query
        .filter_by(student_id=student_id)
        .order_by(JobApplication.applied_at.desc())
        .all()
    )
    job = Job.query.get_or_404(job.job_id)

    return render_template(
        "student/student_job/my_applications.html",
        applications=applications,
        jobs=job,
        student=Students
    )

job_bp.route("/job/email/apply")
def send_job_email(student, job):

    msg = Message(
        subject=f"New Job Match: {job.title}",
        recipients=[student.email]
    )

    apply_link = url_for("job.view_job", job_id=job.id, _external=True)

    msg.html = render_template(
        "emails/job_match.html",
        student=student,
        job=job,
        apply_link=apply_link
    )

    mail.send(msg)

@job_bp.route("/company/application/<int:app_id>/approve")
def approve_application(app_id):

    application = application.query.get_or_404(app_id)

    application.status = "Approved"
    db.session.commit()

    # 🔥 SEND APPROVAL EMAIL
    student = Students.query.get(application.student_id)
    job = Job.query.get(application.job_id)

    send_approval_email(student, job)

    flash("Application Approved & Email Sent!", "success")

    return redirect(
        url_for("job.view_applicants", job_id=job.id)
    )
@job_bp.route("/company/application/<int:app_id>/reject")
def reject_application(app_id):

    application = application.query.get_or_404(app_id)
    application.status = "Rejected"
    db.session.commit()

    student = Students.query.get(application.student_id)
    job = Job.query.get(application.job_id)

    send_rejection_email(student, job)

    flash("Application Rejected & Email Sent!", "danger")

    return redirect(url_for("job.view_applicants", job_id=job.id))

@job_bp.route("/company/job/<int:job_id>/applicants")
def view_applicants(job_id):

    job = Job.query.get_or_404(job_id)
    applications = JobApplication.query.filter_by(job_id=job_id).all()

    return render_template(
        "company/applicants.html",
        job=job,
        applications=applications
    )
