from app.extensions import db

class Projects(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))

    student = db.relationship(
        "Students",
        back_populates="projects"
    )
