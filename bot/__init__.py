import asyncio
import datetime
import logging
import random
import re
import shlex
import sys
import traceback
from logging.handlers import RotatingFileHandler

import discord
from discord.ext import tasks

from bot import database, participation, ranks, utils
from bot.constants import *


class Command:
    class CommandException(Exception):
        pass

    """
    Activation options:

    officer:    Can only be used by officer role holders
    dm:         Can be activated by DMing the bot
    channel:    Can be activated by sending the command in any channel
    """
    DEFAULT_OPTIONS = {"officer": False, "dm": True, "channel": True}

    def __init__(self, func, cmd, nargs, options, syntax, description):
        self.func = func
        self.cmd = cmd
        self.nargs = nargs
        self.options = {**Command.DEFAULT_OPTIONS, **options}
        self.syntax = syntax
        self.description = description

    async def execute(self, message, *args):
        if self.nargs[0] <= len(args) <= self.nargs[1]:
            await self.func(message, *args)
            return
        raise Command.CommandException(
            "`{0}`: {1} argument(s) expected, got {2}".format(
                self.cmd,
                self.nargs[0]
                if self.nargs[0] == self.nargs[1]
                else " to ".join(map(str, self.nargs)),
                len(args),
            )
        )


class B01lersBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = {}

    def register(self, cmd, nargs, options={}):
        def make_command(func):
            if cmd in self.commands:
                logging.info(
                    "Command {0}:{1} has been overridden by {2}.".format(
                        cmd, self.commands[cmd].__name__, func.__name__
                    )
                )
            s = func.__doc__.split("\n")
            self.commands[cmd] = Command(
                func=func,
                cmd=cmd,
                options=options,
                nargs=nargs,
                syntax=s[0],
                description=s[1:],
            )
            return func

        return make_command

    async def get_member(self, uid):
        return self.guild.get_member(
            uid
        )  # no longer necessarily async because of intents, other code awaits this though #

    async def get_text_channels(self):
        return self.guild.text_channels

    async def is_officer_message(self, message):
        officer_role = discord.utils.get(self.guild.roles, name="officer")
        user = await self.get_member(message.author.id)
        if officer_role in user.roles:
            return True
        return False

    async def is_officer_id(self, userid):
        officer_role = discord.utils.get(self.guild.roles, name="officer")
        user = await self.get_member(userid)
        if officer_role in user.roles:
            return True
        return False

    ### event listeners ###

    async def on_ready(self):
        self.update_channel = client.get_channel(UPDATE_CHANNEL)
        self.general_channel = client.get_channel(GENERAL_CHANNEL)
        self.approval_channel = client.get_channel(APPROVAL_CHANNEL)
        self.guild = client.get_guild(GUILD)
        self.ctfs = client.get_channel(LIVE_CTF_CATEGORY)
        self.archive = client.get_channel(ARCHIVE_CATEGORY)
        self.me = await self.guild.fetch_member(self.user.id)

        self.give_voice_points.start()
        await self.ensure_ranks()

        logging.info("Bot is ready!")

    async def ensure_ranks(self):
        for rank, color in zip(ranks.RANK_NAMES, ranks.RANK_COLORS):
            role = discord.utils.get(self.guild.roles, name=rank)
            if role is None:
                await self.guild.create_role(
                    name=rank,
                    hoist=True,
                    mentionable=True,
                    color=discord.Colour(color),
                )
        self.ranks = (
            *zip(
                ranks.generate_ranks(database.get_highest_points()[0], ranks.RANK_COUNT),
                ranks.RANK_NAMES,
            ),
        )

    async def on_member_join(self, member):
        await member.send(
            "Welcome to b01lers! To verify yourself as a Purdue University student, just type `!verify <your-@purdue.edu-email-address-here>`"
        )

    async def on_member_update(self, before, after):
        pass

    async def on_member_remove(self, member):
        await self.update_channel.send(
            embed=utils.create_embed(
                "{0} has left the server. {1}".format(
                    member.display_name,
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
                    )[random.randint(0, 10)],
                )
            )
        )

    async def on_error(self, event, *args, **kwargs):
        embed = discord.Embed(title=":x: Event Error", color=ERROR_COLOR)
        embed.add_field(name="Event", value=event)
        ty, val, tb = sys.exc_info()
        if ty is not None and val is not None and tb is not None:
            embed.description = "```py\n{0}\n```".format(
                "".join(traceback.format_exception(ty, val, tb))
            )
            logging.error(traceback.format_exception(ty, val, tb))
            embed.timestamp = datetime.datetime.utcnow()
            await self.update_channel.send(embed=embed)

    async def on_message(self, message):
        if message.author.id != self.user.id:
            is_dm = isinstance(message.channel, discord.channel.DMChannel)
            is_channel = isinstance(message.channel, discord.channel.TextChannel)

            if message.content.startswith("!"):
                try:
                    argv = shlex.split(message.content)
                except:
                    await message.channel.send(
                        embed=utils.create_embed(
                            "Something went wrong when parsing your message. Please try again."
                        )
                    )
                    return

                is_officer = await self.is_officer_message(message)
                command = self.commands.get(argv[0])

                if (
                    command
                    and (not is_dm or command.options["dm"])
                    and (not is_channel or command.options["channel"])
                    and (not command.options["officer"] or is_officer)
                ):
                    try:
                        await command.execute(message, *argv[1:])
                    except Command.CommandException as err:
                        await self.commands["!help"].execute(message, command.cmd)
                        if str(err) != "":
                            await message.channel.send(
                                embed=utils.create_embed(str(err))
                            )
            else:
                if is_channel and message.channel.category_id == LIVE_CTF_CATEGORY:
                    participation.give_ctf_message_points(message)
                else:
                    participation.give_message_points(message)

                if is_channel:
                    links = [x[0] for x in re.findall(URL_REGEX, message.content)]
                    if links:
                        database.insert_links(message.channel.id, links)

                    await self.update_rank(message)

    async def update_rank(self, message):
        author = message.author
        previous_rank_index = -1

        for role in author.roles:
            if role.name in ranks.RANK_NAMES:
                previous_rank_index = ranks.RANK_NAMES.index(role.name)

        current_rank_index = ranks.get_rank(
            database.get_points(author.id), list(map(lambda r: r[0], self.ranks))
        )

        if current_rank_index > previous_rank_index:
            if previous_rank_index != -1:
                await author.remove_roles(
                    discord.utils.get(
                        self.guild.roles, name=ranks.RANK_NAMES[previous_rank_index]
                    )
                )
            await author.add_roles(
                discord.utils.get(
                    self.guild.roles, name=ranks.RANK_NAMES[current_rank_index]
                )
            )
            await self.general_channel.send(
                f"{message.author.name} has reached rank {ranks.RANK_NAMES[current_rank_index]}!"
            )

    async def on_raw_reaction_add(self, payload):
        cid = payload.channel_id
        mid = payload.message_id
        uid = payload.user_id
        emoji = payload.emoji.name

        try:
            cid = int(cid)
            mid = int(mid)
        except:
            await self.update_channel.send(
                embed=utils.create_embed(
                    f"Something happened when reacting to a message: could not parse {cid}:{mid}.",
                    error=True,
                )
            )
            return
        channel = self.get_channel(cid)
        if channel is None:
            await self.update_channel.send(
                embed=utils.create_embed(
                    f"Something happened when reacting to a message: could not find channel {cid}.",
                    error=True,
                )
            )
            return
        msg = await channel.fetch_message(mid)
        if msg is None:
            await self.update_channel.send(
                embed=utils.create_embed(
                    f"Something happened when reacting to a message: could not find message {cid}:{mid}.",
                    error=True,
                )
            )
            return

        if uid != self.user.id:
            is_officer = await self.is_officer_id(uid)
            if (
                cid == APPROVAL_CHANNEL
                and is_officer
                and msg.author.id == self.user.id
                and len(msg.embeds) == 1
                and msg.embeds[0].footer.text == "APPROVAL NEEDED"
            ):
                if emoji == DONE_EMOJI:
                    await self.commands["!accept"].func(msg)
                elif emoji == CANCEL_EMOJI:
                    await self.commands["!reject"].func(msg)
            elif emoji == "yeet" and uid != msg.author.id:
                participation.give_yeet_points(msg, uid)

    @tasks.loop(minutes=1)
    async def give_voice_points(self):
        # TODO: voice points vs. CTF voice points
        for channel in self.guild.voice_channels:
            for member in channel.members:
                participation.give_voice_points(member)


logging.basicConfig(filename="data/bot.log", level=logging.INFO)
log = logging.getLogger()
handler = RotatingFileHandler("data/bot.log", maxBytes=52428800, backupCount=3)
log.addHandler(handler)

intents = discord.Intents.default()
intents.members = True
client = B01lersBotClient(intents=intents)
