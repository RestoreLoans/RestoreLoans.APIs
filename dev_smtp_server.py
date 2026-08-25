"""Local development SMTP server that captures emails to disk.

Run: python dev_smtp_server.py
Listens on 127.0.0.1:1025. No authentication required.
Saves every email as an .html file in the dev_emails/ folder.
"""
import asyncio
import os
from datetime import datetime
from email import policy
from email.parser import BytesParser

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP

SAVE_DIR = os.path.join(os.path.dirname(__file__), "dev_emails")
os.makedirs(SAVE_DIR, exist_ok=True)


class DevMessageHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        envelope.mail_from = address
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        mail_from = envelope.mail_from
        rcpt_tos = ", ".join(envelope.rcpt_tos)

        msg = BytesParser(policy=policy.default).parsebytes(envelope.content)
        subject = msg.get("Subject", "(no subject)")
        to_header = msg.get("To", rcpt_tos)

        # Build a human-readable filename
        safe_subject = "".join(c if c.isalnum() or c in " _-" else "" for c in subject)[:60]
        filename = f"{timestamp}_{safe_subject}.eml"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(envelope.content)

        print(f"[DEV SMTP] Saved email: {filename}")
        print(f"  From:    {mail_from}")
        print(f"  To:      {to_header}")
        print(f"  Subject: {subject}")
        print(f"  File:    {filepath}")

        return "250 Message saved"


def main():
    handler = DevMessageHandler()
    controller = Controller(
        handler,
        hostname="127.0.0.1",
        port=1025,
    )
    controller.start()
    print(f"[DEV SMTP] Listening on 127.0.0.1:1025")
    print(f"[DEV SMTP] Saving emails to {SAVE_DIR}")
    print(f"[DEV SMTP] Press Ctrl+C to stop")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n[DEV SMTP] Shutting down...")
        controller.stop()


if __name__ == "__main__":
    main()
