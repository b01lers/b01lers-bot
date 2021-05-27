import requests

from bot import logging
from bot.constants import *


def send_mail(recipient, subject, text):
    logging.info(
        "Sending mail to {0} with subject {1} and text {2}".format(
            recipient, subject, text
        )
    )
    response = requests.post(
        "{0}/messages".format(MAILGUN_API_BASE_URL),
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": "Purdue Capture The Flag Team <b01lers@b01lers.com>",
            "to": [recipient],
            "subject": subject,
            "text": text,
        },
    )
    logging.info("Received mailgun message {0}".format(response.content))
