import discord
import json

from bot import client, logging
from bot import utils, database, participation
from bot.constants import *


@client.register("!solve", (3, 7), {"dm": False})
async def submit_solve(message, *args):
    """!solve "<chal name>" <category> "<flag>" [@teammate 1]... [@teammate 4]
    Submits a solved challenge with up to 4 collaborators.
    `<category>` should be one of `re`, `pwn`, `web`, `crypto`, `other`.
    Gives 100 participation points to each collaborator upon officer approval."""

    if message.channel.category_id != LIVE_CTF_CATEGORY:
        await message.channel.send(
            embed=utils.create_embed("Please submit your solve in a live CTF channel.")
        )
        return

    chal, category, flag, *teammates = args
    chal = chal.lower()
    category = category.lower()
    try:
        teammate_ids = tuple(int(utils.parse_uid(t)) for t in teammates) + (
            message.author.id,
        )
    except:
        await message.channel.send(
            embed=utils.create_embed(
                "Make sure you have mentioned everybody correctly!"
            )
        )
        return
    teammates = []
    for t in teammate_ids:
        user = await client.get_member(t)
        if user is not None and t not in teammates:
            teammates.append(t)
        else:
            await message.channel.send(
                embed=utils.create_embed(
                    "Make sure you have mentioned everybody correctly!"
                )
            )
            return

    data = {
        "chal": chal,
        "category": category,
        "flag": flag,
        "teammates": teammates,
        "cid": message.channel.id,
        "mid": message.id,
    }

    if category not in CTF_CHAL_CATEGORIES:
        await message.channel.send(
            embed=utils.create_embed(
                f"Make sure `<category>` is one of {', '.join(map(lambda x: f'`{x}`', CTF_CHAL_CATEGORIES))}!"
            )
        )
        return

    aid = database.add_new_approval("solve", json.dumps(data))
    msg = await client.approval_channel.send(
        embed=utils.create_embed(
            f"""A new solve for {chal} in {message.channel.mention} is pending approval!
        Use `!review {aid}` to see the details of this solve, or click [here](https://discordapp.com/channels/{GUILD}/{data['cid']}/{data['mid']}) for the message.

        React with {DONE_EMOJI} to acccept this solve, or {CANCEL_EMOJI} to reject.""",
            title=f"{aid}",
        ).set_footer(text="APPROVAL NEEDED")
    )  # DO NOT CHANGE THIS LINE! THIS IS WHAT THE BOT LOOKS FOR WHEN THE MESSAGE IS REACTED TO. #
    database.update_approve_message(aid, msg.id)
    await msg.add_reaction(DONE_EMOJI)
    await msg.add_reaction(CANCEL_EMOJI)
    await message.add_reaction(WAITING_EMOJI)

    for teammate in teammates:
        teammate_user = await client.get_member(teammate)
        await teammate_user.send(
            embed=utils.create_embed(
                f"Your solve for {chal} has been recorded with request ID {aid}."
            )
        )

    logging.info(f"Solve {aid} solve awaiting approval.")

    return


@client.register("!review", (1, 1), {"dm": False, "officer": True})
async def review(message, *args):
    """!review <request id>
    Displays data about a solve or writeup request."""

    (aid,) = args

    approval = database.get_approval(aid)
    embed = discord.Embed(title=f"Request #{aid}", color=EMBED_COLOR)
    if approval == None:
        embed.description = "Request not found."
        await message.channel.send(embed=embed)
        return

    embed.add_field(
        name="type",
        value=database.column_name_index("type", APPROVALS_COLUMNS, approval),
    )

    data = json.loads(
        database.column_name_index("description", APPROVALS_COLUMNS, approval)
    )

    for k in data:
        if k == "teammates":
            user = await client.get_member(t)
            embed.add_field(name=str(k), value=", ".join(user.mention for t in data[k]))
        elif k == "cid":
            embed.add_field(name="ctf", value=client.get_channel(data[k]).mention)
        elif k == "mid":
            embed.add_field(
                name="message",
                value=f"[link](https://discordapp.com/channels/{GUILD}/{data['cid']}/{data['mid']})",
            )
        else:
            embed.add_field(name=str(k), value="`" + str(data[k]) + "`")

    embed.add_field(
        name="status",
        value=(WAITING_EMOJI, DONE_EMOJI, CANCEL_EMOJI)[
            database.column_name_index("approved", APPROVALS_COLUMNS, approval)
        ]
        + " **"
        + APPROVAL_VALUES[
            database.column_name_index("approved", APPROVALS_COLUMNS, approval)
        ]
        + "**",
    )  # the "approved" column

    await message.channel.send(embed=embed)

    return


# @client.register("!edit", (3, 3), {"dm": False, "officer": True})
# TODO: This should edit an approval request.
async def edit_request(message, *args):
    """!edit <request id> <field> <new value>
    Edits the description of a request.
    Note that this cannot change whether a solve has been approved or not; a new request must be submitted."""

    aid, field, value = args
    return


async def handle_approval(
    message, approved, referrer=None
):  # the referrer is if the !accept or !reject command is used; message should be the one sent in APPROVAL_CHANNEL
    embed = message.embeds[0]
    try:
        aid = int(embed.title)
    except:
        await client.update_channel.send(
            embed=utils.create_embed(
                f"Something bad happened when trying to parse approval request {embed.title}.",
                error=True,
            )
        )
        return

    approval = database.get_approval(aid)
    if approval is None:
        await message.channel.send(
            embed=utils.create_embed(f"No request with ID {aid} was found.")
        )
        return

    request_type = database.column_name_index("type", APPROVALS_COLUMNS, approval)
    data = json.loads(
        database.column_name_index("description", APPROVALS_COLUMNS, approval)
    )
    try:
        original = await client.get_channel(data["cid"]).fetch_message(data["mid"])
    except:
        original = None

    if database.column_name_index("approved", APPROVALS_COLUMNS, approval) == 0:
        if approved:
            if request_type == "solve":
                chaldata = json.dumps(
                    {"chal": data["chal"], "flag": data["flag"], "ctf": data["cid"]}
                )
                for teammate in data["teammates"]:
                    participation.give_solve_points(
                        teammate, data["category"], chaldata
                    )
                    try:
                        teammate_user = await client.get_member(teammate)
                        await teammate_user.send(
                            embed=utils.create_embed(
                                f"Congratulations! You have been awarded {POINTS_PER_SOLVE} points for solving {data['chal']}!"
                            )
                        )
                    except:
                        await client.update_channel.send(
                            embed=utils.create_embed(
                                f"Failed to send message to user {teammate}.",
                                error=True,
                            )
                        )
            elif request_type == "writeup":
                # TODO: writeup request handling #
                pass

            if original is not None:
                await original.remove_reaction(WAITING_EMOJI, client.user)
                await original.add_reaction(DONE_EMOJI)

            database.accept_request(aid)

            logging.info(f"Accepted {request_type} request {aid}.")
        else:
            for teammate in data["teammates"]:
                try:
                    teammate_user = await client.get_member(teammate)
                    await teammate_user.send(
                        embed=utils.create_embed(
                            f"Your {request_type} for {data['chal']} has been rejected."
                        )
                    )
                except:
                    await client.update_channel.send(
                        embed=utils.create_embed(
                            f"Failed to send message to user {teammate}.", error=True
                        )
                    )

            if original is not None:
                await original.remove_reaction(WAITING_EMOJI, client.user)
                await original.add_reaction(CANCEL_EMOJI)

            database.reject_request(aid)

            logging.info(f"Rejected {request_type} request {aid}.")

        if referrer is not None:
            await referrer.add_reaction(DONE_EMOJI)
    else:
        if referrer is not None:
            await referrer.add_reaction(CANCEL_EMOJI)

    await message.delete()
    return


@client.register("!accept", (1, 1), {"dm": False, "officer": True})
async def accept(message, *args):
    """!accept <request id>
    Manually accepts a solve or writeup submission."""

    if len(args) == 0:  # bot message reaction
        await handle_approval(message, True)
    else:
        approval = database.get_approval(args[0])
        approve_message = await client.approval_channel.fetch_message(
            database.column_name_index("approve_message", APPROVALS_COLUMNS, approval)
        )
        await handle_approval(approve_message, True, message)

    return


@client.register("!reject", (1, 1), {"dm": False, "officer": True})
async def reject(message, *args):
    """!reject <request id>
    Manually rejects a solve or writeup submission."""

    if len(args) == 0:  # bot message reaction
        await handle_approval(message, False)
    else:
        approval = database.get_approval(args[0])
        approve_message = await client.approval_channel.fetch_message(
            database.column_name_index("approve_message", APPROVALS_COLUMNS, approval)
        )
        await handle_approval(approve_message, False, message)

    return
