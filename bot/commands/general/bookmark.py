import discord
from discord.ext import commands

from bot import client, logging, utils
from bot.constants import *


# @client.register("!bookmark", (4, 4), {"dm": False})
@commands.guild_only()
@client.command(
    name="bookmark",
    brief="Make a bookmark!",
    description="Creates a fancy-formatted bookmark in the current channel.",
    extras={"tags": ["general"]},
)
async def do_bookmark(
    ctx: commands.Context, title: str, link: str, description: str, usage: str
):
    """
    !bookmark "bookmark name" "bookmark link" "bookmark description" "Permissions/Usage"
    """

    embed = discord.Embed(title="Bookmark: {0}".format(title), color=EMBED_COLOR)
    embed.add_field(name="Bookmark Link", value=link)
    embed.add_field(name="Bookmark Description", value=description)
    embed.add_field(name="Permissions/Usage", value=usage)
    channel = ctx.channel
    await ctx.message.delete()
    await channel.send(embed=embed)
