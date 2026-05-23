import os
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)
from werkzeug.utils import secure_filename

from app.models.video_resume import VideoResume
from app.models import Students
from app.extensions.db import db

# ===============================
# Blueprint
# ===============================
video_resume_bp = Blueprint(
    "video_resume",
    __name__,
    url_prefix="/video-resume"
)

ALLOWED_EXTENSIONS = {"mp4", "webm", "mov"}


# ===============================
# Helpers
# ===============================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ===============================
# Upload video resume (30s recorder)
@video_resume_bp.route("/upload", methods=["POST"])
def upload_video_resume():
    if "student_id" not in session:
        return "Unauthorized", 401

    student = Students.query.get_or_404(session["student_id"])
    video = request.files.get("video")

    if not video:
        return "No video uploaded", 400

    if not allowed_file(video.filename):
        return "Invalid file type", 400

    upload_folder = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "video_resumes"
    )
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"video_resume_{student.id}.webm"
    file_path = os.path.join(upload_folder, filename)

    video.save(file_path)

    student.video_resume = f"uploads/video_resumes/{filename}"
    db.session.commit()

    return redirect(url_for("student.student_dashboard"))
    


# ===============================
# Upload via file selector (optional)
# ===============================
@video_resume_bp.route("/upload-file", methods=["GET", "POST"])
def upload_video_file():
    if "student_id" not in session:
        return redirect(url_for("auth.login"))

    student = Students.query.get_or_404(session["student_id"])

    if request.method == "POST":
        video = request.files.get("video")
        visibility = request.form.get("visibility", "public")

        if video is None:
            flash("No video received. Please record or upload a video.", "danger")
            return redirect(url_for("video_resume.video_resume_page"))

       

        upload_folder = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "video_resumes"
        )
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(f"video_resume_{student.id}.webm")
        file_path = os.path.join(upload_folder, filename)

        video.save(file_path)

        # Save in Student table
        student.video_resume = f"uploads/video_resumes/{filename}"

        # Optional: save in VideoResume table
        vr = VideoResume(
            user_id=student.id,
            video_filename=filename,
            visibility=visibility
        )
        
        db.session.add(vr)
        db.session.commit()

        flash("Video resume recorded successfully", "success")
        return redirect(url_for("video_resume.video_resume_page"))
    return render_template("student/video_resume/upload_video.html")





# ===============================
# Video Resume Page
# ===============================
@video_resume_bp.route("/")
def video_resume_page():
    if "student_id" not in session:
        return redirect(url_for("auth.login"))

    student = Students.query.get_or_404(session["student_id"])
    return render_template("student/video_resume/video_resume.html", student=student)

@video_resume_bp.route("/update", methods=["POST"])
def update_video_resume():
    if "student_id" not in session:
        return redirect(url_for("auth.login"))

    student = Students.query.get_or_404(session["student_id"])

    video = request.files.get("video")
    visibility = request.form.get("visibility", "public")

    if not video:
        flash("No video selected", "danger")
        return redirect(url_for("video_resume.video_resume_page"))

    if not allowed_file(video.filename):
        flash("Invalid video format", "danger")
        return redirect(url_for("video_resume.video_resume_page"))

    upload_folder = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "video_resumes"
    )
    os.makedirs(upload_folder, exist_ok=True)

    # 🔥 DELETE OLD VIDEO IF EXISTS
    if student.video_resume:
        old_path = os.path.join(
            current_app.root_path,
            "static",
            student.video_resume
        )
        if os.path.exists(old_path):
            os.remove(old_path)

    # 🔥 SAVE NEW VIDEO
    filename = f"video_resume_{student.id}.webm"
    file_path = os.path.join(upload_folder, filename)
    video.save(file_path)

    # 🔥 UPDATE DB
    student.video_resume = f"uploads/video_resumes/{filename}"
    db.session.commit()

    flash("Video resume updated successfully", "success")
    return redirect(url_for("video_resume.video_resume_page"))
