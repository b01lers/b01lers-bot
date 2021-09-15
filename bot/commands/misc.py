import discord

from bot import client, logging, participation, utils
from bot.constants import *


@client.register("!yeet", (0, 0), {"dm": False})
async def do_yeet(message, *args):
    """!yeet
    Just y33t!"""

    channel = message.channel
    await message.delete()
    async for omessage in channel.history(limit=20):
        if not omessage.content.startswith("!yeet"):
            await omessage.add_reaction(
                discord.utils.get(client.guild.emojis, name="yeet")
            )
            if omessage.author.id not in (client.user.id, message.author.id):
                participation.give_yeet_points(omessage, message.author.id)
            return


# This command is not currently used.
# @client.register("!restore", (0, 0), {"channel": False})
async def restore_mail(self, message):
    """!restore
    Restores a member."""

    embed = utils.create_embed(":broken_heart: Removed Member Mail:")
    embed.add_field(name="Contents", value=message.content[8:])
    await client.update_channel.send(embed=embed)
    return

@client.register("!dm", (2, 2), {"dm": True, "officer": True})
async def do_dm(message, *args):
    uid, rest = args[0], args[1:]
    try:
        uid = int(utils.parse_uid(uid))
    except:
        await message.author.send(
            embed=utils.create_embed(
                "That user does not exist."
            )
        )

    user = await client.get_member(uid)
    if user is None:
        await message.author.send(
            embed=utils.create_embed(
                "That user does not exist."
            )
        )

    try:
        msg = " ".join(rest)
        await user.send(msg)
    except:
        await message.author.send(
            embed=utils.create_embed(
                "Couldn't send message to user."
            )
        )