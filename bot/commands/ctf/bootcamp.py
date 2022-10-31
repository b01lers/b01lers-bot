import asyncio
import time
from datetime import datetime, tzinfo, timezone
from typing import Union
from zoneinfo import ZoneInfo

import discord
import email_validator
from discord import Option, ScheduledEvent, TextChannel
from discord.ext import commands

from bot import client, database
from bot.database.bootcamp import (
    get_team_by_email,
    add_team,
    update_ctf_team_entry,
    get_team_by_leader_email, reset_teams,
)
from bot.database.members import get_member_by_discord
from bot.helpers import decorators
from bot.helpers.time import get_current_season

MemberOrRole = Union[discord.Member, discord.Role]

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
    if not client.is_bootcamp_running:
        await ctx.respond("The Bootcamp CTF is not currently running.", ephemeral=True)
        return

    member = await get_member_by_discord(ctx.author.id)
    if not member:
        await ctx.respond("You are not a member yet.", ephemeral=True)
        return

    if not await get_team_by_email(member.email):
        await ctx.respond("You are not registered for the bootcamp ctf.", ephemeral=True)
        return

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


@decorators.officer_only()
@bootcamp_commands_group.command(
    name="delete_records",
    description="Delete all records of bootcamp registration data. THIS ACTION IS IRREVERSIBLE!!!"
)
async def drop_table_and_run_away(ctx: discord.ApplicationContext,
                                  confirm: Option(str, "Type CONFIRM to continue")):
    if confirm != "CONFIRM":
        await ctx.respond("You have not confirmed the action, not doing anything then.", ephemeral=True)
        return

    reset_teams()
    await ctx.respond(f"All registration data have been dropped from the table as requested by {ctx.author.mention}.")


async def change_bootcamp_channel_visibility_and_bot_status(status: bool, channel: TextChannel):
    await channel.set_permissions(
        client.guild.default_role,
        send_messages=True
    )
    client.is_bootcamp_running = True


@decorators.officer_only()
@bootcamp_commands_group.command(
    name="start",
    description="Start the bootcamp CTF."
)
async def start_bootcamp(
        ctx: discord.ApplicationContext,
        start_time: Option(str, "Start date in YYYY-MM-DD hh:mm format (24h)"),
        end_time: Option(str, "End date in YYYY-MM-DD hh:mm format (24h)"),
        location: Option(str, "Location of the bootcamp", required=False),
        local_timezone: Option(str, "Timezone (e.g. Asia/Shanghai)", required=False)
):
    TIME_FORMAT = '%Y-%m-%d %H:%M'

    try:
        start_time = datetime.strptime(start_time, TIME_FORMAT).astimezone()
        end_time = datetime.strptime(end_time, TIME_FORMAT).astimezone()
    except:
        await ctx.respond("Unable to parse date, check if it's in YYYY-MM-DD format?", ephemeral=True)
        return

    if local_timezone:
        try:
            start_time = start_time.replace(tzinfo=ZoneInfo(local_timezone))
            end_time = end_time.replace(tzinfo=ZoneInfo(local_timezone))
        except:
            await ctx.respond("Unable to parse timezone, check if you made a typo?", ephemeral=True)
            return

    current_season = get_current_season()

    if client.ctfs not in client.guild.categories:
        await ctx.respond("Unable to find live CTF category.", ephemeral=True)
        return

    # Lock channel when we create it
    channel = await client.ctfs.create_text_channel(name=f"bootcamp-ctf-{current_season}-{start_time.year}")
    await channel.set_permissions(
        client.guild.default_role,
        send_messages=False
    )

    title = f"Bootcamp CTF - {current_season.title()} {start_time.year}"
    event: ScheduledEvent = await client.guild.create_scheduled_event(
        name=title,
        description=title,
        start_time=start_time,
        end_time=end_time,
        location=location or channel.mention,
        reason=f"Started {title} by {ctx.author.mention}."
    )

    # NOTE: These actions are volatile!
    # Unlock channel when bootcamp starts
    client.loop.call_later(start_time.timestamp() - datetime.now().astimezone().timestamp(),
                           asyncio.create_task,
                           change_bootcamp_channel_visibility_and_bot_status(True, channel))

    # Cleanup after bootcamp ends
    client.loop.call_later(end_time.timestamp() - datetime.now().astimezone().timestamp(),
                           asyncio.create_task,
                           change_bootcamp_channel_visibility_and_bot_status(False, channel))

    await ctx.respond(
        f"{title} is scheduled to start at {start_time} till {end_time} in {location} by {ctx.author.mention}!")
