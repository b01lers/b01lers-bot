import discord

from bot import client, logging
from bot import utils
from bot.constants import *


@client.register("!bookmark", (4, 4), {"dm": False})
async def start_poll(message, *args):
    """!bookmark "bookmark name" "bookmark link" "bookmark description" "Permissions/Usage"
    Creates a fancy-formatted bookmark in the current channel."""

    title, *options = args

    if not message.author.bot:
        embed = discord.Embed(title="Bookmark: {0}".format(title), color=EMBED_COLOR)
        embed.add_field(name="Bookmark Link", value=options[0])
        embed.add_field(name="Bookmark Description", value=options[1])
        embed.add_field(name="Permissions/Usage", value=options[2])
        channel = message.channel
        await message.delete()
        await channel.send(embed=embed)
    return
