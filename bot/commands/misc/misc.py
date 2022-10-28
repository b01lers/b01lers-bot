import discord
from discord import Option
from discord.ext import commands
from owoify import owoify

from bot import client
from bot.helpers import participation
from bot.utils.messages import create_embed


@commands.guild_only()
@client.slash_command(
    name="yeet", description="Just y33t!"
)
async def do_yeet(ctx: discord.ApplicationContext):
    """!yeet
    Just y33t!"""

    channel = ctx.channel
    # Slow, but effective. Isn't that the essence of Python?
    yeet_emoji = discord.utils.get(client.guild.emojis, name="yeet")

    if yeet_emoji is None:
        await ctx.respond("Yeet emoji is not configured yet... 😭", ephemeral=True)
        return

    async for yeet_message in channel.history(limit=20):
        if not yeet_message.content.startswith("!yeet"):
            await yeet_message.add_reaction(yeet_emoji)
            if yeet_message.author.id not in (client.me.id, ctx.author.id):
                participation.give_yeet_points(yeet_message, ctx.author.id)
    await ctx.respond("Y33t!", ephemeral=True)


@commands.has_role("officer")
@client.slash_command(
    name="dm",
    description="Send direct messages to a member."
)
async def do_dm(ctx: discord.ApplicationContext,
                discord_user: Option(discord.Member, "Member to send message to"),
                message: Option(str, "Message content")):
    """!dm <@user> "<message>"
    Direct messages a member."""
    try:
        await discord_user.send(message)
        await ctx.respond("Message sent!", ephemeral=True)
    except:
        await ctx.respond(embed=create_embed("Couldn't send message to user."), ephemeral=True)


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


echo_command_group = client.create_group("echo", "Does what you think it does.")


@echo_command_group.command(
    name="normal",
    description="Does what you think it does normally."
)
async def do_echo(ctx: discord.ApplicationContext, message: Option(str, "Message to echo", required=False, default="")):
    """!echo <message>
    Does what you think it does."""
    if not message:
        await ctx.respond("Echo!")
    else:
        await ctx.respond(message)


@echo_command_group.command(
    name="uwu",
    description="*nuzzles* Wet's wepeat youw wowds i-in a cute way!"
)
async def do_uwu_echo(ctx: discord.ApplicationContext,
                      message: Option(str, "*nuzzles* Sweet things you wanted to s-say to me", required=False)):
    """!echo <message>
    Does what you think it does."""
    if not message:
        await ctx.respond("Hey senpai! P-Pwease say something t-t-to m-me OwO!")
    else:
        await ctx.respond(
            owoify(message, 'uvu')
        )
