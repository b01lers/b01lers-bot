import datetime
import os
from typing import Union

import discord
import email_validator
from discord import TextChannel, Option, ChannelType
from discord.ext import commands

from bot import client, logging, database
from bot.constants import *
from bot.database.bootcamp import (
    get_team_by_email,
    add_team,
    update_ctf_team_entry,
    get_team_by_leader_email,
)
from bot.database.members import get_member_by_discord
from bot.helpers import decorators
from bot.helpers.chat_log_helper import archive_and_gzip_chat_log
from bot.utils.messages import create_embed, get_epoch_timestamp

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


bootcamp_commands_group = client.create_group("bootcamp", "Bootcamp related commands")


# @client.register("!ctfregister", (1, 4), {"channel": False})
@commands.dm_only()
@bootcamp_commands_group.command(
    name="register",
    description="Registers a team for the b00tcamp CTF with you and up to three more teammates."
)
async def ctf_register(
        ctx: discord.ApplicationContext,
        leader_email: Option(str, "Team leader email"),
        tm1: Option(str, "Teammate 1 email", required=False),
        tm2: Option(str, "Teammate 2 email", required=False),
        tm3: Option(str, "Teammate 3 email", required=False),
):
    """
    !ctfregister <youremail@purdue.edu> [teammate1@purdue.edu] [teammate2@purdue.edu] [teammate3@purdue.edu]
    """

    # TODO: Optimize this.
    everyone = list(filter(lambda tm: tm != "", [leader_email, tm1, tm2, tm3]))
    seen = set()
    uniq = [tm for tm in everyone if tm not in seen and not seen.add(tm)]
    if len(uniq) != len(everyone):
        await ctx.respond(
            "You have duplicates in your command, please check before proceeding.", ephemeral=True
        )
        return

    # Validate email
    for email in everyone:
        try:
            valid = email_validator.validate_email(email)
            if valid.domain != "purdue.edu":
                await ctx.respond(f"{email} is not a @purdue.edu email.", ephemeral=True)
                return
        except email_validator.EmailNotValidError:
            await ctx.respond(f"{email} is not a valid email.", ephemeral=True)
            return

    # Validate leader user's verification status
    leader_discord_member = database.members.get_member_by_discord(ctx.author.id)
    if leader_discord_member is None:
        await ctx.respond(
            "You haven't registered with me yet! Use `!verify <your-email@purdue.edu>` to verify yourself.",
            ephemeral=True
        )
        return

    if leader_discord_member.email != leader_email:
        await ctx.respond(
            f"Your provided email does not match the record for your username. Try using {leader_discord_member.email} instead.",
            ephemeral=True
        )
        return

    # Check if their teammates are already registered
    for teammate in everyone[1:]:
        test_entry = get_team_by_email(teammate)
        if test_entry and test_entry.register_email != leader_email:
            await ctx.respond(
                f"The teammate you specified ({teammate}) has already registered for a team!",
                ephemeral=True
            )
            return

    # Check if the leader is a player of a team
    # TODO: Implement a leave team feature
    entry = get_team_by_leader_email(leader_email)
    if entry and entry.register_email != leader_email:
        await ctx.respond(
            "You have already joined a team! Please remove yourself first from that team first before proceeding.",
            ephemeral=True
        )
        return

    # Actual logic
    # Scenario 1. If the leader and their teammates is first time playing
    if not entry:
        add_team(leader_email, tm1, tm2, tm3)
        # 1.1 Solo
        if len(everyone) == 1:
            await ctx.respond(
                "Looks like you're playing by yourself! That's perfectly fine, we're sure you'll get a lot out of it. If you change your mind, you can run this command again with any teammates.",
                ephemeral=True
            )
        else:
            await ctx.respond("You're all signed up. :)", ephemeral=True)
        return

    # Scenario 2. If the leader has already registered and wanted to update
    update_ctf_team_entry(entry, leader_email, tm1, tm2, tm3)

    await ctx.respond(
        "You are already registered as a team leader. I am updating this registration to be just you. If this is an error, just run it again with the right people.",
        ephemeral=True
    )


@commands.dm_only()
@bootcamp_commands_group.command(
    name="unregister",
    description="Unregisters yourself from the b00tcamp CTF."
)
async def unregister(ctx: discord.ApplicationContext):
    # Check if member exists
    member = get_member_by_discord(ctx.author.id)
    if not member or member.validated != 1:
        await ctx.respond(
            "It seems that you haven't verified yourself yet, so you should be safe from entering a team.",
            ephemeral=True
        )
        return

    entry = get_team_by_email(member.email)
    if not entry:
        await ctx.respond(
            "You haven't registered for the b00tcamp ctf yet, but you can still participate via `!ctfregister` :)",
            ephemeral=True
        )
        return

    # TODO: Implement team disband feature
    if entry.register_email == member.email:
        await ctx.respond("", view="aa", ephemeral=True)
    else:
        await ctx.respond("", ephemeral=True)


@commands.dm_only()
@bootcamp_commands_group.command(
    name="survey",
    description="Take a survey about our bootcamp ctf."
)
async def survey(ctx: discord.ApplicationContext):
    class SurveyModal(discord.ui.Modal):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.add_item(
                discord.ui.InputText(
                    label="What do you think of this bootcamp?",
                    style=discord.InputTextStyle.long
                )
            )
            self.add_item(
                discord.ui.InputText(
                    label="Any suggestions for future bootcamps?",
                    style=discord.InputTextStyle.long
                )
            )

        async def callback(self, interaction: discord.Interaction):
            embed = discord.Embed(title="New Survey Feedback")
            embed.add_field(name="Feedback", value=self.children[0].value)
            embed.add_field(name="Future suggestions", value=self.children[1].value)
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.timestamp = datetime.datetime.now()
            await client.update_channel.send(embeds=[embed])
            await interaction.response.send_message(
                "Thank you for taking the survey! Your submission has been recorded."
            )

    # TODO: Do necessary checks here
    await ctx.send_modal(SurveyModal(title="Bootcamp CTF Survey"))


# @client.register("!registrations", (0, 0), {"channel": False, "officer": True})
@decorators.officer_only()
@commands.dm_only()
@bootcamp_commands_group.command(
    name="list",
    description="List all teams that registered for b00tcamp CTF."
)
async def show_registrations(ctx: discord.ApplicationContext):
    """Prints a list of registered b00tcamp CTF teams."""

    records = database.bootcamp.get_all_teams()

    embed = discord.Embed(
        title="Teams registered for the Bootcamp",
        description="Here is the full list of teams that registered for the Bootcamp.",
        colour=0x66CCFF,
    )

    # Discord Embed has variable width...
    embed.add_field(
        name="Team", value="\n".join(map(lambda r: str(r.id), records)), inline=True
    )
    embed.add_field(
        name="Leader",
        value="\n".join(map(lambda r: r.register_email, records)),
        inline=True,
    )
    embed.add_field(
        name="Teammate 1",
        value="\n".join(map(lambda r: r.teammate_one or "None", records)),
        inline=True,
    )
    embed.add_field(
        name="Teammate 2",
        value="\n".join(map(lambda r: r.teammate_two or "None", records)),
        inline=True,
    )
    embed.add_field(
        name="Teammate 3",
        value="\n".join(map(lambda r: r.teammate_three or "None", records)),
        inline=True,
    )

    await ctx.respond(embed=embed, ephemeral=True)
