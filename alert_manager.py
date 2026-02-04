# alert_manager.py
import smtplib
from email.mime.text import MIMEText
import os

LAST_ALERT = {}

def can_alert(symbol, strike, bias):
    key = f"{symbol}-{strike}"
    if LAST_ALERT.get(key) == bias:
        return False
    LAST_ALERT[key] = bias
    return True


def send_mail(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASS"])
        s.send_message(msg)
