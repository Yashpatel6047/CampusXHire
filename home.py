from flask import render_template, request, session, redirect, url_for, current_app,Blueprint
from sqlalchemy.exc import IntegrityError

home_bp = Blueprint("home", __name__)

@home_bp.route("/home-page", methods=["GET", "POST"])
def home():
    return render_template('Home.html')

@home_bp.route("/login")
def login():
    return render_template("Start/first.html")  