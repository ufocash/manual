# OpenClaw Skills Manual

## Included skill

- `skills/gog-email-skill` - Send emails via "gog" SMTP (defaults to Gmail SMTP).

### Quick start

```bash
cd skills/gog-email-skill
cp .env.example .env
# fill in your SMTP credentials in .env, then export them
set -a && source .env && set +a

python3 scripts/send_email.py \
  --to "recipient@example.com" \
  --subject "Test email" \
  --body "Hello from OpenClaw"
```
