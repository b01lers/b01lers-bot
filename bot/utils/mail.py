import aiohttp

from bot import logging
from bot.constants import (
    MAILGUN_API_KEY,
    MAILGUN_API_BASE_URL,
    MAIL_SENDER_EMAIL,
    MAIL_SENDER_NAME,
)


async def send_mail(recipient_email: str, subject: str, body: str) -> bool:
    """Email specified address with subject and body."""
    async with aiohttp.ClientSession() as session:
        result = await session.post(
            f"{MAILGUN_API_BASE_URL}/messages",
            auth=aiohttp.BasicAuth("api", MAILGUN_API_KEY),
            data={
                "from": f"{MAIL_SENDER_NAME} <{MAIL_SENDER_EMAIL}>",
                "to": [recipient_email],
                "subject": subject,
                "html": body,
            },
        )
        response_code = result.status
        if response_code != 200:
            logging.error(
                f"Received error from Mailgun when sending to {recipient_email}: {await result.text()}"
            )
            return False
    return True
