import datetime
import logging
import random
import re
import sys
import traceback

import discord
from discord import RawReactionActionEvent, Message
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument, CommandNotFound, MissingRole, NoPrivateMessage, \
    PrivateMessageOnly

from bot import client, constants, LIVE_CTF_CATEGORY, URL_REGEX
from bot.database.links import batch_insert_links
from bot.helpers import participation
from bot.helpers.participation import give_message_points, give_ctf_message_points
from bot.utils.messages import create_embed


@client.event
async def on_ready() -> None:
    """Event handler for event when bot is ready."""
    # Initialize global data
    client.update_channel = client.get_channel(constants.UPDATE_CHANNEL)
    client.general_channel = client.get_channel(constants.GENERAL_CHANNEL)
    client.approval_channel = client.get_channel(constants.APPROVAL_CHANNEL)
    client.guild = client.get_guild(constants.GUILD)
    client.ctfs = client.get_channel(constants.LIVE_CTF_CATEGORY)
    client.archive = client.get_channel(constants.ARCHIVE_CATEGORY)
    client.me = await client.guild.fetch_member(client.user.id)

    # TODO: Implement
    # self.give_voice_points.start()
    await client.ensure_ranks()
    await client.update_ranks()

    logging.info("B01lers bot is now at your service.")


@client.event
async def on_member_join(member: discord.Member) -> None:
    """Event handler for event when a member joins the server."""
    await member.send(
        "Welcome to b01lers! To verify yourself as a Purdue University student, just type `!verify "
        "<your-@purdue.edu-email-address-here>` "
    )


@client.event
async def on_member_remove(member: discord.Member):
    """Event handler for event when a member leaves the server."""
    await client.update_channel.send(
        embed=create_embed(
            "{0} has left the server. {1}".format(
                member.display_name,
                random.choice(
                    (
                        "Aww.",
                        "Darn.",
                        "Oof.",
                        "SMH.",
                        "Good Riddance.",
                        "Bye...Skid!",
                        "Couldn't Hack It :triumph:",
                        "You'll Miss Out!",
                        "Probably Inactive Anyway...",
                        "Unbelievable.",
                        "Quick, officers! Recruit someone, we're clearly hemmorhaging members! Not! Haha, bye!",
                    )
                ),
            )
        )
    )


@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    """Event handler for event when a member adds a reaction to a message."""
    # Come on Python!
    # (cid, mid, uid, emoji) = payload
    cid = payload.channel_id
    mid = payload.message_id
    uid = payload.user_id
    emoji = payload.emoji

    try:
        cid = int(cid)
        mid = int(mid)
    except:
        await client.update_channel.send(
            embed=create_embed(
                f"Something happened when reacting to a message: could not parse {cid}:{mid}.",
                error=True,
            )
        )
        return
    channel = client.get_channel(cid)
    if channel is None:
        await client.update_channel.send(
            embed=create_embed(
                f"Something happened when reacting to a message: could not find channel {cid}.",
                error=True,
            )
        )
        return
    msg = await channel.fetch_message(mid)
    if msg is None:
        await client.update_channel.send(
            embed=create_embed(
                f"Something happened when reacting to a message: could not find message {cid}:{mid}.",
                error=True,
            )
        )
        return

    if uid != client.user.id:
        is_officer = await client.is_officer_id(uid)
        if (
                cid == constants.APPROVAL_CHANNEL
                and is_officer
                and msg.author.id == client.user.id
                and len(msg.embeds) == 1
                and msg.embeds[0].footer.text == "APPROVAL NEEDED"
        ):
            if emoji == constants.DONE_EMOJI:
                await client.commands["!accept"].func(msg)
            elif emoji == constants.CANCEL_EMOJI:
                await client.commands["!reject"].func(msg)
        elif emoji == "yeet" and uid != msg.author.id:
            participation.give_yeet_points(msg, uid)


@client.event
async def on_message(message: Message) -> None:
    # Ignore self messages
    if message.author.id == client.me.id:
        return

    # TODO: Migrate to cogs and remove hardcoded stuff
    if not message.content.startswith("!"):
        is_dm = isinstance(message.channel, discord.channel.DMChannel)
        is_channel = isinstance(message.channel, discord.channel.TextChannel)

        if is_dm:
            give_message_points(message)
            await client.update_channel.send(
                embed=create_embed(
                    "**{0}** has sent a DM: `{1}`".format(
                        message.author, message.content
                    )
                )
            )
        elif is_channel:
            if message.channel.category_id == LIVE_CTF_CATEGORY:
                give_ctf_message_points(message)
            else:
                give_message_points(message)

            res = [
                (message.channel.id, x[0])
                for x in re.findall(URL_REGEX, message.content)
            ]

            if res:
                batch_insert_links(res)

            if isinstance(message.author, discord.Member):
                await client.update_rank(message.author)

    await client.process_commands(message)


@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, MissingRequiredArgument):
        embed = create_embed(
            "You have an error in your command, you can use `!help [command]` to check its syntax.",
            title="Error")
        await ctx.reply(
            embed=embed
        )
    elif isinstance(error, CommandNotFound) or isinstance(error, MissingRole):
        return
    else:
        embed = create_embed(
            "An error occurred while processing your command. This incident has been logged.",
            title="Error")
        await ctx.reply(
            embed=embed
        )


@client.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, NoPrivateMessage):
        await ctx.respond("This command can only be used in a server.", ephemeral=True)
    elif isinstance(error, PrivateMessageOnly):
        await ctx.respond("This command can only be used in a private message.", ephemeral=True)
    elif isinstance(error, MissingRole):
        await ctx.respond("You do not have the sufficient permissions to do this! :/", ephemeral=True)
    else:
        await ctx.respond("An error occurred, this incident has been reported.")


@client.event
async def on_error(event: str, _, __) -> None:
    """Event handler for error event."""
    embed = discord.Embed(title=":x: Event Error", color=constants.ERROR_COLOR)
    embed.add_field(name="Event", value=event)
    ty, val, tb = sys.exc_info()
    if ty is not None and val is not None and tb is not None:
        embed.description = "```py\n{0}\n```".format(
            "".join(traceback.format_exception(ty, val, tb))
        )
        logging.error(traceback.format_exception(ty, val, tb))
        embed.timestamp = datetime.datetime.utcnow()
        await client.update_channel.send(embed=embed)
