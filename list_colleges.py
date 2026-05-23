from app.extensions.db import db

class EngineeringCollege(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100))
    type = db.Column(db.String(50))
    affiliation = db.Column(db.String(100))
    state = db.Column(db.String(50), default="Gujarat")
