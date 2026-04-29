import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

SMTP_EMAIL = "gagankaur2686@gmail.com"
SMTP_PASSWORD = "ljtc dnmo blxd ozjq"

# async def send_email_with_pdf(to_email, subject, html_content, pdf_bytes=None):
#     if not to_email:
#         print("⚠️ No email provided")
#         return

#     message = MIMEMultipart()
#     message["From"] = SMTP_EMAIL
#     message["To"] = to_email
#     message["Subject"] = subject

#     # HTML Body
#     message.attach(MIMEText(html_content, "html"))

#     # PDF Attachment
#     part = MIMEBase("application", "octet-stream")
#     part.set_payload(pdf_bytes)
#     encoders.encode_base64(part)
#     part.add_header(
#         "Content-Disposition",
#         "attachment; filename=invoice.pdf"
#     )
#     message.attach(part)

#     try:
#         await aiosmtplib.send(
#             message,
#             hostname="smtp.gmail.com",
#             port=587,
#             start_tls=True,
#             username=SMTP_EMAIL,
#             password=SMTP_PASSWORD
#         )
#         print("✅ Email sent successfully")
#     except Exception as e:
#         print("❌ Email failed:", e)

# async def send_email_with_pdf(to_email, subject, html_content, pdf_bytes=None):
#     if not to_email:
#         print("⚠️ No email provided")
#         return

#     message = MIMEMultipart()
#     message["From"] = SMTP_EMAIL
#     message["To"] = to_email
#     message["Subject"] = subject

#     message.attach(MIMEText(html_content, "html"))

#     # ✅ attach PDF only if exists
#     if pdf_bytes:
#         part = MIMEBase("application", "octet-stream")
#         part.set_payload(pdf_bytes)
#         encoders.encode_base64(part)
#         part.add_header(
#             "Content-Disposition",
#             "attachment; filename=invoice.pdf"
#         )
#         message.attach(part)

#     try:
#         await aiosmtplib.send(
#             message,
#             hostname="smtp.gmail.com",
#             port=587,
#             start_tls=True,
#             username=SMTP_EMAIL,
#             password=SMTP_PASSWORD
#         )
#         print(f"✅ Email sent: {subject}")
#     except Exception as e:
#         print("❌ Email failed:", e)

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
        print("📨 Sending email to:", to_email)

        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD
        )

        print(f"✅ Email sent: {subject}")

    except Exception as e:
        print("❌ Email failed:", e)

