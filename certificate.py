from app.extensions import db
class certificate(db.Model):
    __tablename__ = "certificate"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))

    title = db.Column(db.String(200))
    platform = db.Column(db.String(100))
    year = db.Column(db.String(10))
