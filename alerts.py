# alerts.py
import os, smtplib
from email.mime.text import MIMEText

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO   = os.getenv("EMAIL_TO")
EMAIL_PASS = os.getenv("EMAIL_PASS")   # 🔥 FIX HERE

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(EMAIL_FROM, EMAIL_PASS)
        s.send_message(msg)


def should_alert(symbol, bias, atm):
    key = f"{symbol}_{bias}_{atm}"
    if _last_alert.get(symbol) == key:
        return False
    _last_alert[symbol] = key
    return True
