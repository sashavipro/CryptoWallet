"""rest_api/src/infrastructure/providers/mailjet_provider.py."""

import logging
from pathlib import Path

import httpx

from src.infrastructure.settings import mail_settings

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
logger = logging.getLogger(__name__)


class MailjetProvider:
    """Asynchronous Mailjet provider for sending emails."""

    async def send_welcome_email(self, to_email: str, username: str) -> None:
        """Send a welcome email to a newly registered user."""
        if not mail_settings.MAILJET_API_KEY or not mail_settings.MAILJET_API_SECRET:
            logger.info(
                "Mock Email sent to %s. Configure Mailjet keys.",
                to_email,
            )
            return

        url = "https://api.mailjet.com/v3.1/send"

        template_path = TEMPLATES_DIR / "welcome.html"
        html_template = template_path.read_text(encoding="utf-8")

        html_part = html_template.format(
            username=username,
            dashboard_url=mail_settings.FRONTEND_DASHBOARD_URL,
        )

        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": mail_settings.MAILJET_SENDER_EMAIL,
                        "Name": mail_settings.MAILJET_SENDER_NAME,
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": username,
                        }
                    ],
                    "Subject": "Welcome to CryptoWallet!",
                    "HTMLPart": html_part,
                }
            ]
        }

        auth = (mail_settings.MAILJET_API_KEY, mail_settings.MAILJET_API_SECRET)

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, auth=auth)
            response.raise_for_status()
