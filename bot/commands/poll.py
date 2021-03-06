import discord

from bot import client, logging, utils
from bot.constants import *


@client.register("!poll", (1, 17), {"dm": False})
async def start_poll(message, *args):
    """!poll "<poll title>" "[option 1]" "[option 2]" "[option 3]" ... "[option 16]"
    Creates a poll with the specified title and options in the current channel.
    If no options are specified, automatically uses 👍, 👎, and 🤷."""

    title, *options = args

    if not message.author.bot:
        if len(options) == 0:
            embed = discord.Embed(title="POLL: {0}".format(title), color=EMBED_COLOR)
            for rxn in DEFAULT_REACTIONS:
                embed.add_field(name="-", value=rxn)

            channel = message.channel
            sender = message.author
            await message.delete()
            poll = await channel.send(embed=embed)
            for rxn in DEFAULT_REACTIONS:
                await poll.add_reaction(rxn)
        else:
            embed = discord.Embed(
                title="POLL: {0}".format(title),
                description="Select the emoji corresponding to the option you want to choose.",
                color=EMBED_COLOR,
            )
            for idx, opt in zip(EMOJINUMBERS, options):
                embed.add_field(name=idx, value=opt)

            channel = message.channel
            sender = message.author
            await message.delete()
            poll = await channel.send(embed=embed)
            for i in range(len(options)):
                await poll.add_reaction(EMOJINUMBERS[i])

        await sender.send(
            embed=utils.create_embed(
                'Your poll "{0}" has been created. Message me with `!results {1}:{2}` for a results summary.'.format(
                    title, str(channel.id), str(poll.id)
                )
            )
        )

    return


@client.register("!results", (1, 1), {"channel": False})
async def poll_results(message, *args):
    """!results <channel id>:<message id>
    Presents the results of a specified poll to the user."""

    (ids,) = args
    try:
        cid, mid = ids.split(":")
        cid = int(cid)
        mid = int(mid)
    except:
        await message.author.send(
            embed=utils.create_embed("Invalid message or channel ID.")
        )
        return

    channel = client.get_channel(cid)
    if channel is None:
        await message.author.send(embed=utils.create_embed("Malformed channel ID."))
        return
    msg = await channel.fetch_message(mid)
    if len(msg.embeds) != 1:
        await message.author.send(
            embed=utils.create_embed("The given message does not seem to be a poll.")
        )
        return

    embed = msg.embeds[0]
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
    await message.author.send(embed=results_embed)

    return
