import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as mime_encoders
from email.utils import formatdate, make_msgid
from typing import List, Optional, IO
import enum as _enum
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class EmailService:
    def _from_header(self, sender_email):
        name = os.getenv("SENDER_NAME")
        if name:
            return f"{name} <{sender_email}>"
        return sender_email

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_username = os.getenv("SMTP_USERNAME", self.sender_email)
        self.smtp_password = os.getenv("SMTP_PASSWORD", self.sender_password)

    @property
    def sender_header(self):
        return self._from_header(self.sender_email)

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
        message["From"] = self.sender_header
        message["To"] = ", ".join(to_emails)
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain="restoreloans.co.za")

        if attachments:
            wrapper = MIMEMultipart("mixed")
            wrapper["From"] = self.sender_header
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
        client=None,
        employer=None,
        bank=None,
        loan=None,
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
                    f"    <p>Dear {borrower_name},</p>",
                    "",
                    "    <p>Thank you for submitting your loan application. "
                    "We are pleased to confirm that it has been successfully "
                    "received and is now in the review stage.</p>",
                    "",
                    "    <h2 style=\"color: #2c3e50;\">Application Details</h2>",
                    "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                    "border-radius: 5px; margin: 20px 0;\">",
                    "      <ul>",
                    f"        <li>Loan ID: #{loan_id}</li>",
                    f"        <li>Amount: R{amount:,.2f}</li>",
                    "        <li>Status: Pending Review</li>",
                    "      </ul>",
                    "    </div>",
                    "",
                    "    <p>Our team is currently assessing your application. "
                    "Should any additional information or documents be "
                    "required, we will contact you directly.</p>",
                    "",
                    "    <p>Thank you for choosing RestoreLoans. We will "
                    "provide an update shortly.</p>",
                    "",
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

    def _build_details_html(self, client, employer, bank, loan):
        """Build the full CLIENT/EMPLOYER/BANK/LOAN details HTML block.

        Returns a list of lines to be joined and spliced into an email body.
        """

        def fmt(value, default="N/A"):
            if value is None or value == "":
                return default
            if isinstance(value, _enum.Enum):
                return str(value.value)
            if hasattr(value, "isoformat"):
                return value.isoformat()
            return str(value)

        def section(title, pairs):
            return [
                f"    <p><strong>{title}:</strong></p>",
                "    <ul>",
                *[f"        <li>{k}: {v}</li>" for k, v in pairs],
                "    </ul>",
            ]

        client_pairs = [
            ("Title", fmt(getattr(client, "title", None))),
            ("First Name", fmt(getattr(client, "first_name", None))),
            ("Last Name", fmt(getattr(client, "last_name", None))),
            ("ID Number", fmt(getattr(client, "id_number", None))),
            ("Email", fmt(getattr(client, "email", None))),
            ("Cellphone Number", fmt(getattr(client, "phone_number", None))),
            ("Home Phone", fmt(getattr(client, "homephone", None))),
            ("Home Address", fmt(getattr(client, "home_add1", None))),
            ("Home Address 2", fmt(getattr(client, "home_add2", None))),
            ("Suburb", fmt(getattr(client, "suburb", None))),
            ("Town", fmt(getattr(client, "town", None))),
            ("Postal Code", fmt(getattr(client, "postal_code", None))),
            ("Language", fmt(getattr(client, "language", None))),
            ("Date of Birth", fmt(getattr(client, "dob", None))),
            ("Nationality", "South Africa" if (getattr(client, "nationality", None) or 0) == 0 else fmt(getattr(client, "nationality", None))),
            ("Gender", fmt(getattr(client, "gender", None))),
        ]

        employer_pairs = [
            ("Company Name", fmt(getattr(employer, "name", None))),
            ("Type", fmt(getattr(employer, "type", None))),
            ("Pay Day Date", fmt(getattr(employer, "pay_day_date", None))),
            ("Address 1", fmt(getattr(employer, "address1", None))),
            ("Address 2", fmt(getattr(employer, "address2", None))),
            ("Town", fmt(getattr(employer, "town", None))),
            ("Suburb", fmt(getattr(employer, "suburb", None))),
            ("Postal Code", fmt(getattr(employer, "post_code", None))),
            ("Phone", fmt(getattr(employer, "phone", None))),
            ("Appointed On", fmt(getattr(employer, "appointed_on_date", None))),
            ("Pay Date Shift", fmt(getattr(employer, "pay_date_shift", None))),
            ("Contact Method", fmt(getattr(employer, "contact_method", None))),
            ("Salary Frequency", fmt(getattr(employer, "salary_freq", None))),
            ("Pay Method", fmt(getattr(employer, "pay_method", None))),
            ("Pay Day of Week", fmt(getattr(employer, "pay_day_of_week", None))),
            ("Contract End Date", fmt(getattr(employer, "contract_end_date", None))),
        ]

        bank_pairs = [
            ("Bank Name", fmt(getattr(bank, "bank_name", None))),
            ("Branch Name", fmt(getattr(bank, "branch_name", None))),
            ("Branch Code", fmt(getattr(bank, "branch_code", None))),
            ("Account Holder", fmt(getattr(bank, "account_holder_name", None))),
            ("Account Number", fmt(getattr(bank, "account_number", None))),
            ("Account Type", fmt(getattr(bank, "account_type", None))),
        ]

        loan_type = fmt(getattr(loan, "loan_type", None))
        amount = getattr(loan, "loan_amount", 0) or 0
        interest = getattr(loan, "interest_rate", 0) or 0
        term = getattr(loan, "loan_term", 0) or 0
        loan_pairs = [
            ("Loan ID", f"#{getattr(loan, 'id', None)}"),
            ("Loan Type", loan_type),
            ("Amount", f"R {amount:,.2f}"),
            ("Interest Rate", f"{interest}%"),
            ("Loan Term", f"{term} months"),
            ("Status", "Pending Review"),
        ]

        return [
            *section("CLIENT DETAILS", client_pairs),
            *section("EMPLOYER DETAILS", employer_pairs),
            *section("BANK DETAILS", bank_pairs),
            *section("LOAN DETAILS", loan_pairs),
        ]

    def send_application_with_docs_email(
        self,
        loan,
        client,
        employer=None,
        bank=None,
        to_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None,
    ):
        subject = "New Loan Application"

        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "padding: 20px;\">",
                "    <h2 style=\"color: #2c3e50;\">New Loan Application</h2>",
                "    <p>A new loan application has been submitted and "
                "requires review.</p>",
                "    <div style=\"background-color: #f8f9fa; padding: 15px; "
                "border-radius: 5px; margin: 20px 0;\">",
                *self._build_details_html(client, employer, bank, loan),
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
            to_emails or ["applicants@restoreloans.co.za"], subject, body,
            attachments=attachments,
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