from tkinter import Canvas
from flask import Blueprint, current_app, render_template, request, redirect, session, url_for, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from werkzeug.utils import secure_filename
import os
from io import BytesIO

from app.extensions import db
from app.models.student import Students
from app.models.project import Projects
from app.models.skills import Skills
from app.models.certificate import certificate as Certificate
from app.routes import student

resume_bp = Blueprint("resume", __name__)

# ===== ASK EXTRA INFO =====


UPLOAD_FOLDER = "app/static/uploads"



@resume_bp.route("/resume-form", methods=["GET", "POST"])
def resume_form():

    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("home.login"))

    student = Students.query.get_or_404(student_id)

    if request.method == "POST":

        action = request.form.get("action")

        # =========================
        # UPDATE OPTIONAL FIELDS
        # =========================

        student.objective = (request.form.get("objective") or "").strip() or None
        student.github = (request.form.get("github") or "").strip() or None
        student.linkedin = (request.form.get("linkedin") or "").strip() or None
        student.portfolio = (request.form.get("portfolio") or "").strip() or None

        title = (request.form.get("title") or "").strip()
        if title:
            student.specialization = title

        sem_raw = (request.form.get("sem") or "").strip()
        cgpa_raw = (request.form.get("cgpa") or "").strip()
        student.sem = int(sem_raw) if sem_raw.isdigit() else None
        try:
            student.cgpa = float(cgpa_raw) if cgpa_raw else None
        except ValueError:
            student.cgpa = None

        if hasattr(Students, "internship"):
            student.internship = (request.form.get("internship") or "").strip() or None
        if hasattr(Students, "languages"):
            student.languages = (request.form.get("languages") or "").strip() or None

        # Replace skills from comma-separated input.
        skills_raw = (request.form.get("skills") or "").strip()
        student.skills.clear()
        if skills_raw:
            for skill_name in [s.strip() for s in skills_raw.split(",") if s.strip()]:
                student.skills.append(Skills(name=skill_name))

        # Replace projects from multiline input: "Title - Description".
        projects_raw = (request.form.get("projects") or "").strip()
        student.projects.clear()
        if projects_raw:
            for line in projects_raw.splitlines():
                item = line.strip()
                if not item:
                    continue
                if " - " in item:
                    title_text, description = item.split(" - ", 1)
                    title_text = title_text.strip() or "Project"
                    description = description.strip()
                else:
                    title_text = "Project"
                    description = item
                student.projects.append(
                    Projects(
                        title=title_text[:150],
                        description=description
                    )
                )

        # Replace certifications from comma-separated input.
        certs_raw = (request.form.get("certifications") or "").strip()
        student.certificate.clear()
        if certs_raw:
            for cert_title in [c.strip() for c in certs_raw.split(",") if c.strip()]:
                student.certificate.append(Certificate(title=cert_title))

        # =========================
        # PHOTO UPLOAD
        # =========================
        photo = request.files.get("photo")

        if photo and photo.filename != "":
            from werkzeug.utils import secure_filename

            filename = secure_filename(photo.filename)

            upload_folder = os.path.join(
                current_app.root_path,
                "static",
                "uploads",
                "photos"
            )
            os.makedirs(upload_folder, exist_ok=True)

            file_path = os.path.join(upload_folder, filename)
            photo.save(file_path)

            photo_rel_path = f"uploads/photos/{filename}"
            if hasattr(Students, "photo"):
                student.photo = photo_rel_path
            # Fallback when Students model/table does not have a photo column.
            session["resume_photo"] = photo_rel_path

        db.session.commit()

        if action == "download":
            return redirect(url_for("resume.download_resume"))

        return redirect(url_for("resume.resume_form"))

    return render_template(
        "student/Resume/resume.html",
        student=student
    )

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Image, HRFlowable
)
from reportlab.lib.styles import (
    getSampleStyleSheet, ParagraphStyle
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from flask import send_file
from io import BytesIO
import os


def generate_pdf(data):

    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        HRFlowable, ListFlowable, ListItem
    )
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from flask import send_file
    from io import BytesIO

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()

    # ==============================
    # COLORS (DARK ATS FRIENDLY)
    # ==============================

    PRIMARY = colors.HexColor("#1a1a1a")   # Dark professional
    LIGHT_LINE = colors.HexColor("#444444")

    # ==============================
    # CUSTOM STYLES
    # ==============================

    name_style = ParagraphStyle(
        name="NameStyle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=PRIMARY,
        spaceAfter=4
    )

    contact_style = ParagraphStyle(
        name="ContactStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=8
    )

    section_style = ParagraphStyle(
        name="SectionStyle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=4
    )

    content_style = ParagraphStyle(
        name="ContentStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=15,
        textColor=colors.black
    )

    # ==============================
    # HEADER
    # ==============================

    elements.append(Paragraph(
        f"<b>{data.get('full_name','')}</b>",
        name_style
    ))

    contact_parts = [
        data.get("email", ""),
        data.get("mobile_no", ""),
        data.get("linkedin", ""),
        data.get("github", "")
    ]

    contact_line = " | ".join([c for c in contact_parts if c])

    elements.append(Paragraph(contact_line, contact_style))

    elements.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=PRIMARY,
            spaceBefore=6,
            spaceAfter=10
        )
    )

    # ==============================
    # SECTION FUNCTION
    # ==============================

    def section(title, content):

        if not content:
            return

        elements.append(Paragraph(title.upper(), section_style))

        elements.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=LIGHT_LINE,
                spaceAfter=6
            )
        )

        # Bullet formatting for ATS
        lines = [line.strip() for line in str(content).split("\n") if line.strip()]

        if len(lines) > 1:
            bullet_points = [
                ListItem(Paragraph(line, content_style))
                for line in lines
            ]
            elements.append(
                ListFlowable(
                    bullet_points,
                    bulletType="bullet"
                )
            )
        else:
            elements.append(Paragraph(content, content_style))

        elements.append(Spacer(1, 12))

    # ==============================
    # ADD SECTIONS
    # ==============================

    section("Professional Summary", data.get("objective"))
    section("Experience", data.get("internship"))
    section("Projects", data.get("projects"))
    section("Education", data.get("education"))

    # ==============================
    # SKILLS INLINE (ATS FRIENDLY)
    # ==============================

    skills = data.get("skills")
    if skills:
        elements.append(Paragraph("TECHNICAL SKILLS", section_style))
        elements.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=LIGHT_LINE,
                spaceAfter=6
            )
        )

        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        formatted_skills = " • ".join(skill_list)

        elements.append(Paragraph(formatted_skills, content_style))
        elements.append(Spacer(1, 12))

    section("Certifications", data.get("certifications"))
    section("Languages", data.get("languages"))

    # ==============================
    # BUILD PDF
    # ==============================

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Professional_ATS_Resume.pdf",
        mimetype="application/pdf"
    )
# ===== PDF GENERATION =====

@resume_bp.route("/download-resume")
def download_resume():
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("home.login"))

    s = Students.query.get_or_404(student_id)
   # ===============================
# 2️⃣ REPORTLAB PROFESSIONAL ATS VERSION
# ===============================

    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        HRFlowable, ListFlowable, ListItem, Image, Table, TableStyle
    )
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    elements = []
    styles = getSampleStyleSheet()

    # ===============================
    # PROFESSIONAL DARK COLORS
    # ===============================
    PRIMARY = colors.HexColor("#1a1a1a")   # Dark Black
    LINE = colors.HexColor("#333333")

    # ===============================
    # STYLES
    # ===============================

    name_style = ParagraphStyle(
        name="NameStyle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=PRIMARY,
        spaceAfter=4
    )

    contact_style = ParagraphStyle(
        name="ContactStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=8
    )

    section_style = ParagraphStyle(
        name="SectionStyle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=4
    )

    content_style = ParagraphStyle(
        name="ContentStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=15
    )

    contact_parts = []
    if s.email:
        contact_parts.append(s.email)
    if s.mobile_no:
        contact_parts.append(s.mobile_no)
    if s.linkedin:
        contact_parts.append(s.linkedin)
    if s.github:
        contact_parts.append(s.github)

    # ===============================
    # HEADER SECTION (TEXT LEFT, PHOTO RIGHT)
    # ===============================
    contact_line = " | ".join(contact_parts)
    photo_flowable = Spacer(1, 1)

    photo_path = getattr(s, "photo", None) or session.get("resume_photo")
    if photo_path:
        try:
            image_path = os.path.join(
                current_app.root_path,
                "static",
                photo_path
            )

            photo_flowable = Image(image_path, width=1.2 * inch, height=1.2 * inch)

        except Exception as e:
            print("Photo Error:", e)

    header_left = Paragraph(
        f"<b>{s.full_name or ''}</b><br/><font size='10' color='grey'>{contact_line}</font>",
        content_style
    )

    header_table = Table(
        [[header_left, photo_flowable]],
        colWidths=[doc.width - (1.2 * inch) - 12, 1.2 * inch]
    )
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(header_table)
    elements.append(Spacer(1, 8))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=2,
            color=PRIMARY,
            spaceBefore=2,
            spaceAfter=12
        )
    )

    # ===============================
    # SECTION FUNCTION WITH BULLETS
    # ===============================

    def section(title, content):
        if not content:
            return

        elements.append(Paragraph(title.upper(), section_style))

        elements.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=LINE,
                spaceAfter=6
            )
        )

        lines = [line.strip() for line in str(content).split("\n") if line.strip()]

        if len(lines) > 1:
            bullet_points = [
                ListItem(Paragraph(line, content_style))
                for line in lines
            ]
            elements.append(
                ListFlowable(
                    bullet_points,
                    bulletType="bullet"
                )
            )
        else:
            elements.append(Paragraph(content, content_style))

        elements.append(Spacer(1, 12))


    # ===============================
    # ADD SECTIONS
    # ===============================

    section("Professional Summary", s.objective)
    section("Experience", getattr(s, "internship", None))

    # Projects
    if s.projects:
        project_lines = [
            f"<b>{p.title}</b> - {p.description}"
            for p in s.projects
        ]
        section("Projects", "\n".join(project_lines))

    # Skills
    if s.skills:
        skills_text = " • ".join([skill.name for skill in s.skills])
        section("Technical Skills", skills_text)

    # Education
    if s.field or s.specialization:
        education_text = f"""
    {s.field or ''}
    {s.specialization or ''}
    Duration: {s.start_year or ''} - {s.end_year or ''}
    CGPA: {s.cgpa or 'N/A'}
    """
        section("Education", education_text)

    # Certifications
    if getattr(s, "certificate", None):
        cert_text = "\n".join([c.title for c in s.certificate])
        section("Certifications", cert_text)

    # Languages
    if getattr(s, "languages", None):
        section("Languages", s.languages)

    # ===============================
    # FOOTER
    # ===============================

    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph(
            "<font size=8 color=grey>Generated by CampusXHire • Professional Resume Builder</font>",
            styles["Normal"]
        )
    )

    # ===============================
    # BUILD PDF
    # ===============================

    doc.build(elements)
    buffer.seek(0)

    resume_folder = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "resumes"
    )
    os.makedirs(resume_folder, exist_ok=True)

    filename = f"resume_{s.id}.pdf"
    file_path = os.path.join(resume_folder, filename)

    with open(file_path, "wb") as f:
        f.write(buffer.getvalue())

    s.resume_file = f"uploads/resumes/{filename}"
    db.session.commit()

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{s.full_name}_Professional_Resume.pdf",
        mimetype="application/pdf"
    )
