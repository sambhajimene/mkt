import smtplib
from email.mime.text import MIMEText
from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO

_last_alert = {}

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def should_alert(symbol, strike, bias):
    key = f"{symbol}_{strike}_{bias}"
    if _last_alert.get(symbol) == key:
        return False
    _last_alert[symbol] = key
    return True
