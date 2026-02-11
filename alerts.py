# alerts.py SAmbhaji Mene
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO

_last_alert = {}

def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(EMAIL_TO)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        print("[EMAIL SENT]", subject)
        return True
    except Exception as e:
        print("[EMAIL ERROR]", e)
        return False


def should_alert(symbol, bias, cooldown_minutes=30):
    now = datetime.now()
    last = _last_alert.get(symbol)

    if last:
        last_bias, last_time = last
        if last_bias == bias and now - last_time < timedelta(minutes=cooldown_minutes):
            return False

    _last_alert[symbol] = (bias, now)
    return True
