import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template_string
from datetime import datetime

# ======================
# ENV CONFIG (FROM OPENSHIFT SECRET)
# ======================
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO   = os.getenv("EMAIL_TO")

CHECK_INTERVAL = 15 * 60  # 15 minutes

# ======================
# FLASK APP
# ======================
app = Flask(__name__)

# Store alerts in memory (PVC not used)
ALERTS = []

# ======================
# EMAIL FUNCTION
# ======================
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.send_message(msg)

# ======================
# MOCK OPTION DATA (REPLACE WITH NSE LIVE DATA)
# ======================
def fetch_option_data():
    """
    Replace this with NSE live fetch logic.
    """
    return {
        "symbol": "NIFTY",
        "atm": 22500,
        "alerts": [
            {"strike": 22550, "type": "CALL"},
            {"strike": 22450, "type": "PUT"}
        ]
    }

# ======================
# ALERT ENGINE (15 MIN)
# ======================
def check_alerts():
    data = fetch_option_data()

    if not data["alerts"]:
        return

    for alert in data["alerts"]:
        record = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "symbol": data["symbol"],
            "atm": data["atm"],
            "strike": alert["strike"],
            "side": alert["type"]
        }

        ALERTS.append(record)

        subject = f"🚨 {record['symbol']} {record['side']} Alert"
        body = f"""
        <h3>{record['symbol']} Option Alert</h3>
        <p><b>ATM:</b> {record['atm']}</p>
        <p><b>Strike:</b> {record['strike']}</p>
        <p><b>Side:</b> {record['side']}</p>
        <p><b>Time:</b> {record['time']}</p>
        """

        send_email(subject, body)

# ======================
# BACKGROUND LOOP
# ======================
def alert_loop():
    while True:
        try:
            check_alerts()
        except Exception as e:
            print("Alert error:", e)

        time.sleep(CHECK_INTERVAL)

# ======================
# DASHBOARD (ONLY ALERTS)
# ======================
@app.route("/")
def dashboard():
    html = """
    <html>
    <head>
        <title>Option Alerts Dashboard</title>
        <style>
            body { font-family: Arial; background:#111; color:#fff; }
            table { width:100%; border-collapse: collapse; }
            th, td { padding:10px; border-bottom:1px solid #333; text-align:center; }
            .call { background:#0033cc; }
            .put  { background:#990000; }
        </style>
    </head>
    <body>
        <h2>🚨 Live Option Alerts (15-Min Candle)</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>ATM</th>
                <th>Strike</th>
                <th>Side</th>
            </tr>
            {% for a in alerts %}
            <tr class="{{ 'call' if a.side == 'CALL' else 'put' }}">
                <td>{{a.time}}</td>
                <td>{{a.symbol}}</td>
                <td>{{a.atm}}</td>
                <td>{{a.strike}}</td>
                <td>{{a.side}}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, alerts=ALERTS)

# ======================
# START
# ======================
if __name__ == "__main__":
    import threading
    threading.Thread(target=alert_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
