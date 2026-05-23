# app/routes/portfolio.py
from flask import Blueprint, render_template, session
from app.models.student import Students
from app.extensions import db
portfolio_bp = Blueprint("portfolio", __name__)

@portfolio_bp.route("/my-portfolio")

def portfolio():
    student = Students.query.get(session["student_id"])
    student.portfolio = f"/portfolio/{student.slug}"
    db.session.commit()

    return render_template("student/portfolio/portfolio_page.html", student=student)
