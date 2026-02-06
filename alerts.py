import smtplib
from email.mime.text import MIMEText
from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO

# Keep track of last alerts to avoid duplicates
_last_alert = {}

def send_email(subject: str, body: str):
    """
    Send email alert using Gmail SMTP (SSL).
    Works with app password.
    """
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(EMAIL_TO)

        # Connect and send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL SENT] {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

def should_alert(symbol: str, strike: float, bias: str) -> bool:
    """
    Returns True if an alert for this symbol/strike/bias should be sent.
    Prevents duplicate alerts for the same strike/bias.
    """
    key = f"{symbol}_{strike}_{bias}"
    if _last_alert.get(symbol) == key:
        return False
    _last_alert[symbol] = key
    return True
