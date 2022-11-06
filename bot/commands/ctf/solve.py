from typing import Union

import discord
from discord import Member, Option
from discord.ext import commands
from discord.ui import Item

from bot import client
from bot.constants import *
from bot.database.approval import (
    create_approval_and_return_id,
    get_approval_by_id,
    accept_request,
    reject_request,
)
from bot.helpers import participation
from bot.utils.messages import create_embed


async def handle_approval(aid: int, approved: bool) -> bool:
    # TODO: Implement writeup
    approval = get_approval_by_id(aid)
    if approval is None or approval.approved:
        return False

    data = json.loads(approval.description)

    if approved:
        accept_request(aid)
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
    else:
        reject_request(aid)
        for teammate in data["teammates"]:
            try:
                teammate_user = await client.get_member(teammate)
                await teammate_user.send(
                    embed=create_embed(
                        f"Your solve for {data['chal']} has been rejected."
                    )
                )
            except:
                await client.update_channel.send(
                    embed=create_embed(
                        f"Failed to send message to user {teammate}.", error=True
                    )
                )

    return True


@discord.guild_only()
@client.slash_command(
    name="solve",
    description="Submit a flag to specific challenge."
)
async def submit_solve(
        ctx: discord.ApplicationContext,
        challenge: Option(str, "Challenge name"),
        category: Option(str, "Challenge category", autocomplete=discord.utils.basic_autocomplete(CTF_CHAL_CATEGORIES)),
        flag: Option(str, "Challenge flag"),
        tm1: Option(Member, "Teammate 1", required=False),
        tm2: Option(Member, "Teammate 2", required=False),
        tm3: Option(Member, "Teammate 3", required=False),
        tm4: Option(Member, "Teammate 4", required=False)
):
    """!solve "<chal name>" <category> "<flag>" [@teammate 1]... [@teammate 4]
    Submits a solved challenge with up to 4 collaborators.
    `<category>` should be one of `re`, `pwn`, `web`, `crypto`, `other`.
    Gives 100 participation points to each collaborator upon officer approval."""

    # Preliminary checks
    if ctx.channel.category_id != LIVE_CTF_CATEGORY:
        await ctx.respond(
            embed=create_embed("Please submit your solve in a live CTF channel."), ephemeral=True
        )
        return

    if category not in CTF_CHAL_CATEGORIES:
        await ctx.respond(
            embed=create_embed(
                f"Make sure `<category>` is one of {', '.join(map(lambda x: f'`{x}`', CTF_CHAL_CATEGORIES))}!"
            ), ephemeral=True
        )
        return

    teammates = list(filter(lambda item: item is not None, [tm1, tm2, tm3, tm4]))
    challenge = challenge.lower()
    category = category.lower()

    teammates.insert(0, await client.get_member(ctx.author.id))

    data = {
        "chal": challenge,
        "category": category,
        "flag": flag,
        "teammates": [x.id for x in teammates],
        "cid": ctx.channel.id
        # "mid": ctx.message.id,
    }

    aid = create_approval_and_return_id(json.dumps(data))

    class ApprovalView(discord.ui.View):

        def __init__(self, *items: Item, timeout: Union[float, None] = 180.0, disable_on_timeout: bool = False):
            super().__init__(*items, timeout=timeout, disable_on_timeout=disable_on_timeout)
            self.timeout = None
            self.aid = aid

        @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
        async def accept_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
            if await handle_approval(aid, True):
                await self.message.edit(f"This request is approved by {interaction.user.mention}.", view=None)
            else:
                await self.message.edit(f"Request #{aid} is already reviewed by other officers.", embed=None, view=None)

        @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❎")
        async def reject_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
            if await handle_approval(aid, False):
                await self.message.edit(f"This request is rejected by {interaction.user.mention}.", view=None)
            else:
                await self.message.edit(f"Request #{aid} is already reviewed by other officers.", embed=None, view=None)

    embed = discord.Embed(
        title=f"New Review Request #{aid}",
        description=f"Here is a new CTF solve request submitted by {ctx.author.mention}"
    )

    embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/568451513295441921/9Hm60msK_400x400.png")

    embed.add_field(name="Challenge", value=challenge, inline=True)
    embed.add_field(name="Category", value=category, inline=True)
    embed.add_field(name="CTF", value=ctx.channel.mention, inline=True)
    embed.add_field(name="Flag", value=f"```{flag}```", inline=False)
    embed.add_field(name="Participants", value=', '.join(tm.mention for tm in teammates), inline=False)

    await client.approval_channel.send(embed=embed, view=ApprovalView())

    await ctx.respond(
        f"Your solve for {challenge} has been recorded with request ID {aid}."
    )


# @client.register("!review", (1, 1), {"dm": False, "officer": True})
@discord.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="review",
    description="Displays data about a solve or writeup request."
)
async def review(ctx: discord.ApplicationContext, approval_id: Option(int, "ID of the approval request")):
    """!review <request id>
    Displays data about a solve or writeup request."""

    approval = get_approval_by_id(approval_id)
    if not approval:
        await ctx.respond("Request not found.", ephemeral=True)
        return

    embed = discord.Embed(title=f"Request #{approval_id}", color=EMBED_COLOR)

    embed.add_field(
        name="Type",
        value=approval.type,
    )

    data = json.loads(approval.description)

    for k in data:
        if k == "teammates":
            mentions = []
            for t in data[k]:
                user = await client.get_member(t)
                mentions.append(user.mention)
            embed.add_field(name=str(k).title(), value=", ".join(mentions))
        elif k == "cid":
            embed.add_field(name=str(k).title(), value=client.get_channel(data[k]).mention)
        else:
            embed.add_field(name=str(k).title(), value="`" + str(data[k]) + "`")

    embed.add_field(
        name="Status",
        value=(WAITING_EMOJI, DONE_EMOJI, CANCEL_EMOJI)[approval.approved]
              + " **"
              + APPROVAL_VALUES[approval.approved]
              + "**",
    )  # the "approved" column

    await ctx.respond(embed=embed)


# @client.register("!accept", (1, 1), {"dm": False, "officer": True})
@discord.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="accept",
    description="Manually accepts a solve or writeup submission."
)
async def accept(ctx: discord.ApplicationContext, aid: Option(int, "Id of the request")):
    """!accept <request id>
    Manually accepts a solve or writeup submission."""
    if await handle_approval(aid, True):
        await ctx.respond(f"Request {aid} has been manually accepted by {ctx.author.mention}.")
    else:
        await ctx.respond(f"Cannot accept request {aid}, maybe it is already handled by other officers?", ephemeral=True)


# @client.register("!reject", (1, 1), {"dm": False, "officer": True})
@discord.guild_only()
@commands.has_role("officer")
@client.slash_command(
    name="reject",
    description="Manually rejects a solve or writeup submission."
)
async def reject(ctx: discord.ApplicationContext, aid: Option(int, "Id of the request")):
    """!reject <request id>
    Manually rejects a solve or writeup submission."""
    if await handle_approval(aid, False):
        await ctx.respond(f"Request {aid} has been manually rejected by {ctx.author.mention}.")
    else:
        await ctx.respond(f"Cannot reject request {aid}, maybe it is already handled by other officers?", ephemeral=True)
