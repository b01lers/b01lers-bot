import discord
from discord.ext import commands

from bot import client
from bot.helpers import participation
from bot.constants import *
from bot.utils.messages import create_embed


@commands.guild_only()
@client.command(
    name="yeet", brief="Just y33t!", description="Just y33t!", extras={"tags": ["fun"]}
)
async def do_yeet(ctx: commands.Context):
    """!yeet
    Just y33t!"""

    channel = ctx.channel
    # Slow, but effective. Isn't that the essence of Python?
    yeet_emoji = discord.utils.get(client.guild.emojis, name="yeet")

    if yeet_emoji is None:
        sad_message = await channel.send("Yeet emoji is not configured yet...")
        await sad_message.add_reaction(
            # I don't think Discord would remove :cry:...
            "😭"
        )
        return

    await ctx.message.delete()
    async for yeet_message in channel.history(limit=20):
        if not yeet_message.content.startswith("!yeet"):
            await yeet_message.add_reaction(yeet_emoji)
            if yeet_message.author.id not in (client.me.id, ctx.author.id):
                participation.give_yeet_points(yeet_message, ctx.author.id)


@commands.has_role("officer")
@client.command(
    name="dm",
    brief="Send direct messages a member.",
    description="Send direct messages to a member.",
    extras={"tags": ["general", "officer"]},
)
async def do_dm(ctx: commands.Context, discord_user: discord.Member, *args):
    """!dm <@user> "<message>"
    Direct messages a member."""
    try:
        await discord_user.send(" ".join(args))
        await ctx.message.add_reaction(DONE_EMOJI)
    except:
        await ctx.author.send(embed=create_embed("Couldn't send message to user."))


# This command is not currently used.
# @client.register("!restore", (0, 0), {"channel": False})
# async def restore_mail(self, message):
#     """!restore
#     Restores a member."""
#
#     embed = create_embed(":broken_heart: Removed Member Mail:")
#     embed.add_field(name="Contents", value=message.content[8:])
#     await client.update_channel.send(embed=embed)
#     return

# @client.register("!echo", (0, 5000))
@client.command(
    name="echo",
    brief="Does what you think it does.",
    description="Does what you think it does.",
    extras={"tags": ["general"]},
)
async def do_echo(ctx: commands.Context, *, message=""):
    """!echo <message>
    Does what you think it does."""
    # Default message as empty to avoid MissingRequiredArgument error
    if message.strip() == "":
        await ctx.channel.send(embed=create_embed("Echo!"))
    else:
        await ctx.channel.send(message)
    await ctx.message.delete()
