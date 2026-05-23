from datetime import datetime
from app.extensions.db import db

class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False
    )
    job_id = db.Column(
        db.Integer, db.ForeignKey("jobs.id"), nullable=False
    )
    student_email = db.Column(db.String(120), nullable=False)
    resume = db.Column(db.String(255))
    video_resume = db.Column(db.String(255))
    portfolio_link = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)

    status = db.Column(db.String(20), default="Applied")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ FIXED RELATIONSHIPS
    student = db.relationship("Students", backref="applications")
    job = db.relationship("Job", backref="job_applications")

__table_args__ = (
    db.UniqueConstraint('student_id', 'job_id', name='unique_application'),
)
