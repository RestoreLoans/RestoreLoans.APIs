import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as mime_encoders
from email.utils import formatdate, make_msgid
from typing import List, Optional, IO
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_username = os.getenv("SMTP_USERNAME", self.sender_email)
        self.smtp_password = os.getenv("SMTP_PASSWORD", self.sender_password)

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = True,
        attachments: Optional[List[tuple]] = None,
    ) -> bool:
        if not to_emails:
            raise Exception("No recipient emails provided")

        content_type = "html" if is_html else "plain"
        message = MIMEText(body, content_type, _charset="utf-8")
        message["From"] = self.sender_email
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain="restoreloans.co.za")

        if attachments:
            wrapper = MIMEMultipart("mixed")
            wrapper["From"] = self.sender_email
            wrapper["To"] = ", ".join(to_emails)
            wrapper["Subject"] = subject
            wrapper["Date"] = formatdate(localtime=True)
            wrapper["Message-ID"] = make_msgid(domain="restoreloans.co.za")
            wrapper.attach(message)
            for file_bytes, filename in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_bytes)
                mime_encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f'attachment; filename="{filename}"'
                )
                wrapper.attach(part)
            message = wrapper

        try:
            is_local = self.smtp_server in ("127.0.0.1", "localhost")
            if is_local:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.send_message(message)
            elif self.smtp_port == 465:
                # Implicit TLS (SMTPS)
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, local_hostname="restoreloans.co.za")
                server.ehlo("restoreloans.co.za")
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
                server.quit()
            else:
                # STARTTLS (e.g. port 587)
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.ehlo("restoreloans.co.za")
                    server.login(self.smtp_username, self.smtp_password)
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
        custom_message: Optional[str] = None,
    ):
        subject = "Loan Application Received"
        is_html = True
        if custom_message:
            body = custom_message
            is_html = any(tag in custom_message.lower() for tag in ['<html', '<body', '<p', '<div', '<h2'])
        else:
            body = "\n".join(
                [
                    "<html>",
                    "  <body style=\"font-family: Arial, sans-serif; "
                    "padding: 20px;\">",
                    "    <h2 style=\"color: #2c3e50;\">"
                    "Loan Application Received</h2>",
                    f"    <p>Dear {borrower_name},</p>",
                    "    <p>We have successfully received your loan",
                    "    application.</p>",
                    "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                    "border-radius: 5px; margin: 20px 0;\">",
                    "      <p><strong>Application Details:</strong></p>",
                    "      <ul>",
                    f"        <li>Loan ID: #{loan_id}</li>",
                    f"        <li>Amount: R{amount:,.2f}</li>",
                    "        <li>Status: Pending Review</li>",
                    "      </ul>",
                    "    </div>",
                    "    <p>Our team will review your application and contact",
                    "    you shortly.</p>",
                    "    <br>",
                    "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>",
                    "  </body>",
                    "</html>",
            ]
        )
        return self.send_email(to_emails, subject, body, is_html=is_html)

    def send_loan_approval_email(
        self,
        borrower_name: str,
        loan_id: int,
        amount: float,
        account_no: str,
        to_emails: List[str],
    ):
        subject = f"Loan Approved - #{loan_id}"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #27ae60;\">Congratulations! Your Loan "
                "is Approved</h2>",
                f"    <p>Dear {borrower_name},</p>",
                "    <p>We are pleased to inform you that your loan "
                "application has been <strong>approved</strong>.</p>",
                "    <div style=\"background-color: #d4edda; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                "      <p><strong>Loan Details:</strong></p>",
                "      <ul>",
                f"        <li>Loan ID: #{loan_id}</li>",
                f"        <li>Approved Amount: ${amount:,.2f}</li>",
                f"        <li>Account Number: {account_no}</li>",
                "        <li>Status: Approved</li>",
                "      </ul>",
                "    </div>",
                "    <p>The funds will be disbursed to your account within",
                "    2-3 business days.</p>",
                "    <br>",
                "    <p>Thank you for choosing RestoreLoans!</p>",
                "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>",
                "  </body>",
                "</html>",
            ]
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
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #e74c3c;\">Loan Application Status "
                "Update</h2>",
                f"    <p>Dear {borrower_name},</p>",
                "    <p>Thank you for your interest in RestoreLoans. After",
                "    careful review, we regret to inform you that we are unable",
                "    to approve your loan application at this time.</p>",
                "    <div style=\"background-color: #f8d7da; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                "      <p><strong>Application Details:</strong></p>",
                "      <ul>",
                f"        <li>Loan ID: #{loan_id}</li>",
                "        <li>Status: Not Approved</li>",
                f"        <li>Reason: {reason}</li>",
                "      </ul>",
                "    </div>",
                "    <p>You may reapply after addressing the concerns mentioned",
                "    above.</p>",
                "    <br>",
                "    <p>If you have any questions, please contact our support",
                "    team.</p>",
                "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>",
                "  </body>",
                "</html>",
            ]
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
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #2c3e50;\">Loan Application Update"
                "</h2>",
                f"    <p>Dear {borrower_name},</p>",
                f"    <p>{message}</p>",
                "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                "      <p><strong>Loan Details:</strong></p>",
                "      <ul>",
                f"        <li>Loan ID: #{loan_id}</li>",
                f"        <li>Amount: ${amount:,.2f}</li>",
                f"        <li>Current Status: {status}</li>",
                "      </ul>",
                "    </div>",
                "    <br>",
                "    <p>Best regards,<br><strong>RestoreLoans Team</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email(to_emails, subject, body)

    def send_contract_signed_email(
        self,
        borrower_name: str,
        loan_id: int,
        amount: float,
        account_no: str,
        to_emails: List[str],
    ):
        subject = f"Loan Contract Signed - #{loan_id}"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #2c3e50;\">"
                "Loan Contract Signed Successfully</h2>",
                f"    <p>Dear {borrower_name},</p>",
                "    <p>Your loan contract has been <strong>"
                "signed and confirmed</strong>. "
                "The loan is now active and will be disbursed shortly.</p>",
                "    <div style=\"background-color: #d4edda; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                "      <p><strong>Contract Details:</strong></p>",
                "      <ul>",
                f"        <li>Loan ID: #{loan_id}</li>",
                f"        <li>Approved Amount: ${amount:,.2f}</li>",
                f"        <li>Account Number: {account_no}</li>",
                "        <li>Status: Contract Signed</li>",
                "      </ul>",
                "    </div>",
                "    <p>If you have any questions, please contact our "
                "support team.</p>",
                "    <br>",
                "    <p>Best regards,<br><strong>"
                "RestoreLoans Team</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email(to_emails, subject, body)

    def send_application_with_docs_email(
        self,
        borrower_name: str,
        loan_id: int,
        amount: float,
        loan_type: str,
        interest_rate: float,
        loan_term: int,
        to_emails: List[str],
        attachments: Optional[List[tuple]] = None,
    ):
        subject = "New Loan Application"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #2c3e50;\">New Loan Application</h2>",
                f"    <p>A new loan application has been submitted and "
                f"requires review.</p>",
                "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                "      <p><strong>Applicant Details:</strong></p>",
                "      <ul>",
                f"        <li>Borrower: {borrower_name}</li>",
                f"        <li>Loan ID: #{loan_id}</li>",
                f"        <li>Loan Type: {loan_type}</li>",
                f"        <li>Amount: R {amount:,.2f}</li>",
                f"        <li>Interest Rate: {interest_rate}%</li>",
                f"        <li>Loan Term: {loan_term} months</li>",
                "        <li>Status: Pending Review</li>",
                "      </ul>",
                "    </div>",
                "    <p>Supporting documents (ID, bank statement, "
                "proof of residence) are attached to this email.</p>",
                "    <br>",
                "    <p>Best regards,<br><strong>"
                "RestoreLoans System</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email(
            to_emails, subject, body, attachments=attachments
        )

    def send_new_application_notification(
        self,
        applicant_name: str,
        applicant_phone: str,
        applicant_email: str,
        id_number: str = "",
        employer_name: str = "",
        to_emails: Optional[List[str]] = None,
    ):
        subject = "New Application"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #2c3e50;\">New Application</h2>",
                "    <p>A new client has registered and requires review.</p>",
                "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                "      <p><strong>Applicant Details:</strong></p>",
                "      <ul>",
                f"        <li>Name: {applicant_name}</li>",
                f"        <li>Phone: {applicant_phone}</li>",
                f"        <li>Email: {applicant_email}</li>",
                f"        <li>ID Number: {id_number}</li>",
                f"        <li>Employer: {employer_name}</li>",
                "        <li>Status: Pending Application</li>",
                "      </ul>",
                "    </div>",
                "    <p>Please log in to review the new application.</p>",
                "    <br>",
                "    <p>Best regards,<br><strong>"
                "RestoreLoans System</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email(
            to_emails or ["applicants@restoreloans.co.za"], subject, body
        )


# Create a singleton instance
email_service = EmailService()