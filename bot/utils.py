from bot import logging
from bot import database
from bot.constants import *

import time


def get_time():
    return int(time.time())


import hashlib


def generate_hash(record):
    m = hashlib.sha256()
    m.update(
        database.column_name_index("email", MEMBERS_COLUMNS, record).encode("utf-8")
        + SECRET
    )
    return m.hexdigest()


import urllib, requests
from bs4 import BeautifulSoup


class LookupResponse:
    def __init__(self, success, record=None, error="", log=""):
        self.success = success
        self.record = record
        self.error = error
        self.log = log


async def lookup_student(email, message):
    logging.info("Looking up student with email {0}".format(email))
    url = "https://www.purdue.edu/directory/"

    payload = "SearchString={0}".format(urllib.parse.quote(email))
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.5",
        "connection": "keep-alive",
        "content-length": "18",
        "content-type": "application/x-www-form-urlencoded",
        "host": "www.purdue.edu",
        "origin": "https://www.purdue.edu",
        "referer": "https://www.purdue.edu/directory/",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    try:
        response.raise_for_status()
    except:
        return LookupResponse(
            success=False,
            error="*ERROR**: The Purdue directory failed the lookup. Try again later. If this issue persists, contact an officer.",
            log="{0} tried to verify with email {1} and the Purdue directory returned an error.".format(
                message.author.display_name, email
            ),
        )

    response_document = BeautifulSoup(response.content, features="html.parser")
    try:
        entries = [tag.contents[0] for tag in response_document.find_all("td")]
        if len(entries) < 2:
            return LookupResponse(
                success=False,
                error="**ERROR**: It doesn't look like you're in the Purdue directory! Try again with a valid email or contact an officer.",
                log="{0} tried to verify with email {1} and failed.".format(
                    message.author.display_name, email
                ),
            )
        entries[1] = entries[1].contents[0]
        headers = [tag.contents[0] for tag in response_document.find_all("th")]
        headers[0] = headers[0].contents[0]
    except:
        return LookupResponse(
            success=False,
            error="**ERROR**: Looks like your entry in the Purdue directory is malformed. :( The officers have been notified.",
            log="{0} tried to verify with email {1} but their directory entry is malformed.".format(
                message.author.display_name, email
            ),
        )

    pinfo = {}
    pinfo["name"] = headers[0]
    for header, entry in zip(headers[1:], entries):
        pinfo[header.lower()] = entry

    # name, alias, email, token, validated
    record = (headers[0], str(message.author.id), email, generate_hash(email), 0)
    logging.info("Generated student record {0}".format(record))
    return LookupResponse(success=True, record=record)


import discord


def create_embed(message, title=None, error=False):
    if title:
        return discord.Embed(
            title=title,
            description=message,
            color=ERROR_COLOR if error else EMBED_COLOR,
        )
    else:
        return discord.Embed(
            description=message, color=ERROR_COLOR if error else EMBED_COLOR
        )


def parse_uid(uid):
    return re.findall("\d+", uid)[0]
