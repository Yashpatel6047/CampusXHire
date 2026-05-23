from app.services.email_service import EmailService
from app.utils.otp_generator import generate_otp
from flask import Blueprint, request, jsonify

auth = Blueprint("auth", __name__)

@auth.route("/send-otp", methods=["POST"])
def send_otp():
    email = request.json.get("email")

    otp = generate_otp()
    # save OTP + expiry in DB here

    EmailService.send_otp_email(email, otp)

    return jsonify({"message": "OTP sent successfully"})
