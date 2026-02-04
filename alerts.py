import smtplib
from email.mime.text import MIMEText
from config import *

_last_alert = {}

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(EMAIL_FROM, EMAIL_PASSWORD)
        s.send_message(msg)

def should_alert(symbol, bias, atm):
    key = f"{symbol}_{bias}_{atm}"
    if _last_alert.get(symbol) == key:
        return False
    _last_alert[symbol] = key
    return True
