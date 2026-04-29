import logging
import smtplib
from email.message import EmailMessage
from fastapi import BackgroundTasks
from app.core.config import settings
from app.models.sales_order import SalesOrderStatus

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, background_tasks: BackgroundTasks = None):
        self.background_tasks = background_tasks

    def _send_email_sync(self, to_email: str, subject: str, html_content: str):
        if not settings.ENABLE_EMAILS:
            logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
            logger.info(f"[MOCK EMAIL CONTENT]\n{html_content}")
            return

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.error("SMTP credentials are not configured but ENABLE_EMAILS is True.")
            return

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = to_email
        msg.set_content("Please enable HTML to view this email.")
        msg.add_alternative(html_content, subtype='html')

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")

    def send_email(self, to_email: str, subject: str, html_content: str):
        """Sends an email in the background if background_tasks is available, else synchronously."""
        if self.background_tasks:
            self.background_tasks.add_task(self._send_email_sync, to_email, subject, html_content)
        else:
            self._send_email_sync(to_email, subject, html_content)

    def _get_html_wrapper(self, title: str, content: str) -> str:
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-bottom: 3px solid #f163c6;">
                    <h2 style="color: #1f1f1f; margin: 0;">{settings.APP_TITLE}</h2>
                </div>
                <div style="padding: 30px 20px; background-color: #ffffff; border: 1px solid #e9ecef; border-top: none;">
                    <h3 style="color: #f163c6; margin-top: 0;">{title}</h3>
                    {content}
                </div>
                <div style="text-align: center; padding: 20px; font-size: 12px; color: #6c757d;">
                    &copy; {settings.APP_TITLE}. All rights reserved.
                </div>
            </body>
        </html>
        """

    def send_order_drafted_customer(self, customer_email: str, order_number: str):
        content = f"""
        <p>Hello,</p>
        <p>Your sales order <strong>{order_number}</strong> has been successfully initiated and is currently in <strong>Draft</strong> status.</p>
        <p>We will notify you once the order is confirmed and stock is reserved.</p>
        <p>Thank you for shopping with us!</p>
        """
        html_content = self._get_html_wrapper(f"Order Initiated: {order_number}", content)
        self.send_email(customer_email, f"Order Initiated - {order_number}", html_content)

    def send_order_drafted_admin(self, admin_emails: list[str], order_number: str, customer_name: str):
        content = f"""
        <p>Hello Admin,</p>
        <p>A new sales order <strong>{order_number}</strong> has been drafted by customer <strong>{customer_name}</strong>.</p>
        <p>Please review and confirm the order when ready.</p>
        """
        html_content = self._get_html_wrapper(f"New Order Draft: {order_number}", content)
        for email in admin_emails:
            self.send_email(email, f"New Order Alert - {order_number}", html_content)

    def send_order_status_update(self, customer_email: str, order_number: str, new_status: str):
        status_display = new_status.replace('_', ' ').title()
        
        # Customize message based on status
        if new_status == SalesOrderStatus.CONFIRMED.value:
            msg = "Great news! Your order has been confirmed and stock has been reserved."
        elif new_status == SalesOrderStatus.PACKED.value:
            msg = "Your order has been packed and is ready for dispatch."
        elif new_status == SalesOrderStatus.SHIPPED.value:
            msg = "Your order is on its way! It has been shipped from our warehouse."
        elif new_status == SalesOrderStatus.DELIVERED.value:
            msg = "Your order has been delivered. We hope you enjoy your purchase!"
        elif new_status == SalesOrderStatus.CANCELLED.value:
            msg = "Your order has been cancelled."
        elif new_status == SalesOrderStatus.RETURNED.value:
            msg = "Your order return has been processed successfully."
        else:
            msg = f"Your order status has been updated to: {status_display}"

        content = f"""
        <p>Hello,</p>
        <p>There is an update on your sales order <strong>{order_number}</strong>.</p>
        <p style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #f163c6; margin: 20px 0;">
            {msg}
        </p>
        <p>Current Status: <strong>{status_display}</strong></p>
        """
        html_content = self._get_html_wrapper(f"Order Update: {order_number}", content)
        self.send_email(customer_email, f"Order Update - {order_number} ({status_display})", html_content)

    def send_low_stock_alert(self, admin_emails: list[str], product_name: str, sku: str, current_stock: int, reorder_level: int):
        content = f"""
        <p>Hello,</p>
        <p>This is an automated alert from your Smart Inventory Platform.</p>
        <p style="padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; margin: 20px 0;">
            <strong>Low Stock Warning</strong><br/>
            Product: <strong>{product_name}</strong> (SKU: {sku})<br/>
            Current Global Stock: <strong>{current_stock}</strong><br/>
            Reorder Level: <strong>{reorder_level}</strong>
        </p>
        <p>Please review and initiate a Purchase Order to restock this item soon.</p>
        """
        html_content = self._get_html_wrapper(f"Low Stock Alert: {sku}", content)
        for email in admin_emails:
            self.send_email(email, f"Low Stock Alert - {product_name} ({sku})", html_content)
