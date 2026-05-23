from datetime import datetime
from app.extensions.db import db


class Job(db.Model):
    __tablename__ = "jobs"

    # ---------------- PRIMARY KEY ----------------
    id = db.Column(db.Integer, primary_key=True)

    # ---------------- COMPANY RELATION ----------------
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )

    # ---------------- BASIC INFO ----------------
    job_title = db.Column(db.String(150), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    work_mode = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))

    # ---------------- REQUIREMENTS ----------------
    experience = db.Column(db.String(50))
    education = db.Column(db.String(100))

    # Comma-separated skills: "Python,Flask,SQL"
    skills = db.Column(db.Text)

    description = db.Column(db.Text)

    # ---------------- JOB DETAILS ----------------
    salary = db.Column(db.String(50))
    openings = db.Column(db.Integer, default=1)

    selection_process = db.Column(db.Text)
    deadline = db.Column(db.Date)

    # ---------------- STATUS ----------------
    status = db.Column(
        db.String(20),
        default="ACTIVE",
        nullable=False
    )

    # ---------------- TIMESTAMP ----------------
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ---------------- RELATIONSHIP ----------------
    company = db.relationship(
        "Company",
        backref=db.backref("jobs", lazy=True),
        passive_deletes=True
    )

    # ---------------- DEBUG ----------------
    def __repr__(self):
        return f"<Job {self.id} - {self.job_title}>"
