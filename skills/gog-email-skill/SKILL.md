---
name: gog-email-sender
description: Send emails from OpenClaw through GOG SMTP (Gmail-compatible by default) with secure env-based credentials.
requires:
  env:
    - GOG_SMTP_USERNAME
    - GOG_SMTP_PASSWORD
---

# GOG Email Sender

Use this skill when the user asks to send an email through "gog".

## What this skill does

- Sends plain-text or HTML email over SMTP.
- Supports multiple `to`, `cc`, and `bcc` recipients.
- Supports optional file attachments.
- Uses environment variables for credentials (no hard-coded secrets).

## Configuration

Required env vars:

- `GOG_SMTP_USERNAME`: SMTP login username (usually the sender mailbox)
- `GOG_SMTP_PASSWORD`: SMTP password or app password

Optional env vars:

- `GOG_SMTP_HOST`: SMTP host (default: `smtp.gmail.com`)
- `GOG_SMTP_PORT`: SMTP port (default: `587`)
- `GOG_SMTP_USE_SSL`: `true` for implicit SSL (default: `false`, uses STARTTLS)
- `GOG_FROM_EMAIL`: explicit sender address (default: `GOG_SMTP_USERNAME`)

## Usage

```bash
python3 scripts/send_email.py \
  --to "alice@example.com,bob@example.com" \
  --subject "Status update" \
  --body "Build completed successfully."
```

With HTML + attachment:

```bash
python3 scripts/send_email.py \
  --to "team@example.com" \
  --cc "manager@example.com" \
  --subject "Weekly report" \
  --body "Please see the attached report." \
  --html-body "<p>Please see the attached report.</p>" \
  --attachment "/tmp/report.pdf"
```

Dry-run validation (build message without sending):

```bash
python3 scripts/send_email.py \
  --to "test@example.com" \
  --subject "Dry run" \
  --body "Testing config." \
  --dry-run
```

## Notes

- If by "gog" you meant Google/Gmail, defaults already target Gmail SMTP.
- For Gmail personal accounts, use an app password (2FA required), not the account password.

## Troubleshooting

If you get `smtp_auth_failed` or Gmail `535 5.7.8 Username and Password not accepted`:

1. Enable Google 2-Step Verification.
2. Generate a Gmail App Password and set it as `GOG_SMTP_PASSWORD`.
3. Set `GOG_SMTP_USERNAME` to the full email address (for example `you@gmail.com`).
4. Re-run with `--dry-run` first to validate runtime config, then send.
