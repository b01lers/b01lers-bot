import discord
from discord import Member
from discord.ext import commands

from bot import client, logging
from bot.helpers import participation
from bot.constants import *
from bot.database.approval import (
    create_approval_and_return_id,
    get_approval_by_id,
    update_approve_message,
    accept_request,
    reject_request,
)
from bot.utils.messages import create_embed


# @client.register("!solve", (3, 7), {"dm": False})
@commands.guild_only()
@client.command(
    name="solve",
    brief="Submit a flag to specific challenge.",
    description="Submits a solved challenge with up to 4 collaborators.",
    extras={"tags": ["ctf"]},
)
async def submit_solve(
    ctx: commands.Context,
    chal: str,
    category: str,
    flag: str,
    tm1: Member = None,
    tm2: Member = None,
    tm3: Member = None,
    tm4: Member = None,
):
    """!solve "<chal name>" <category> "<flag>" [@teammate 1]... [@teammate 4]
    Submits a solved challenge with up to 4 collaborators.
    `<category>` should be one of `re`, `pwn`, `web`, `crypto`, `other`.
    Gives 100 participation points to each collaborator upon officer approval."""

    if ctx.channel.category_id != LIVE_CTF_CATEGORY:
        await ctx.channel.send(
            embed=create_embed("Please submit your solve in a live CTF channel.")
        )
        return

    teammates = list(filter(lambda item: item is not None, [tm1, tm2, tm3, tm4]))
    chal = chal.lower()
    category = category.lower()

    teammates.insert(0, await client.get_member(ctx.message.id))

    data = {
        "chal": chal,
        "category": category,
        "flag": flag,
        "teammates": teammates,
        "cid": ctx.channel.id,
        "mid": ctx.message.id,
    }

    if category not in CTF_CHAL_CATEGORIES:
        await ctx.channel.send(
            embed=create_embed(
                f"Make sure `<category>` is one of {', '.join(map(lambda x: f'`{x}`', CTF_CHAL_CATEGORIES))}!"
            )
        )
        return

    aid = create_approval_and_return_id(json.dumps(data))
    msg = await client.approval_channel.send(
        embed=create_embed(
            f"""A new solve for {chal} in {ctx.channel.mention} is pending approval!
        Use `!review {aid}` to see the details of this solve, or click [here](https://discordapp.com/channels/{GUILD}/{data['cid']}/{data['mid']}) for the message.

        React with {DONE_EMOJI} to acccept this solve, or {CANCEL_EMOJI} to reject.""",
            title=f"{aid}",
        ).set_footer(text="APPROVAL NEEDED")
    )  # DO NOT CHANGE THIS LINE! THIS IS WHAT THE BOT LOOKS FOR WHEN THE MESSAGE IS REACTED TO. #
    update_approve_message(aid, msg.id)
    await msg.add_reaction(DONE_EMOJI)
    await msg.add_reaction(CANCEL_EMOJI)
    await ctx.message.add_reaction(WAITING_EMOJI)

    await ctx.reply(
        embed=create_embed(
            f"Your solve for {chal} has been recorded with request ID {aid}."
        )
    )

    logging.info(f"Solve {aid} solve awaiting approval.")


# @client.register("!review", (1, 1), {"dm": False, "officer": True})
@commands.guild_only()
@commands.has_role("officer")
@client.command(
    name="review",
    brief="Displays data about a solve or writeup request.",
    description="Displays data about a solve or writeup request.",
    extras={"tags": ["ctf", "officer"]},
)
async def review(ctx: commands.Context, aid: str):
    """!review <request id>
    Displays data about a solve or writeup request."""

    approval = get_approval_by_id(aid)
    if not approval:
        await ctx.reply("Request not found.")
        return

    embed = discord.Embed(title=f"Request #{aid}", color=EMBED_COLOR)

    embed.add_field(
        name="type",
        value=approval.type,
    )

    data = json.loads(approval.description)

    for k in data:
        if k == "teammates":
            mentions = []
            for t in data[k]:
                user = await client.get_member(t)
                mentions.append(user.mention)
            embed.add_field(name="teammates", value=", ".join(mentions))
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
        value=(WAITING_EMOJI, DONE_EMOJI, CANCEL_EMOJI)[approval.approved]
        + " **"
        + APPROVAL_VALUES[approval.approved]
        + "**",
    )  # the "approved" column

    await ctx.reply(embed=embed)


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
            embed=create_embed(
                f"Something bad happened when trying to parse approval request {embed.title}.",
                error=True,
            )
        )
        return

    approval = get_approval_by_id(aid)
    if approval is None:
        await message.channel.send(
            embed=create_embed(f"No request with ID {aid} was found.")
        )
        return

    request_type = approval.type
    data = json.loads(approval.description)
    try:
        original = await client.get_channel(data["cid"]).fetch_message(data["mid"])
    except:
        original = None

    if approval.approved == 0:
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
                            embed=create_embed(
                                f"Congratulations! You have been awarded {POINTS_PER_SOLVE} points for solving {data['chal']}!"
                            )
                        )
                    except:
                        await client.update_channel.send(
                            embed=create_embed(
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

            accept_request(aid)

            logging.info(f"Accepted {request_type} request {aid}.")
        else:
            for teammate in data["teammates"]:
                try:
                    teammate_user = await client.get_member(teammate)
                    await teammate_user.send(
                        embed=create_embed(
                            f"Your {request_type} for {data['chal']} has been rejected."
                        )
                    )
                except:
                    await client.update_channel.send(
                        embed=create_embed(
                            f"Failed to send message to user {teammate}.", error=True
                        )
                    )

            if original is not None:
                await original.remove_reaction(WAITING_EMOJI, client.user)
                await original.add_reaction(CANCEL_EMOJI)

            reject_request(aid)

            logging.info(f"Rejected {request_type} request {aid}.")

        if referrer is not None:
            await referrer.add_reaction(DONE_EMOJI)
    else:
        if referrer is not None:
            await referrer.add_reaction(CANCEL_EMOJI)

    await message.delete()
    return


# @client.register("!accept", (1, 1), {"dm": False, "officer": True})
@commands.guild_only()
@commands.has_role("officer")
@client.command(
    name="accept",
    brief="Manually accepts a solve or writeup submission.",
    description="Manually accepts a solve or writeup submission.",
    extras={"tags": ["ctf", "officer"]},
)
async def accept(ctx: commands.Context, request: str = ""):
    """!accept <request id>
    Manually accepts a solve or writeup submission."""

    if "" == request:  # bot message reaction
        await handle_approval(ctx.message, True)
    else:
        approval = get_approval_by_id(request)

        if not approval:
            await ctx.reply("Didn't find specified request.")

        approve_message = await client.approval_channel.fetch_message(
            approval.approve_message
        )
        await handle_approval(approve_message, True, ctx)


# @client.register("!reject", (1, 1), {"dm": False, "officer": True})
@commands.guild_only()
@commands.has_role("officer")
@client.command(
    name="reject",
    brief="Manually rejects a solve or writeup submission.",
    description="Manually rejects a solve or writeup submission.",
    extras={"tags": ["ctf", "officer"]},
)
async def reject(ctx: commands.Context, request: str = ""):
    """!reject <request id>
    Manually rejects a solve or writeup submission."""

    if request == "":  # bot message reaction
        await handle_approval(ctx.message, False)
    else:
        approval = get_approval_by_id(request)

        if not approval:
            await ctx.reply("Didn't find specified request.")

        approve_message = await client.approval_channel.fetch_message(
            approval.approve_message
        )
        await handle_approval(approve_message, False, ctx)
