import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = True,
    ):
        message = MIMEMultipart("alternative")
        message["From"] = self.sender_email
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject

        content_type = "html" if is_html else "plain"
        message.attach(MIMEText(body, content_type))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            return True
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def send_loan_application_email(
        self,
        borrower_name: str,
        loan_id: int,
        amount: float,
        to_emails: List[str],
    ):
        subject = f"Loan Application Received - #{loan_id}"
        body = (
            "<html>\n"
            "  <body style=\"font-family: Arial, sans-serif; padding: 20px;\">\n"
            f"    <h2 style=\"color: #2c3e50;\">Loan Application Received</h2>\n"
            f"    <p>Dear {borrower_name},</p>\n"
            "    <p>We have successfully received your loan "
            "application.</p>\n"
            "    <div style=\"background-color: #f8f9fa; padding: 15px;"
            " border-radius: 5px; margin: 20px 0;\">\n"
            "      <p><strong>Application Details:</strong></p>\n"
            "      <ul>\n"
            f"        <li>Loan ID: #{loan_id}</li>\n"
            f"        <li>Amount: ${amount:,.2f}</li>\n"
            "        <li>Status: Pending Review</li>\n"
            "      </ul>\n"
            "    </div>\n"
            "    <p>Our team will review your application and contact you "
            "shortly.</p>\n"
            "    <br>\n"
            "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>\n"
            "  </body>\n"
            "</html>\n"
        )
        return self.send_email(to_emails, subject, body)

    def send_loan_approval_email(
        self,
        borrower_name: str,
        loan_id: int,
        amount: float,
        account_no: str,
        to_emails: List[str],
    ):
        subject = f"Loan Approved - #{loan_id}"
        body = (
            "<html>\n"
            "  <body style=\"font-family: Arial, sans-serif; padding: 20px;\">\n"
            f"    <h2 style=\"color: #27ae60;\">Congratulations! Your Loan is "
            "Approved</h2>\n"
            f"    <p>Dear {borrower_name},</p>\n"
            "    <p>We are pleased to inform you that your loan application "
            "has been <strong>approved</strong>.</p>\n"
            "    <div style=\"background-color: #d4edda; padding: 15px;"
            " border-radius: 5px; margin: 20px 0;\">\n"
            "      <p><strong>Loan Details:</strong></p>\n"
            "      <ul>\n"
            f"        <li>Loan ID: #{loan_id}</li>\n"
            f"        <li>Approved Amount: ${amount:,.2f}</li>\n"
            f"        <li>Account Number: {account_no}</li>\n"
            "        <li>Status: Approved</li>\n"
            "      </ul>\n"
            "    </div>\n"
            "    <p>The funds will be disbursed to your account within "
            "2-3 business days.</p>\n"
            "    <br>\n"
            "    <p>Thank you for choosing RestoreLoans!</p>\n"
            "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>\n"
            "  </body>\n"
            "</html>\n"
        )
        return self.send_email(to_emails, subject, body)

    def send_loan_rejection_email(
        self,
        borrower_name: str,
        loan_id: int,
        reason: str,
        to_emails: List[str],
    ):
        subject = f"Loan Application Update - #{loan_id}"
        body = (
            "<html>\n"
            "  <body style=\"font-family: Arial, sans-serif; padding: 20px;\">\n"
            f"    <h2 style=\"color: #e74c3c;\">Loan Application Status "
            "Update</h2>\n"
            f"    <p>Dear {borrower_name},</p>\n"
            "    <p>Thank you for your interest in RestoreLoans. After "
            "careful review, we regret to inform you that we are unable to "
            "approve your loan application at this time.</p>\n"
            "    <div style=\"background-color: #f8d7da; padding: 15px;"
            " border-radius: 5px; margin: 20px 0;\">\n"
            "      <p><strong>Application Details:</strong></p>\n"
            "      <ul>\n"
            f"        <li>Loan ID: #{loan_id}</li>\n"
            "        <li>Status: Not Approved</li>\n"
            f"        <li>Reason: {reason}</li>\n"
            "      </ul>\n"
            "    </div>\n"
            "    <p>You may reapply after addressing the concerns mentioned "
            "above.</p>\n"
            "    <br>\n"
            "    <p>If you have any questions, please contact our support "
            "team.</p>\n"
            "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>\n"
            "  </body>\n"
            "</html>\n"
        )
        return self.send_email(to_emails, subject, body)

    def send_custom_loan_email(
        self,
        borrower_name: str,
        loan_id: int,
        amount: float,
        status: str,
        message: str,
        to_emails: List[str],
    ):
        subject = f"Loan Application #{loan_id} - Status Update"
        body = (
            "<html>\n"
            "  <body style=\"font-family: Arial, sans-serif; padding: 20px;\">\n"
            f"    <h2 style=\"color: #2c3e50;\">Loan Application Update</h2>\n"
            f"    <p>Dear {borrower_name},</p>\n"
            f"    <p>{message}</p>\n"
            "    <div style=\"background-color: #f8f9fa; padding: 15px;"
            " border-radius: 5px; margin: 20px 0;\">\n"
            "      <p><strong>Loan Details:</strong></p>\n"
            "      <ul>\n"
            f"        <li>Loan ID: #{loan_id}</li>\n"
            f"        <li>Amount: ${amount:,.2f}</li>\n"
            f"        <li>Current Status: {status}</li>\n"
            "      </ul>\n"
            "    </div>\n"
            "    <br>\n"
            "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>\n"
            "  </body>\n"
            "</html>\n"
        )
        return self.send_email(to_emails, subject, body)


# Create a singleton instance
email_service = EmailService()