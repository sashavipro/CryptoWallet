"""rest_api/src/infrastructure/providers/mailjet_provider.py."""

import asyncio
import logging
from http import HTTPStatus
from pathlib import Path

from mailjet_rest import Client

from src.infrastructure.settings import MailSettings

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
logger = logging.getLogger(__name__)


class MailjetProvider:
    """Asynchronous Mailjet provider for sending emails using the official SDK."""

    def __init__(self, settings: MailSettings) -> None:
        """Initialize provider with Mailjet settings."""
        self.settings = settings

        if self.settings.MAILJET_API_KEY and self.settings.MAILJET_API_SECRET:
            self.mailjet_client = Client(
                auth=(self.settings.MAILJET_API_KEY, self.settings.MAILJET_API_SECRET),
                version="v3.1",
            )
        else:
            self.mailjet_client = None

    async def send_welcome_email(self, to_email: str, username: str) -> None:
        """Send a welcome email to a newly registered user."""
        if not self.mailjet_client:
            logger.info("Mock Email sent to %s. Configure Mailjet keys.", to_email)
            return

        logger.info("Sending welcome email to %s", to_email)

        template_path = TEMPLATES_DIR / "welcome.html"
        html_template = template_path.read_text(encoding="utf-8")

        html_part = html_template.format(
            username=username,
            dashboard_url=self.settings.FRONTEND_DASHBOARD_URL,
        )

        data = {
            "Messages": [
                {
                    "From": {
                        "Email": self.settings.MAILJET_SENDER_EMAIL,
                        "Name": self.settings.MAILJET_SENDER_NAME,
                    },
                    "To": [{"Email": to_email, "Name": username}],
                    "Subject": "Welcome to CryptoWallet!",
                    "TextPart": (
                        f"Dear {username}, welcome to CryptoWallet. "
                        "Please visit your dashboard: "
                        f"{self.settings.FRONTEND_DASHBOARD_URL}"
                    ),
                    "HTMLPart": html_part,
                }
            ]
        }

        try:
            result = await asyncio.to_thread(self.mailjet_client.send.create, data=data)
        except Exception:
            logger.exception(
                "Exception occurred during Mailjet API call for %s",
                to_email,
            )
            raise

        if result.status_code == HTTPStatus.OK:
            logger.info("Successfully sent welcome email to %s", to_email)
        else:
            logger.error(
                "Failed to send email to %s. Status: %s, Response: %s",
                to_email,
                result.status_code,
                result.json(),
            )
            err_msg = f"Mailjet API Error: {result.status_code}"
            raise ValueError(err_msg)
