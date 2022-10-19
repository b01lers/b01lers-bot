import logging
from typing import Optional, Union

import discord
from discord import Guild, Member, TextChannel
from discord.ext.commands import Bot

from bot import rank_constants, utils
from bot.database.points import get_points_by_discord, get_highest_points
from bot.utils.messages import create_embed

# The bot requires members and message intent.
intents = discord.Intents.all()
intents.members = True


# Actual class of our bot
class B01lersBot(Bot):
    update_channel: TextChannel = None
    general_channel: TextChannel = None
    approval_channel: TextChannel = None
    guild: Guild = None
    ctfs = None
    archive = None
    me: Member = None
    ranks = None

    async def get_member(self, uid: Union[int, str]) -> Optional[Member]:
        """Get a member from guild."""
        return self.guild.get_member(int(uid))

    async def get_text_channels(self) -> list[TextChannel]:
        """Get all text channels."""
        return self.guild.text_channels

    async def is_officer(self, userid: int) -> bool:
        """Check if specified user with user id is an officer."""
        officer_role = discord.utils.get(self.guild.roles, name="officer")
        user = await self.get_member(userid)
        if not user:
            return False
        return officer_role in user.roles

    async def is_officer_message(self, message) -> bool:
        """Check if specified message is from an officer."""
        return await self.is_officer(message.author.id)

    async def update_rank(self, member, bot_channel=False):
        if self.ranks is None:
            return

        author = member
        previous_rank_index = -1

        for role in author.roles:
            if role.name in rank_constants.RANK_NAMES:
                previous_rank_index = rank_constants.RANK_NAMES.index(role.name)

        current_rank_index = rank_constants.get_rank(
            get_points_by_discord(author.id), list(map(lambda r: r[0], self.ranks))
        )

        if current_rank_index > previous_rank_index:
            if previous_rank_index != -1:
                prev_roles = discord.utils.get(
                    self.guild.roles,
                    name=rank_constants.RANK_NAMES[previous_rank_index],
                )
                if prev_roles is not None:
                    await author.remove_roles(prev_roles)
            current_rank_role = discord.utils.get(
                self.guild.roles, name=rank_constants.RANK_NAMES[current_rank_index]
            )
            if current_rank_role is not None:
                await author.add_roles(current_rank_role)
            if not bot_channel and not current_rank_index == 0:
                await self.general_channel.send(
                    embed=create_embed(
                        f"{author.name} has reached rank {rank_constants.RANK_NAMES[current_rank_index]}!"
                    )
                )
            else:
                await self.update_channel.send(
                    embed=create_embed(
                        f"{author.name} has reached rank {rank_constants.RANK_NAMES[current_rank_index]}!"
                    )
                )

            await author.send(
                f"You have reached rank {rank_constants.RANK_NAMES[current_rank_index]} in b01lers! Remember, you can earn points by chatting, solving ctf challenges and claiming points with the `!solve` command, and more!"
            )

    async def update_ranks(self):
        for member in self.guild.members:
            try:
                await self.update_rank(member, bot_channel=True)
            except discord.errors.Forbidden as e:
                logging.error(e)

    async def ensure_roles(self):
        pass

    async def ensure_ranks(self):
        for rank, color in zip(rank_constants.RANK_NAMES, rank_constants.RANK_COLORS):
            role = discord.utils.get(self.guild.roles, name=rank)
            if role is None:
                await self.guild.create_role(
                    name=rank,
                    hoist=True,
                    mentionable=True,
                    color=discord.Colour(color),
                )

        top_points = get_highest_points()

        self.ranks = (
            *zip(
                rank_constants.generate_ranks(top_points, rank_constants.RANK_COUNT),
                rank_constants.RANK_NAMES,
            ),
        )


# Bootstrap
client = B01lersBot(
    description="B01lers Bot",
    command_prefix="!",
    pm_help=False,
    intents=intents,
    help_command=None,
)
