import discord
import json
import re
import io

from bot import client, logging
from bot import utils, database, participation
from bot.constants import *


@client.register(
    "!rebuildlinks", (0, 0), {"officer": True, "dm": False, "channel": True}
)
async def rebuild_links(message, *args):
    """!rebuildlinks
    Drop all links and re-scrape the server. USE SPARINGLY."""

    database.purge_links()
    channels = await client.get_text_channels()
    logging.info("Got text channels " + str(channels))
    url_re = re.compile(URL_REGEX)
    await message.channel.send("Rebuilding link store. This will take a long time.")

    for channel in channels:
        # Use this SPARINGLY, it is very slow.
        channel_links = []

        async for message in channel.history(limit=None):
            res = [x[0] for x in url_re.findall(message.content)]
            channel_links.extend(res)

        database.insert_links(channel.id, channel_links)
    logging.info("Link rebuild completed.")
    await message.channel.send("Link rebuild completed.")

    return


@client.register("!links", (0, 0), {"officer": False, "dm": False, "channel": True})
async def links(message, *args):
    """!links
    Sends the sender a text file containing all links from the channel the message was sent in."""

    links = [x[0] for x in database.get_links(message.channel.id)]
    logging.info("Got links requested by {}:".format(message.author.id) + str(links))

    if not links:
        await message.author.send(
            "No links available for channel {}".format(message.channel.id)
        )
    else:
        linklist = io.BytesIO(bytes("\n".join(links), "utf-8"))
        linkfile = discord.File(
            linklist, filename="links-{}.txt".format(message.channel.id)
        )
        await message.author.send(
            "Here are your links from channel {}".format(message.channel.id)
        )
        await message.author.send(file=linkfile)
