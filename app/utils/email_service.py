import asyncio
import os
import smtplib
import traceback
from pathlib import Path
from email.message import EmailMessage
from email.utils import formataddr
from email.header import Header
from dotenv import load_dotenv

from app.core.config import settings
from app.utils.invoice_pdf import generate_order_invoice_pdf


def _clean_env_value(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'")


def _runtime_smtp_config() -> dict:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

    username = _clean_env_value(os.getenv("SMTP_USERNAME", settings.SMTP_USERNAME))
    username = "".join(username.split())

    password = _clean_env_value(os.getenv("SMTP_PASSWORD", settings.SMTP_PASSWORD))
    password = "".join(password.split())

    sender_email = _clean_env_value(
        os.getenv("SMTP_SENDER_EMAIL", settings.SMTP_SENDER_EMAIL or username)
    )
    sender_email = "".join(sender_email.split())

    host = _clean_env_value(os.getenv("SMTP_HOST", settings.SMTP_HOST))

    sender_name = (
        _clean_env_value(os.getenv("SMTP_SENDER_NAME", settings.SMTP_SENDER_NAME))
        or "Smart Inventory"
    )

    port_raw = _clean_env_value(os.getenv("SMTP_PORT", str(settings.SMTP_PORT)))
    try:
        port = int(port_raw or "587")
    except ValueError:
        port = 587

    tls_raw = _clean_env_value(
        os.getenv("SMTP_USE_TLS", "true" if settings.SMTP_USE_TLS else "false")
    ).lower()
    use_tls = tls_raw in {"true", "1", "yes"}

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "sender_email": sender_email,
        "sender_name": sender_name,
        "use_tls": use_tls,
    }


def _smtp_sender_email(config: dict) -> str:
    return config.get("sender_email") or config.get("username") or ""


def _can_send_email(recipient: str, config: dict) -> bool:
    return bool(
        recipient
        and config.get("host")
        and config.get("port")
        and config.get("username")
        and config.get("password")
        and _smtp_sender_email(config)
    )


def _missing_smtp_fields(recipient: str, config: dict) -> list[str]:
    missing = []
    if not recipient:
        missing.append("recipient_email")
    if not config.get("host"):
        missing.append("SMTP_HOST")
    if not config.get("port"):
        missing.append("SMTP_PORT")
    if not config.get("username"):
        missing.append("SMTP_USERNAME")
    if not config.get("password"):
        missing.append("SMTP_PASSWORD")
    if not _smtp_sender_email(config):
        missing.append("SMTP_SENDER_EMAIL")
    return missing


def _build_email_message(order_data: dict, config: dict) -> tuple[EmailMessage, str]:
    recipient = str(order_data.get("customer_email") or "").strip()
    order_reference = str(
        order_data.get("order_reference") or order_data.get("id") or ""
    )
    customer_name = str(order_data.get("customer_name") or "Customer")
    payment_method = str(order_data.get("payment_method") or "N/A").upper()
    shipping_address = str(order_data.get("shipping_address") or "N/A")
    total_amount = float(order_data.get("total_amount") or 0)

    pdf_bytes, pdf_filename = generate_order_invoice_pdf(order_data)

    message = EmailMessage()

    message["Subject"] = str(
        Header(f"Order Placed Successfully - {order_reference}", "utf-8")
    )

    sender_name = str(Header(config.get("sender_name"), "utf-8"))
    message["From"] = formataddr((sender_name, _smtp_sender_email(config)))

    message["To"] = recipient

    plain_body = (
        f"Hello {customer_name},\n\n"
        "Your order has been placed successfully.\n\n"
        f"Order Reference: {order_reference}\n"
        f"Total Amount: INR {total_amount:.2f}\n"
        f"Payment Method: {payment_method}\n"
        f"Shipping Address: {shipping_address}\n\n"
        "Your invoice is attached with this email.\n\n"
        "Thank you,\n"
        "Smart Inventory"
    )
    message.set_content(plain_body)

    html_body = f"""
    <html>
      <body>
        <h2>Order Confirmation</h2>
        <p>Hello <strong>{customer_name}</strong>,</p>
        <p>Your order has been placed successfully.</p>
        <p><b>Order Reference:</b> {order_reference}</p>
        <p><b>Total Amount:</b> INR {total_amount:.2f}</p>
        <p><b>Payment Method:</b> {payment_method}</p>
        <p><b>Shipping Address:</b> {shipping_address}</p>
        <p>Your invoice is attached.</p>
      </body>
    </html>
    """
    message.add_alternative(html_body, subtype="html")

    message.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_filename,
    )

    return message, pdf_filename


def _send_email_sync(message: EmailMessage, config: dict) -> None:
    with smtplib.SMTP(config.get("host"), config.get("port"), timeout=25) as smtp:
        smtp.ehlo()

        if config.get("use_tls"):
            smtp.starttls()
            smtp.ehlo()

        smtp.login(config.get("username"), config.get("password"))
        smtp.send_message(message)


async def send_order_confirmation_email(order_data: dict):
    recipient = str(order_data.get("customer_email") or "").strip()
    config = _runtime_smtp_config()

    if not _can_send_email(recipient, config):
        missing = _missing_smtp_fields(recipient, config)
        return False, None, f"SMTP not configured ({', '.join(missing)})"

    message, pdf_filename = _build_email_message(order_data, config)

    try:
        await asyncio.to_thread(_send_email_sync, message, config)
        return True, pdf_filename, None

    except Exception:
        traceback.print_exc()
        return False, pdf_filename, "Email could not be sent"
