import json

import discord

from bot import client, database, logging, participation, utils
from bot.constants import *
from bot.ranks import *


@client.register("!rank", (0, 0))
async def server_rank(message, *args):
    """!rank
    Displays how many points you have in ths server."""

    uid = message.author.id
    embed = discord.Embed(
        title="Server Rank",
        description="Points can be earned through participation in the server, like sending messages or solving CTF challenges.",
        color=EMBED_COLOR,
    )

    pts = database.get_points(uid)
    embed.add_field(name="Point Total", value=str(pts))
    for i, rank, cutoff in zip(
        range(RANK_COUNT),
        RANK_NAMES,
        generate_ranks(database.get_highest_points()[0], RANK_COUNT),
    ):
        embed.add_field(name=rank, value=f"Rank #{i} @ {cutoff} points.")

    # TODO: When roles and stuff are added, make sure to update this as well. #

    await message.channel.send(embed=embed)

    return


@client.register("!stats", (0, 0))
async def server_stats(message, *args):
    """!stats
    Displays your CTF solve statistics."""

    uid = message.author.id
    embed = discord.Embed(
        title="CTF Stats",
        description="The number under each category is how many solves you've contributed to.",
        color=EMBED_COLOR,
    )

    for category in CTF_CHAL_CATEGORIES:
        embed.add_field(
            name=category,
            value=str(database.get_transaction_count(uid, SOLVE_TYPE(category))),
        )

    # TODO: Add an embedded image with a horizontal stacked bar graph that allows users to visualize the percentages. #

    await message.channel.send(embed=embed)

    return


@client.register("!leaderboard", (0, 0))
async def leaderboard(message, *args):
    """!leaderboard
    Displays the top 10 highest-point members in the server."""

    embed = discord.Embed(title="b01lers Leaderboard", color=EMBED_COLOR)

    leaderboard_string = ""
    top = database.get_top_scorers(20)

    position = 1
    for member in top:
        if position > 10:
            break

        try:
            user = await client.get_member(
                int(database.column_name_index("uid", POINTS_COLUMNS, member))
            )
        except:
            continue

        if user is not None:
            leaderboard_string += f"{position:>2}. "
            if user.nick is not None:
                leaderboard_string += f"{user.nick} ({str(user)})"
            else:
                leaderboard_string += f"{user.name} ({str(user)})"
            leaderboard_string += f" - {database.column_name_index('points', POINTS_COLUMNS, member)} points\n"
            position += 1

    embed.description = (
        "The top 10 point-holders in b01lers are:\n```\n" + leaderboard_string + "```"
    )
    await message.channel.send(embed=embed)

    return


@client.register("!givepoints", (2, 2), {"dm": False, "officer": True})
async def give_points(message, *args):
    """!givepoints <@user> <points>
    Gives participation points to the specified user."""

    uid, points = args
    try:
        uid = int(utils.parse_uid(uid))
    except:
        await message.channel.send(
            embed=utils.create_embed(
                "Make sure you have mentioned the user correctly! You can mention users not in this channel by typing `<!@USERID>`."
            )
        )
        return
    user = await client.get_member(uid)
    if user is None:
        await message.channel.send(
            embed=utils.create_embed(
                "Please make sure that the user you mentioned is in the server!"
            )
        )
        return
    try:
        points = int(points)
    except:
        await message.channel.send(
            embed=utils.create_embed("The amount of points needs to be an integer.")
        )
        return

    timestamp = utils.get_time()
    total = database.get_points(uid)
    database.log_point_transaction(
        uid, *MANUAL_POINTS_TYPE(message.author.id), "", points, timestamp
    )
    database.update_user_points(uid, total + points)
    logging.info(
        "Officer {0} gave {1} points to user {2}".format(
            message.author.name, points, uid
        )
    )
    await message.add_reaction(DONE_EMOJI)

    return
