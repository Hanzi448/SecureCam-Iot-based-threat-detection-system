# services/email_alerts.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import Config


def send_alert(result: dict, subject: str = None, recipient_email: str = None):
    """
    Sends an email alert via Gmail SMTP when a weapon or criminal is detected.
    Supports custom subjects and dynamic content.
    """
    recipient = recipient_email or Config.ALERT_EMAIL_TO
    if not recipient:
        print("[WARN] No recipient email specified.")
        return False

    if not (Config.GMAIL_USER and Config.GMAIL_APP_PASSWORD):
        print("[WARN] Gmail credentials missing in Config.")
        return False

    # --- Determine subject automatically if not provided ---
    if not subject:
        if result.get("weapon_detected") and result.get("criminal_detected"):
            subject = "[ALERT] Weapon + Criminal Detected"
        elif result.get("weapon_detected"):
            subject = "[ALERT] Weapon Detected"
        elif result.get("criminal_detected"):
            subject = "[ALERT] Criminal Detected"
        else:
            subject = "[INFO] Smart Surveillance Update"

    # --- Compose email body ---
    lines = [
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Weapon Detected: {result.get('weapon_detected', False)}",
        f"Criminal Detected: {result.get('criminal_detected', False)}",
    ]

    if result.get("criminal_detected"):
        lines.append(f"Criminal Name: {result.get('criminal_name', 'Unknown')}")
        if result.get("match_distance") is not None:
            lines.append(f"Match Distance: {result.get('match_distance'):.3f}")

    dets = result.get("detections", [])
    if dets:
        lines.append(f"Confidence: {dets[0].get('conf', 'N/A')}")

    if result.get("cloud_url"):
        lines.append(f"\nAnnotated Image: {result['cloud_url']}")

    lines.append("\nPlease review the surveillance footage immediately.")
    body = "\n".join(lines)

    # --- Construct message ---
    msg = MIMEMultipart()
    msg["From"] = Config.GMAIL_USER
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(Config.GMAIL_USER, Config.GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"[EMAIL] Alert sent successfully to {recipient} ({subject})")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False
