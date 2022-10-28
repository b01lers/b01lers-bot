import discord
from discord import Option
from discord.ext import commands

from bot import client, logging, utils
from bot.constants import *
from bot.utils.messages import create_embed


# @client.register("!poll", (1, 17), {"dm": False})
@discord.guild_only()
@client.slash_command(
    name="poll",
    description="Creates a poll in current channel."
)
async def start_poll(ctx: discord.ApplicationContext,
                     title: Option(str, "Poll title"),
                     option_1: Option(str, "Option 1", required=False),
                     option_2: Option(str, "Option 2", required=False),
                     option_3: Option(str, "Option 3", required=False),
                     option_4: Option(str, "Option 4", required=False),
                     option_5: Option(str, "Option 5", required=False),
                     option_6: Option(str, "Option 6", required=False),
                     option_7: Option(str, "Option 7", required=False),
                     option_8: Option(str, "Option 8", required=False),
                     option_9: Option(str, "Option 9", required=False),
                     option_10: Option(str, "Option 10", required=False),
                     option_11: Option(str, "Option 11", required=False),
                     option_12: Option(str, "Option 12", required=False),
                     option_13: Option(str, "Option 13", required=False),
                     option_14: Option(str, "Option 14", required=False),
                     option_15: Option(str, "Option 15", required=False),
                     option_16: Option(str, "Option 16", required=False)):
    """!poll "<poll title>" "[option 1]" "[option 2]" "[option 3]" ... "[option 16]"
    Creates a poll with the specified title and options in the current channel.
    If no options are specified, automatically uses 👍, 👎, and 🤷."""

    # This is some shitty code... but it works for now.
    # I hope no one would blame me on this...

    options = [option_1, option_2, option_3, option_4, option_5, option_6, option_7, option_8, option_9, option_10,
               option_11, option_12, option_13, option_14, option_15, option_16]
    options = list(filter(None, options))

    if len(options) == 0:
        embed = discord.Embed(title="POLL: {0}".format(title), color=EMBED_COLOR)
        for rxn in DEFAULT_REACTIONS:
            embed.add_field(name="-", value=rxn)

        channel = ctx.channel
        sender = ctx.author
        poll = await channel.send(embed=embed)
        for rxn in DEFAULT_REACTIONS:
            await poll.add_reaction(rxn)
    elif len(options) > 1:
        embed = discord.Embed(
            title="POLL: {0}".format(title),
            description="Select the emoji corresponding to the option you want to choose.",
            color=EMBED_COLOR,
        )
        for idx, opt in zip(EMOJINUMBERS, options):
            embed.add_field(name=idx, value=opt)

        channel = ctx.channel
        sender = ctx.author
        poll = await channel.send(embed=embed)
        for i in range(len(options)):
            await poll.add_reaction(EMOJINUMBERS[i])
    else:
        # Nay! Nay! Nay!
        await ctx.respond(f"Guys! {ctx.author.mention} just tried to break our democracy by just giving only one option to vote!")
        return

    await ctx.respond(f"{ctx.author.mention} has started a poll '{title}' with id {channel.id}:{poll.id}!")

    await sender.send(
        embed=create_embed(
            f'Your poll "{title}" has been created. Message me with `/pollresult {channel.id}:{poll.id}` for a ' +
            'results summary or you can right click on the poll message -> select Apps -> Show poll result.'
        )
    )


@client.message_command(name="Show poll result")
async def show_poll_result(ctx: discord.ApplicationContext, msg: discord.Message):
    if len(msg.embeds) != 1:
        await ctx.respond(
            embed=create_embed("The given message does not seem to be a poll."), ephemeral=True
        )
        return

    embed = msg.embeds[0]

    if not embed.title or "POLL" not in embed.title or len(msg.reactions) == 0:
        await ctx.respond(
            embed=create_embed("The given message does not seem to be a poll."), ephemeral=True
        )
        return

    results = {}
    questions = {}
    for idx, field in enumerate(embed.fields):
        questions[idx] = field.value

    for idx, reaction in enumerate(msg.reactions):
        users = await reaction.users().flatten()
        userlist = [
            u.display_name for u in filter(lambda u: u.id != client.user.id, users)
        ]
        results[idx] = [questions[idx], len(userlist), userlist]

    results_embed = discord.Embed(
        title='Poll results for "{0}"'.format(embed.title),
        description="results by number of responses and list of users",
        color=EMBED_COLOR,
    )
    total_responses = 0
    for i in results:
        results_embed.add_field(
            name=results[i][0],
            value="Responses: {0}\nRespondees: {1}".format(
                str(results[i][1]), results[i][2]
            ),
            inline=True,
        )
        total_responses += results[i][1]
    results_embed.add_field(
        name="Total responses: ", value="{0}".format(str(total_responses)), inline=True
    )
    await ctx.respond(embed=results_embed)


@client.slash_command(
    name="pollresult",
    description="Show poll result with specified channel and message id"
)
async def show_poll_result_with_id(ctx: discord.ApplicationContext, poll_id: Option(str, "Id of the poll")):
    """!results <channel id>:<message id>
    Presents the results of a specified poll to the user."""

    try:
        cid, mid = poll_id.split(":")
        cid = int(cid)
        mid = int(mid)
    except:
        await ctx.respond(embed=create_embed("Invalid message or channel ID."), ephemeral=True)
        return

    channel = client.get_channel(cid)
    if channel is None:
        await ctx.respond(embed=create_embed("Malformed channel ID."), ephemeral=True)
        return
    msg = await channel.fetch_message(mid)
    await show_poll_result(ctx, msg)
