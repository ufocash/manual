#!/usr/bin/env python3
"""Send email via SMTP for the OpenClaw gog-email-sender skill."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_recipients(raw_values: list[str] | None) -> list[str]:
    recipients: list[str] = []
    for raw in raw_values or []:
        for part in raw.split(","):
            addr = part.strip()
            if addr:
                recipients.append(addr)
    return recipients


def _attach_files(message: EmailMessage, attachments: list[str]) -> None:
    for path_str in attachments:
        path = Path(path_str).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Attachment not found: {path}")

        content = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(path.name)
        if mime_type:
            maintype, subtype = mime_type.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"

        message.add_attachment(
            content,
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )


def build_message(args: argparse.Namespace, from_email: str) -> tuple[EmailMessage, list[str]]:
    to_addrs = _parse_recipients(args.to)
    cc_addrs = _parse_recipients(args.cc)
    bcc_addrs = _parse_recipients(args.bcc)
    all_recipients = [*to_addrs, *cc_addrs, *bcc_addrs]

    if not all_recipients:
        raise ValueError("At least one recipient is required via --to/--cc/--bcc")

    if not args.subject:
        raise ValueError("Subject is required")

    if not args.body and not args.html_body:
        raise ValueError("Either --body or --html-body is required")

    msg = EmailMessage()
    msg["From"] = from_email
    if to_addrs:
        msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    msg["Subject"] = args.subject

    text_body = args.body or " "
    msg.set_content(text_body)

    if args.html_body:
        msg.add_alternative(args.html_body, subtype="html")

    _attach_files(msg, args.attachment or [])
    return msg, all_recipients


def send_via_smtp(
    message: EmailMessage,
    recipients: list[str],
    host: str,
    port: int,
    username: str,
    password: str,
    use_ssl: bool,
) -> None:
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_cls(host, port, timeout=30) as client:
        if not use_ssl:
            client.ehlo()
            client.starttls()
            client.ehlo()
        client.login(username, password)
        client.send_message(message, to_addrs=recipients)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send email via GOG SMTP")
    parser.add_argument("--to", action="append", help="To recipients (comma-separated allowed)")
    parser.add_argument("--cc", action="append", help="Cc recipients (comma-separated allowed)")
    parser.add_argument("--bcc", action="append", help="Bcc recipients (comma-separated allowed)")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", default="", help="Plain text body")
    parser.add_argument("--html-body", default="", help="Optional HTML body")
    parser.add_argument("--attachment", action="append", help="Attachment file path")
    parser.add_argument("--dry-run", action="store_true", help="Validate and build message only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    smtp_host = os.getenv("GOG_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("GOG_SMTP_PORT", "587"))
    smtp_user = os.getenv("GOG_SMTP_USERNAME", "").strip()
    smtp_pass = os.getenv("GOG_SMTP_PASSWORD", "").strip()
    use_ssl = _env_bool("GOG_SMTP_USE_SSL", default=False)
    from_email = os.getenv("GOG_FROM_EMAIL", smtp_user).strip()

    if not smtp_user:
        raise ValueError("Missing required env var: GOG_SMTP_USERNAME")
    if not smtp_pass:
        raise ValueError("Missing required env var: GOG_SMTP_PASSWORD")
    if not from_email:
        raise ValueError("Unable to determine sender address (set GOG_FROM_EMAIL)")

    message, recipients = build_message(args, from_email=from_email)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_ok",
                    "smtp_host": smtp_host,
                    "smtp_port": smtp_port,
                    "use_ssl": use_ssl,
                    "from": from_email,
                    "recipient_count": len(recipients),
                    "subject": args.subject,
                    "attachments": len(args.attachment or []),
                },
                ensure_ascii=True,
            )
        )
        return 0

    send_via_smtp(
        message=message,
        recipients=recipients,
        host=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_pass,
        use_ssl=use_ssl,
    )

    print(
        json.dumps(
            {
                "status": "sent",
                "from": from_email,
                "recipient_count": len(recipients),
                "subject": args.subject,
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
