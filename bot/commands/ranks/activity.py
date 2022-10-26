import datetime

import discord
from discord.ext import commands

from bot import client, logging, rank_constants
from bot.constants import *
from bot.database.points import *
from bot.rank_constants import *


# @client.register("!rank", (0, 0))
@client.slash_command(
    name="rank",
    description="Displays how many points you have in ths server."
)
async def server_rank(ctx: discord.ApplicationContext):
    """!rank
    Displays how many points you have in ths server."""

    top_points = get_highest_points()
    if top_points is None:
        await ctx.respond("No data... just for now!")
        return

    uid = ctx.author.id
    embed = discord.Embed(
        title="Server Rank",
        description="Points can be earned through participation in the server, like sending messages or solving CTF "
        "challenges.",
        color=EMBED_COLOR,
    )

    pts = get_points_by_discord(uid)
    embed.add_field(name="Point Total", value=str(pts))
    for i, rank, cutoff in zip(
        range(RANK_COUNT),
        rank_constants.RANK_NAMES,
        generate_ranks(top_points, RANK_COUNT),
    ):
        embed.add_field(name=rank, value=f"Rank #{i} @ {cutoff} points.")

    # TODO: When roles and stuff are added, make sure to update this as well. #

    await ctx.respond(embed=embed)


# @client.register("!stats", (0, 0))
@client.command(
    name="stats",
    brief="Displays your CTF solve statistics.",
    description="Displays your CTF solve statistics.",
    extras={"tags": ["fun"]},
)
async def server_stats(ctx: commands.Context):
    """!stats
    Displays your CTF solve statistics."""

    uid = ctx.author.id
    embed = discord.Embed(
        title="CTF Stats",
        description="The number under each category is how many solves you've contributed to.",
        color=EMBED_COLOR,
    )

    for category in CTF_CHAL_CATEGORIES:
        embed.add_field(
            name=category,
            value=str(get_transaction_count_by_uid_and_type(uid, SOLVE_TYPE(category))),
        )

    # TODO: Add an embedded image with a horizontal stacked bar graph that allows users to visualize the percentages. #

    await ctx.channel.send(embed=embed)


@client.command(
    name="leaderboard",
    brief="Displays the top 10 highest-point members in the server.",
    description="Displays the top 10 highest-point members in the server.",
    extras={"tags": ["fun"]},
)
async def leaderboard(ctx: commands.Context):
    """!leaderboard
    Displays the top 10 highest-point members in the server."""

    embed = discord.Embed(
        title="b01lers Leaderboard",
        description="Here is the current leaderboard on the server",
        color=EMBED_COLOR,
    )

    mentions = []
    ranks = []
    points = []

    top = get_top_scorers(10)

    if len(top) == 0:
        await ctx.reply("There is currently no data on the server!")
        return

    position = 1
    for member in top:
        try:
            discord_user = await client.get_member(member.uid)
            if discord_user is None:
                raise Exception()
        except:
            logging.warning("An error occurred while getting member from database.")
            continue

        # Leaderboard name string
        # Mention will not actually mention here in embed
        if position == 1:
            mentions.append(f"🥇{discord_user.mention}")
        elif position == 2:
            mentions.append(f"🥈{discord_user.mention}")
        elif position == 3:
            mentions.append(f"🥉{discord_user.mention}")
        else:
            mentions.append(f"{position}. {discord_user.mention}")

        # Points string
        points.append(f"{member.points} points")
        position += 1

    embed.set_thumbnail(
        url="https://pbs.twimg.com/profile_images/568451513295441921/9Hm60msK_400x400.png"
    )

    embed.add_field(name="Users", value="\n".join(mentions), inline=True)
    embed.add_field(name="Points", value="\n".join(points), inline=True)

    embed.set_footer(text="Last updated on")
    embed.timestamp = datetime.datetime.now()

    await ctx.channel.send(embed=embed)


# @client.register("!givepoints", (2, 2), {"dm": False, "officer": True})
@commands.guild_only()
@commands.has_role("officer")
@client.command(
    name="givepoints",
    brief="Gives participation points to the specified user.",
    description="Gives participation points to the specified user.",
    extras={"tags": ["fun", "officer"]},
)
async def give_points(ctx: commands.Context, member: discord.Member, points: int):
    """!givepoints <@user> <points>
    Gives participation points to the specified user."""

    add_transaction(member.id, MANUAL_POINTS_TYPE(ctx.author.id), points)
    add_points_to_user(uid=member.id, points=points)
    logging.info(
        "Officer {0} gave {1} points to user {2} ({3})".format(
            ctx.author.name, points, member, member.id
        )
    )
    await ctx.message.add_reaction(DONE_EMOJI)
