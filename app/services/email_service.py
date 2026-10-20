import smtplib
import logging
import threading
import io
import zipfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as mime_encoders
from email.utils import formatdate, make_msgid
from typing import List, Optional, IO
import enum as _enum
import os

from app.env_loader import load_env

# Load .env from either the app/ or project-root location; injected
# environment variables always take precedence.
load_env()


class EmailService:
    def _from_header(self, sender_email):
        name = os.getenv("SENDER_NAME")
        if name:
            return f"{name} <{sender_email}>"
        return sender_email

    def __init__(self):
        # SMTP profile for the internal "New Loan Application" review email to
        # applicants@restoreloans.co.za. It defaults to the external Gmail
        # account: the domain's real inbox path runs through the Ucebox MX
        # (mx...ucebox.co.za), while mail submitted to mail.restoreloans.co.za
        # for its own domain is kept in that server's local store and never
        # reaches the mailbox the team reads — so company-SMTP sends are
        # accepted (250) but stay invisible. Set DOCS_EMAIL_SMTP_PROFILE to
        # "restoreloans" to send it over the company account once that server
        # relays through the domain MX (and 102.222.124.10 is authorised in
        # Ucebox).
        self.DOCS_EMAIL_PROFILE = (
            os.getenv("DOCS_EMAIL_SMTP_PROFILE", "external") or "external"
        ).strip().lower()
        self._load_profiles()
        # Backwards-compatible aliases pointing at the external profile.
        self.smtp_server = self.profiles["external"]["smtp_server"]
        self.smtp_port = self.profiles["external"]["smtp_port"]
        self.sender_email = self.profiles["external"]["sender_email"]
        self.sender_password = self.profiles["external"]["smtp_password"]
        self.smtp_username = self.profiles["external"]["smtp_username"]
        self.smtp_password = self.profiles["external"]["smtp_password"]
        self.envelope_sender = self.profiles["external"]["envelope_sender"]
        # Cached SMTP connection so consecutive emails reuse the already
        # established TLS session instead of reconnecting per message.
        self._conn_lock = threading.Lock()
        self._conn = None
        # Cache downloaded loan documents keyed by (loan_id, url) so repeat
        # emails don't re-fetch the same attachments from object storage.
        self._doc_attachments_cache = {}
        # Track loan ids for which the "New Loan Application" email has
        # already been sent, to avoid duplicate emails (e.g. when both the
        # create_loan auto-send and the manual docs endpoint fire for the
        # same loan).
        self._new_application_sent = set()
        # Track loan ids for which the "Loan Application Received"
        # acknowledgement email has already been sent, to avoid duplicates
        # (e.g. when both the create_loan auto-send and the manual
        # send-loan-email endpoint fire for the same loan).
        self._loan_ack_sent = set()

    def _load_profiles(self):
        self.profiles = {
            # Primary SMTP for all application emails.
            "external": {
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "smtp_username": os.getenv("SMTP_USERNAME"),
                "smtp_password": os.getenv("SMTP_PASSWORD"),
                "sender_email": os.getenv("SENDER_EMAIL"),
                "sender_name": os.getenv("SENDER_NAME"),
                "envelope_sender": (
                    os.getenv("MAIL_FROM")
                    or os.getenv("SMTP_ENVELOPE_SENDER")
                    or os.getenv("SENDER_EMAIL")
                ),
            },
        }
        # Optional failover SMTP used when the primary fails (e.g. Gmail).
        fallback_server = os.getenv("FALLBACK_SMTP_SERVER")
        if fallback_server:
            self.profiles["fallback"] = {
                "smtp_server": fallback_server,
                "smtp_port": int(os.getenv("FALLBACK_SMTP_PORT", "587")),
                "smtp_username": os.getenv("FALLBACK_SMTP_USERNAME"),
                "smtp_password": os.getenv("FALLBACK_SMTP_PASSWORD"),
                "sender_email": os.getenv("FALLBACK_SENDER_EMAIL"),
                "sender_name": os.getenv("FALLBACK_SENDER_NAME"),
                "envelope_sender": (
                    os.getenv("FALLBACK_MAIL_FROM")
                    or os.getenv("FALLBACK_SENDER_EMAIL")
                ),
            }
            # Company SMTP account (mail.restoreloans.co.za), always registered
            # as the "restoreloans" profile (independent of which profile the
            # docs email is routed through). Dedicated RESTORELOANS_* variables
            # win; otherwise the FALLBACK_* settings describe the same server,
            # so they are reused.
            self.profiles["restoreloans"] = {
                "smtp_server": (
                    os.getenv("RESTORELOANS_SMTP_SERVER") or fallback_server
                ),
                "smtp_port": int(
                    os.getenv("RESTORELOANS_SMTP_PORT")
                    or os.getenv("FALLBACK_SMTP_PORT", "587")
                ),
                "smtp_username": (
                    os.getenv("RESTORELOANS_SMTP_USERNAME")
                    or os.getenv("FALLBACK_SMTP_USERNAME")
                ),
                "smtp_password": (
                    os.getenv("RESTORELOANS_SMTP_PASSWORD")
                    or os.getenv("FALLBACK_SMTP_PASSWORD")
                ),
                "sender_email": (
                    os.getenv("RESTORELOANS_SENDER_EMAIL")
                    or os.getenv("FALLBACK_SENDER_EMAIL")
                ),
                "sender_name": (
                    os.getenv("RESTORELOANS_SENDER_NAME")
                    or os.getenv("FALLBACK_SENDER_NAME")
                    or os.getenv("SENDER_NAME")
                ),
                "envelope_sender": (
                    os.getenv("RESTORELOANS_MAIL_FROM")
                    or os.getenv("FALLBACK_MAIL_FROM")
                    or os.getenv("FALLBACK_SENDER_EMAIL")
                ),
            }

    @property
    def sender_header(self):
        return self._from_header(self.sender_email)

    @staticmethod
    def _safe_attachment_name(filename, fallback="document"):
        name = os.path.basename(str(filename or "").replace("\\", "/")).strip()
        name = "".join(
            ch for ch in name if ch.isprintable() and ch not in '"<>|:*?'
        )
        return name or fallback

    def _pack_attachments(self, attachments):
        """Bundle every attachment into one ZIP archive before sending.

        Uploaded application documents are multi-megabyte scans/photos, and
        each MIME part is base64-encoded on the wire (adding ~33%). Packing
        them into a single compressed archive keeps the message inside
        mailbox upload limits and gives the recipient one file to download.
        """
        if not attachments:
            return attachments
        # An archive that is already a ZIP is attached as-is.
        if len(attachments) == 1:
            name = str(attachments[0][1] or "")
            if name.lower().endswith(".zip"):
                return attachments
        buf = io.BytesIO()
        taken = set()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_bytes, filename in attachments:
                name = self._safe_attachment_name(filename)
                stem, ext = os.path.splitext(name)
                candidate = name
                counter = 1
                while candidate in taken:
                    candidate = f"{stem} ({counter}){ext}"
                    counter += 1
                taken.add(candidate)
                archive.writestr(candidate, file_bytes or b"")
        return [(buf.getvalue(), "application_documents.zip")]

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = True,
        attachments: Optional[List[tuple]] = None,
        profile: str = "external",
        profile_names: Optional[List[str]] = None,
    ) -> bool:
        if not to_emails:
            raise Exception("No recipient emails provided")

        # Compress attachments automatically before the message is built, so
        # every send path ships a single ZIP instead of raw multi-MB files.
        if attachments:
            try:
                attachments = self._pack_attachments(attachments)
            except Exception:
                logging.exception(
                    "Could not compress attachments; sending them uncompressed"
                )

        p = self.profiles.get(profile)
        if p is None:
            if profile != "external":
                logging.warning(
                    "SMTP profile '%s' is not configured (missing environment "
                    "variables); sending via the external Gmail account instead",
                    profile,
                )
            p = self.profiles["external"]
        content_type = "html" if is_html else "plain"

        def _build_message(sender_name, sender_email, to_list):
            from_header = (
                f"{sender_name} <{sender_email}>" if sender_name else sender_email
            )
            message = MIMEText(body, content_type, _charset="utf-8")
            message["From"] = from_header
            message["To"] = ", ".join(to_list)
            message["Subject"] = subject
            message["Date"] = formatdate(localtime=True)
            message["Message-ID"] = make_msgid(domain="restoreloans.co.za")
            if attachments:
                wrapper = MIMEMultipart("mixed")
                wrapper["From"] = from_header
                wrapper["To"] = ", ".join(to_list)
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
            return message

        # Dual/multi send (e.g. both restoreloans and Gmail): each recipient is
        # attempted on every profile; succeeds if any profile accepts the message.
        if profile_names:
            for recipient in to_emails:
                last_err = None
                ok = False
                for prof_name in profile_names:
                    prof = self.profiles.get(prof_name)
                    if prof is None:
                        continue
                    try:
                        message = _build_message(
                            prof["sender_name"] or "", prof["sender_email"], [recipient]
                        )
                        self._send_via_profile(prof, message.as_string(), [recipient])
                        ok = True
                    except Exception as e:
                        last_err = e
                        logging.warning(
                            "Email via %s to %s failed: %s", prof_name, recipient, e
                        )
                if not ok:
                    self.close()
                    raise Exception(f"Failed to send email: {str(last_err)}")
            return True

        # Single send: build once for the selected profile, and fail over to
        # the other configured account only if the primary raises at the
        # connection/SMTP level (RestoreLoans SMTP <-> Gmail).
        message = _build_message(p["sender_name"] or "", p["sender_email"], to_emails)
        flat = message.as_string()
        try:
            self._send_via_profile(p, flat, to_emails)
            return True
        except Exception as e:
            fallback_name = (
                "external" if profile == "restoreloans" else "fallback"
            )
            fallback = self.profiles.get(fallback_name)
            if fallback is not None and fallback is not p:
                try:
                    self._send_via_profile(fallback, flat, to_emails)
                    logging.warning(
                        "SMTP profile '%s' failed (%s); message sent via '%s'",
                        profile, e, fallback_name,
                    )
                    return True
                except Exception as fb_err:
                    logging.error(
                        "Email send failed on primary (%s) and fallback (%s)", e, fb_err
                    )
            self.close()
            raise Exception(f"Failed to send email: {str(e)}")

    def _send_via_profile(self, p, message_bytes, to_emails):
        is_local = p["smtp_server"] in ("127.0.0.1", "localhost")
        self._send_via_cached(
            p["smtp_server"], p["smtp_port"], p["smtp_username"], p["smtp_password"],
            is_local, p["envelope_sender"] or p["sender_email"], to_emails, message_bytes,
        )

    def _open_connection(self, server, port, username, password, is_local):
        if is_local:
            srv = smtplib.SMTP(server, port, timeout=30)
            srv.ehlo("restoreloans.co.za")
            return srv
        if port == 465:
            # Implicit TLS (SMTPS)
            srv = smtplib.SMTP_SSL(server, port, timeout=30, local_hostname="restoreloans.co.za")
            srv.ehlo("restoreloans.co.za")
            srv.login(username, password)
            return srv
        # STARTTLS (e.g. port 587)
        srv = smtplib.SMTP(server, port, timeout=30)
        srv.ehlo("restoreloans.co.za")
        srv.starttls()
        srv.ehlo("restoreloans.co.za")
        srv.login(username, password)
        return srv

    def _send_via_cached(
        self, server, port, username, password, is_local,
        envelope_sender, to_emails, message_bytes,
    ):
        with self._conn_lock:
            cached = self._conn
            if cached is not None and cached[0] == (server, port):
                try:
                    cached[1].sendmail(envelope_sender, to_emails, message_bytes)
                    return
                except Exception:
                    # The cached connection may have gone stale; drop it and
                    # reconnect once before giving up.
                    try:
                        cached[1].quit()
                    except Exception:
                        pass
                    self._conn = None
            srv = self._open_connection(server, port, username, password, is_local)
            try:
                srv.sendmail(envelope_sender, to_emails, message_bytes)
                self._conn = ((server, port), srv)
            except Exception:
                try:
                    srv.quit()
                except Exception:
                    pass
                self._conn = None
                raise

    def close(self):
        """Close the cached SMTP connection (e.g. on application shutdown)."""
        with self._conn_lock:
            if self._conn is not None:
                try:
                    self._conn[1].quit()
                except Exception:
                    pass
                self._conn = None

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
        force: bool = False,
    ):
        # Avoid duplicate "Loan Application Received" emails for the same loan.
        if not force and loan_id is not None and loan_id in self._loan_ack_sent:
            return True

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
                    "line-height: 1.6; padding: 20px;\">",
                    f"    <p>Good day {borrower_name},</p>",
                    "",
                    "    <p>This message serves to acknowledge receipt of your "
                    "loan application. Our team is currently reviewing the "
                    "details provided.</p>",
                    "",
                    "    <p>If any further documentation or clarification is "
                    "needed, we will reach out to you promptly.</p>",
                    "",
                    "    <p>Thank you for choosing Restore Loans. We will keep "
                    "you informed throughout the process.</p>",
                    "",
                    "    <p>Warm regards,<br><strong>Restore Loans</strong></p>",
                    "  </body>",
                    "</html>",
                ]
            )
        result = self.send_email(to_emails, subject, body, is_html=is_html)
        if loan_id is not None:
            self._loan_ack_sent.add(loan_id)
        return result

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

    def _download_document_attachments(self, loan):
        """Download the ID, bank statement and proof of residence attached to
        the loan record and return them as email attachments. Results are
        cached per loan to keep repeat sends fast."""
        import requests as http_requests

        attachments = []
        loan_id = getattr(loan, "id", None)
        for attr, label in [
            ("id_path", "id_document"),
            ("bank_path", "bank_statement"),
            ("proof_of_residence_path", "proof_of_residence"),
        ]:
            url = getattr(loan, attr, None)
            if url:
                key = (loan_id, url)
                cached = self._doc_attachments_cache.get(key)
                if cached is not None:
                    attachments.append(cached)
                    continue
                try:
                    resp = http_requests.get(url, timeout=30)
                    resp.raise_for_status()
                    filename = url.split("/")[-1].split("?")[0] or f"{label}.pdf"
                    attachment = (resp.content, filename)
                    if len(self._doc_attachments_cache) < 128:
                        self._doc_attachments_cache[key] = attachment
                    attachments.append(attachment)
                except Exception as exc:
                    logging.warning(
                        "Could not download %s from %s for loan %s: %s",
                        label, url, getattr(loan, "id", None), exc,
                    )
        return attachments or None

    def send_application_with_docs_email(
        self,
        loan,
        client,
        employer=None,
        bank=None,
        to_emails: Optional[List[str]] = None,
        attachments: Optional[List[tuple]] = None,
        force: bool = False,
    ):
        loan_id = getattr(loan, "id", None)
        # Avoid duplicate "New Loan Application" emails for the same loan.
        if not force and loan_id is not None and loan_id in self._new_application_sent:
            return True

        # Ensure the supporting documents are always attached, whether the
        # caller supplied them or not (download from the loan record).
        if not attachments:
            attachments = self._download_document_attachments(loan)

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
                "proof of residence) are attached to this email as a single "
                "compressed ZIP archive (application_documents.zip).</p>",
                "    <br>",
                "    <p>Best regards,<br><strong>"
                "RestoreLoans System</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        recipients = to_emails or ["applicants@restoreloans.co.za"]
        # Profile for the review mail is switchable (see __init__); it defaults
        # to the Gmail account because that is the path that reaches the
        # mailbox the team reads.
        result = self.send_email(
            recipients, subject, body,
            attachments=attachments,
            profile=self.DOCS_EMAIL_PROFILE,
        )
        if loan_id is not None:
            self._new_application_sent.add(loan_id)
        return result

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

    def send_welcome_email(
        self,
        first_name: str,
        last_name: str,
        to_email: str,
    ):
        subject = "Welcome to RestoreLoans"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "line-height: 1.6; padding: 20px;\">",
                f"    <p>Good day{', ' + (first_name or '').strip() if first_name else ''},</p>",
                "",
                "    <p>Welcome to <strong>RestoreLoans</strong>. "
                "We’re excited to have you join our community and appreciate "
                "you taking the time to register.</p>",
                "",
                "    <p>Your account has been successfully created, and you now "
                "have access to our loan services, application tools, and "
                "support resources. Our goal is to make your financial journey "
                "simple, transparent, and stress‑free.</p>",
                "",
                "    <p>If you need any assistance getting started or have "
                "questions about our loan products, our team is here to help. "
                "Feel free to reach out at any time.</p>",
                "",
                "    <p>Thank you for choosing <strong>RestoreLoans</strong>. "
                "We look forward to supporting you.</p>",
                "",
                "    <p>Kind regards,<br>"
                "<strong>RestoreLoans Team</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email([to_email], subject, body)

    def send_password_reset_email(
        self,
        to_email: str,
        first_name: str,
        otp: str,
        expires_minutes: int = 15,
    ):
        subject = "Reset your Restore Loans password"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "line-height: 1.6; padding: 20px;\">",
                f"    <p>Good day {first_name or 'there'},</p>",
                "",
                "    <p>We received a request to reset the password for your "
                "<strong>Restore Loans</strong> account.</p>",
                "",
                "    <p>Use the code below to choose a new password:</p>",
                "",
                "    <div style=\"background-color: #f0f7ff; padding: 20px; "
                "border-left: 4px solid #3b82f6; border-radius: 5px; "
                "margin: 20px 0; text-align: center;\">",
                f"      <p style=\"font-size: 30px; letter-spacing: 8px; "
                f"font-weight: bold; margin: 0;\">{otp}</p>",
                "    </div>",
                "",
                f"    <p>This code expires in <strong>{expires_minutes} "
                "minutes</strong> and can only be used once.</p>",
                "",
                "    <p>If you did not request a password reset, you can safely "
                "ignore this email &mdash; your password will not change.</p>",
                "",
                "    <p>Warm regards,<br>"
                "<strong>Restore Loans</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email([to_email], subject, body)

    def send_password_changed_email(
        self,
        to_email: str,
        first_name: str,
    ):
        subject = "Your Restore Loans password was changed"
        body = "\n".join(
            [
                "<html>",
                "  <body style=\"font-family: Arial, sans-serif; "
                "line-height: 1.6; padding: 20px;\">",
                f"    <p>Good day {first_name or 'there'},</p>",
                "",
                "    <p>The password for your <strong>Restore Loans</strong> "
                "account was changed successfully.</p>",
                "",
                "    <div style=\"background-color: #f0f7ff; padding: 15px; "
                "border-left: 4px solid #3b82f6; border-radius: 5px; "
                "margin: 20px 0;\">",
                "      <p>If this was not you, please contact our support team "
                "immediately.</p>",
                "    </div>",
                "",
                "    <p>Warm regards,<br>"
                "<strong>Restore Loans</strong></p>",
                "  </body>",
                "</html>",
            ]
        )
        return self.send_email([to_email], subject, body)


# Create a singleton instance
email_service = EmailService()