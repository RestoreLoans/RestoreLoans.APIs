import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as mime_encoders
from email.utils import formatdate, make_msgid
from typing import List, Optional, IO
import os
import re
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=ENV_PATH)


class EmailService:
    def __init__(self):
        self._reload_env()

    def _reload_env(self):
        # Re-read the .env file on every reload so edits are picked up
        # without restarting the server (uvicorn --reload only watches .py).
        load_dotenv(dotenv_path=ENV_PATH, override=True)
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

        self._reload_env()

        if is_html:
            html_body = body
            plain_body = re.sub(r"<[^>]+>", " ", body)
            plain_body = re.sub(r"\s+", " ", plain_body).strip()
        else:
            html_body = None
            plain_body = body

        alternative = MIMEMultipart("alternative")
        alternative.attach(MIMEText(plain_body, "plain", _charset="utf-8"))
        if html_body:
            alternative.attach(MIMEText(html_body, "html", _charset="utf-8"))

        message = MIMEMultipart("mixed")
        message["From"] = self.sender_email
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain="restoreloans.co.za")
        message["X-Mailer"] = "RestoreLoans"
        message.attach(alternative)

        if attachments:
            for file_bytes, filename in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_bytes)
                mime_encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f'attachment; filename="{filename}"'
                )
                message.attach(part)

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
        client_details: Optional[dict] = None,
        employer_details: Optional[dict] = None,
        bank_details: Optional[dict] = None,
    ):
        subject = "New Loan Application"

        def _li(label, value):
            return (
                f"        <li>{label}: "
                f"{value if value is not None and str(value).strip() != '' else 'N/A'}</li>"
            )

        blocks = []

        client_map = [
            ("Title", "title"),
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("ID Number", "id_number"),
            ("Email", "email"),
            ("Cellphone Number", "phone_number"),
            ("Home Phone", "homephone"),
            ("Home Address", "home_add1"),
            ("Home Address 2", "home_add2"),
            ("Suburb", "suburb"),
            ("Town", "town"),
            ("Postal Code", "postal_code"),
            ("Language", "language"),
            ("Date of Birth", "dob"),
            ("Nationality", "nationality"),
            ("Gender", "gender"),
        ]
        if client_details:
            blocks.append(
                ("CLIENT DETAILS",
                 [_li(label, client_details.get(key)) for label, key in client_map])
            )

        employer_map = [
            ("Company Name", "name"),
            ("Type", "type"),
            ("Pay Day Date", "pay_day_date"),
            ("Address 1", "address1"),
            ("Address 2", "address2"),
            ("Town", "town"),
            ("Suburb", "suburb"),
            ("Postal Code", "post_code"),
            ("Phone", "phone"),
            ("Appointed On", "appointed_on_date"),
            ("Pay Date Shift", "pay_date_shift"),
            ("Contact Method", "contact_method"),
            ("Salary Frequency", "salary_freq"),
            ("Pay Method", "pay_method"),
            ("Pay Day of Week", "pay_day_of_week"),
            ("Contract End Date", "contract_end_date"),
        ]
        if employer_details:
            blocks.append(
                ("EMPLOYER DETAILS",
                 [_li(label, employer_details.get(key)) for label, key in employer_map])
            )

        bank_map = [
            ("Bank Name", "bank_name"),
            ("Branch Name", "branch_name"),
            ("Branch Code", "branch_code"),
            ("Account Holder", "account_holder_name"),
            ("Account Number", "account_number"),
            ("Account Type", "account_type"),
        ]
        if bank_details:
            blocks.append(
                ("BANK DETAILS",
                 [_li(label, bank_details.get(key)) for label, key in bank_map])
            )

        blocks.append(
            ("LOAN DETAILS",
             [
                 _li("Loan ID", f"#{loan_id}"),
                 _li("Loan Type", loan_type),
                 _li("Amount", f"R {amount:,.2f}"),
                 _li("Interest Rate", f"{interest_rate}%"),
                 _li("Loan Term", f"{loan_term} months"),
                 _li("Status", "Pending Review"),
             ])
        )

        html_parts = [
            "<html>",
            "  <body style=\"font-family: Arial, sans-serif; "
            "padding: 20px;\">",
            "    <h2 style=\"color: #2c3e50;\">New Loan Application</h2>",
            "    <p>A new loan application has been submitted and "
            "requires review.</p>",
        ]
        for heading, rows in blocks:
            html_parts.append(
                "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">"
            )
            html_parts.append(f"      <p><strong>{heading}:</strong></p>")
            html_parts.append("      <ul>")
            html_parts.extend(rows)
            html_parts.append("      </ul>")
            html_parts.append("    </div>")
        html_parts.append(
            "    <p>Supporting documents (ID, bank statement, "
            "proof of residence) are attached to this email.</p>"
        )
        html_parts.append("    <br>")
        html_parts.append("    <p>Best regards,<br><strong>"
                         "RestoreLoans System</strong></p>")
        html_parts.append("  </body>")
        html_parts.append("</html>")
        body = "\n".join(html_parts)
        return self.send_email(
            to_emails, subject, body, attachments=attachments
        )


def client_details_from_user(user):
    if user is None:
        return None
    return {
        "title": user.title,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "id_number": user.id_number,
        "email": user.email,
        "phone_number": user.phone_number,
        "homephone": user.homephone,
        "home_add1": user.home_add1,
        "home_add2": user.home_add2,
        "suburb": user.suburb,
        "town": user.town,
        "postal_code": user.postal_code,
        "language": user.language,
        "dob": user.dob.isoformat() if user.dob else None,
        "nationality": user.nationality,
        "gender": user.gender.value if hasattr(user.gender, "value") else user.gender,
    }


def employer_details_from_company(company):
    if company is None:
        return None
    return {
        "name": company.name,
        "type": company.type,
        "pay_day_date": company.pay_day_date.isoformat() if company.pay_day_date else None,
        "address1": company.address1,
        "address2": company.address2,
        "town": company.town,
        "suburb": company.suburb,
        "post_code": company.post_code,
        "phone": company.phone,
        "appointed_on_date": company.appointed_on_date.isoformat() if company.appointed_on_date else None,
        "pay_date_shift": company.pay_date_shift,
        "contact_method": company.contact_method,
        "salary_freq": company.salary_freq,
        "pay_method": company.pay_method,
        "pay_day_of_week": company.pay_day_of_week,
        "contract_end_date": company.contract_end_date.isoformat() if company.contract_end_date else None,
    }


def bank_details_from_bank(bank):
    if bank is None:
        return None
    return {
        "bank_name": bank.bank_name,
        "branch_name": bank.branch_name,
        "branch_code": bank.branch_code,
        "account_holder_name": bank.account_holder_name,
        "account_number": bank.account_number,
        "account_type": bank.account_type.value if hasattr(bank.account_type, "value") else bank.account_type,
    }


# Create a singleton instance
email_service = EmailService()