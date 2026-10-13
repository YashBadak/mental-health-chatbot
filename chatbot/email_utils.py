# chatbot/email_utils.py
import os
import smtplib
import ssl
from email.message import EmailMessage

def send_welcome_email(recipient_email: str, username: str):
    # This function remains the same
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_APP_PASSWORD")
    if not sender_email or not sender_password:
        print("WARNING: Email credentials are not set.")
        return
    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Welcome to the Mental Health Chatbot! 🎉"
    body = f"""
    Hi {username},
    Welcome! We're so glad you've joined our community.
    The Mental Health Chatbot is a safe and supportive space for you to express your thoughts and feelings.
    Best,
    The Mental Health Chatbot Team
    """
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
    except Exception as e:
        print(f"Error: Failed to send welcome email. Exception: {e}")

def send_otp_email(recipient_email: str, otp: str):
    """Sends a password reset OTP to the user's email."""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_APP_PASSWORD")

    if not sender_email or not sender_password:
        print("WARNING: Email credentials are not set. Cannot send OTP.")
        return False

    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Your Password Reset OTP"
    body = f"""
    Hello,

    You requested to reset your password.
    Your One-Time Password (OTP) is: {otp}

    This OTP is valid for 10 minutes.

    If you did not request this, please ignore this email.

    Best,
    The Mental Health Chatbot Team
    """
    message.set_content(body)
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        print(f"OTP email successfully sent to {recipient_email}.")
        return True
    except Exception as e:
        print(f"Error: Failed to send OTP email. Exception: {e}")
        return False