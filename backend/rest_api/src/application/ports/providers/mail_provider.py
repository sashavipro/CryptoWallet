"""rest_api/src/application/ports/providers/mail_provider.py."""

from typing import Protocol


class MailProvider(Protocol):
    """Port for email delivery via SMTP or external API."""

    async def send_welcome_email(self, to_email: str, username: str) -> None:
        """Send a welcome email to a newly registered user."""
        ...
