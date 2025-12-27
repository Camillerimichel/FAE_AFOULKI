import os
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str, body_html: str | None = None) -> tuple[bool, str | None]:
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        return False, "SMTP_HOST non configure"

    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM") or smtp_user
    use_tls = os.getenv("SMTP_TLS", "true").lower() in {"1", "true", "yes"}
    use_ssl = os.getenv("SMTP_SSL", "false").lower() in {"1", "true", "yes"}

    if not smtp_from:
        return False, "SMTP_FROM non configure"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(body)
    if body_html:
        message.add_alternative(body_html, subtype="html")

    server = None
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            if use_tls:
                server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(message)
    except Exception as exc:
        return False, str(exc)
    finally:
        if server:
            server.quit()

    return True, None
