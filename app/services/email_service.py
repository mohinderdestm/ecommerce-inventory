import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


async def send_email_with_pdf(to_email, subject, html_content, pdf_bytes=None):
    if not to_email:
        print("⚠️ No email provided")
        return

    message = MIMEMultipart()
    message["From"] = SMTP_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(html_content, "html"))

    # ✅ attach PDF only if present
    if pdf_bytes:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment; filename=invoice.pdf"
        )
        message.attach(part)

    try:
        print("Sending email to:", to_email)

        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD
        )

        print(f"Email sent: {subject}")

    except Exception as e:
        print("Email failed:", e)
        raise e

