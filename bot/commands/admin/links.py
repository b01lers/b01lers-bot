import io
import re

import discord
from discord.ext import commands

from bot import client, logging
from bot.constants import *
from bot.database.links import purge_links, batch_insert_links, get_links_by_channel_id


@commands.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="rebuildlinks",
    description="Drop all links and re-scrape the server. (very slow)"
)
async def rebuild_links(ctx: discord.ApplicationContext) -> None:
    """!rebuildlinks
    Drop all links and re-scrape the server. USE SPARINGLY."""

    purge_links()
    interaction = await ctx.respond("Rebuilding link store. This will take a long time.")

    channels = client.guild.text_channels
    logging.info("Got text channels " + str(channels))
    url_re = re.compile(URL_REGEX)

    for channel in channels:
        # Use this SPARINGLY, it is very slow.
        channel_links = []

        async for channel_ctx in channel.history(limit=None):
            res = [(channel.id, x[0]) for x in url_re.findall(channel_ctx.content)]
            channel_links.extend(res)

        batch_insert_links(channel_links)
    logging.info("Link rebuild completed.")
    await interaction.followup.send("Link rebuild completed.")


# @client.register("!links", (0, 0), {"officer": False, "dm": False, "channel": True})
@commands.guild_only()
@client.slash_command(
    name="links",
    description="Collect all the links from the channel."
)
async def links(ctx: discord.ApplicationContext) -> None:
    """!links
    Sends the sender a text file containing all links from the channel the message was sent in."""

    url_strings = map(lambda link: link.link, get_links_by_channel_id(ctx.channel.id))
    logging.debug(f"Got links requested by {ctx.author}.")

    if not url_strings:
        await ctx.respond(f"No links available for channel {ctx.channel.mention}")
    else:
        linklist = io.BytesIO(bytes("\n".join(url_strings), "utf-8"))
        linkfile = discord.File(
            linklist, filename="links-{}.txt".format(ctx.channel.id)
        )
        await ctx.respond(f"Here are your links from channel {ctx.channel.mention}:", file=linkfile)
