import os
from typing import Union

import discord
from discord import TextChannel, Option, ChannelType
from discord.ext import commands

from bot import client, logging
from bot.constants import *
from bot.helpers.chat_log_helper import archive_and_gzip_chat_log
from bot.utils.messages import create_embed

MemberOrRole = Union[discord.Member, discord.Role]


# @client.register("!competition", (4, 4), {"officer": True})
@discord.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="competition",
    description="Creates a competition channel."
)
async def make_competition(
    ctx: discord.ApplicationContext,
    title: Option(str, "Competition title"),
    description: Option(str, "Competition description"),
    username: Option(str, "Competition login username"),
    password: Option(str, "Competition login password")
):
    """!competition "<channel name>" "<description>" "<username>" "<password>"
    Creates a competition channel."""

    # Cehck if CTF category exists
    ctf_category = client.ctfs
    if ctf_category not in client.guild.categories:
        message = "Unable to find live CTF category."
        await ctx.respond(embed=create_embed("The `live ctfs` category cannot be found."), ephemeral=True)
        logging.error(message)
        return

    # Check if the channel with same name exists
    check_channel = discord.utils.get(
        ctf_category.channels, name=title.replace(" ", "-").lower()
    )
    if check_channel:
        await ctx.respond(
            f"The channel for **{title}** already exists: {check_channel.mention}.", ephemeral=True
        )
        return

    # Actual creation logic
    channel = await ctf_category.create_text_channel(
        title,
        position=0,
        topic=f"Channel for {title}, please check pinned message for shared credentials. (for officers: type !archive "
              f"to archive)",
    )

    embed = discord.Embed(
        title=title + " credentials", description=description, color=EMBED_COLOR
    )
    for k, v in zip(("Username", "Password"), (f"`{username}`", f"`{password}`")):
        embed.add_field(name=k, value=v, inline=False)

    pinned_message = await channel.send(embed=embed)
    await pinned_message.pin()
    await ctx.respond(
        f"You just created a channel for **{title}**, discuss it with your friends in {channel.mention}!"
    )


@discord.guild_only()
@client.slash_command(
    name="challenge",
    description="Creates a challenge thread in a live CTF channel."
)
async def create_challenge_thread(ctx: discord.ApplicationContext, challenge: Option(str, "Challenge name")):
    # Check if the message is sent in a live ctf channel
    if ctx.channel.category_id != client.ctfs.id:
        await ctx.respond(
            embed=create_embed(
                "This command can only be used in a `live ctfs` channel."
            ),
            ephemeral=True
        )
        return

    if (
            ctx.channel.type == discord.ChannelType.public_thread
            or ctx.channel.type == discord.ChannelType.private_thread
    ):
        await ctx.respond("You cannot create a thread inside a thread!", ephemeral=True)
        return

    # FIXME: Allow long name
    challenge = challenge.replace(" ", "-").lower()
    thread = discord.utils.get(ctx.channel.threads, name=challenge)
    if thread:
        await ctx.respond(f"This thread already exists, please check {thread.mention}.", ephemeral=True)
        return

    try:
        # Create a thread and archive it after 3 days (4320 minutes)
        thread = await ctx.channel.create_thread(
            name=challenge, auto_archive_duration=4320, type=ChannelType.public_thread
        )
        await ctx.respond(
            f"I have created a challenge thread for {thread.mention} as per {ctx.author.mention}'s request."
        )
    except Exception as e:
        await ctx.respond("Unable to start a thread.", ephemeral=True)
        logging.error("Unable to make a thread", e)


async def archive_and_lock_channel(channel: TextChannel):
    if (
            channel.type == discord.ChannelType.public_thread
            or channel.type == discord.ChannelType.private_thread
    ):
        # Lock thread
        await channel.edit(archived=True, locked=True)
    else:
        # Archive the channel and its threads
        # Threads
        for thread in channel.threads:
            await thread.edit(archived=True, locked=True)
        # Channel
        await channel.set_permissions(client.guild.default_role, send_messages=False)
        await channel.set_permissions(client.guild.default_role, read_messages=False)
        await channel.edit(category=client.archive)
        await channel.edit(position=0)


# @client.register("!archive", (0, 0), {"dm": False, "officer": True})
@commands.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="archive",
    description="Archives the current competition channel/thread as well as its challenge threads, if it has any."
)
async def archive_competition(ctx: discord.ApplicationContext):
    """!archive
    Archives the current competition channel from the Live CTFs category, as well as challenge channels if they exist.
    If used in a challenge-specific channel, deletes the channel and sends a log of the chat to the main competition channel."""

    # FIXME: Fix it for thread
    # Check if it's a live CTF channel
    if ctx.channel.category_id != client.ctfs.id:
        await ctx.respond("You cannot archive a non live CTF channel!", ephemeral=True)
        return

    # If this is a thread, archive it
    if (
            ctx.channel.type == discord.ChannelType.public_thread
            or ctx.channel.type == discord.ChannelType.private_thread
    ):
        description = "thread for challenge"
    else:
        description = "discussion channel for CTF"

    file = await archive_and_gzip_chat_log(ctx)
    # I don't know why the hell this won't work here but I'll leave it for now.
    # Probably due to async environment?
    # logging.debug("Created archive file at", file.name.lower())
    await ctx.respond(
        f"This {description} {ctx.channel.name} is now archived as per {ctx.author.mention}'s request, and its chat log is attached below:",
        file=discord.File(file.name),
    )
    # Do it after chat log otherwise bot will not be able to archive threads due to their invisibility.
    await archive_and_lock_channel(ctx.channel)

    logging.debug(file.name)
    # Clean up
    file.close()
    os.remove(file.name)


# @client.register("!invite", (1, 4), {"dm": False, "officer": True})
@discord.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="invite",
    description="Grant roles or users access to a CTF channel."
)
async def invite(ctx: discord.ApplicationContext, member_or_role: Option(MemberOrRole, "Member or role")):
    """!invite <member/role>
    Gives a role or user access to a CTF channel."""

    # NOTE: Discord limitation disallows for variable length arguments.

    if not ctx.channel.category.name.lower() == "live ctfs":
        await ctx.respond(
            embed=create_embed("Please use this command in a live CTF channel only!"),
            ephemeral=True
        )
        return

    try:
        await ctx.channel.set_permissions(
            member_or_role, read_messages=True, send_messages=True
        )
    except:
        await ctx.respond(
            embed=create_embed(f"Could not invite {member_or_role.mention} to channel."),
            ephemeral=True
        )
        return

    await ctx.respond(
        f"Have fun, {member_or_role.mention}!"
    )


# @client.register("!uninvite", (1, 4), {"dm": False, "officer": True})
@discord.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="uninvite",
    description="Revoke roles' or users' access from a CTF channel."
)
async def uninvite(ctx: discord.ApplicationContext, member_or_role: Option(MemberOrRole, "Member or role")):
    """!uninvite <@mention-1> [@mention-2] [@mention-3] [@mention-4] ...
    Removes roles' or users' access from a CTF channel."""

    if not ctx.channel.category.name.lower() == "live ctfs":
        await ctx.respond(
            embed=create_embed("Please use this command in a live ctfs channel only!"),
            ephemeral=True
        )
        return

    try:
        await ctx.channel.set_permissions(
            member_or_role, read_messages=False, send_messages=False
        )
    except:
        await ctx.respond(
            embed=create_embed(f"Could not remove {member_or_role.mention} from channel."),
            ephemeral=True
        )
        return

    await ctx.respond(f"Goodbye, {member_or_role.mention}. :pensive:")
