import discord
from discord import Option

from bot import client
from bot.constants import *


# @client.register("!bookmark", (4, 4), {"dm": False})
@discord.guild_only()
@client.slash_command(
    name="bookmark",
    description="Creates a fancy-formatted bookmark in the current channel.",
)
async def bookmark(
        ctx: discord.ApplicationContext,
        title: Option(str, "Bookmark title"),
        link: Option(str, "Bookmark link"),
        description: Option(str, "Bookmark description"),
        usage: Option(str, "Bookmark permissions/usage")
):
    """
    !bookmark "bookmark name" "bookmark link" "bookmark description" "Permissions/Usage"
    """

    embed = discord.Embed(title="Bookmark: {0}".format(title), color=EMBED_COLOR)
    embed.add_field(name="Bookmark Link", value=link)
    embed.add_field(name="Bookmark Description", value=description)
    embed.add_field(name="Permissions/Usage", value=usage)
    await ctx.respond(embed=embed)
