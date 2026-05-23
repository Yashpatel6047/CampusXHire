from app.extensions import db
from app.extensions.db import db

class Skills(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))

    name = db.Column(db.String(100), nullable=False)

    student = db.relationship("Students", back_populates="skills")
