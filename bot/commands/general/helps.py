import logging

import discord
from discord import Option, guild_only
from discord.ext.commands import Context

from bot import client, commands
from bot.constants import *


# @client.register("!help", (0, 1))
@client.command(
    name="help",
    brief="Get help message",
    description="Displays a list of commands, or info for a specific command if specified.",
    extras={"tags": ["general"]},
)
async def do_help(ctx: Context, command_name: str = ""):
    """!help [command]
    Displays a list of commands, or info for a specific command if specified."""

    all_command_names = [x.name for x in client.commands]

    if command_name != "":
        if command_name in all_command_names:
            command = None
            for x in client.commands:
                if x.name == command_name:
                    command = x
                    break

            is_sender_officer = await client.is_officer(ctx.author.id)

            if "officer" in command.extras.get("tags") and not is_sender_officer:
                await ctx.reply("Unknown command.")
                return

            embed = discord.Embed(
                title=f"Help for command {command.name}", description=command.brief
            )

            embed.set_author(name="B01lers Bot", icon_url=client.me.display_avatar.url)

            embed.add_field(name="Description", value=command.description, inline=True)

            embed.add_field(name="Usage", value=command.help, inline=False)

            embed.set_footer(text="Notes: <required>, [optional]")

            await ctx.reply(embed=embed)
            return
        else:
            await ctx.reply("Unknown command.")
            return

    embed = discord.Embed(
        title="List of all commands available",
        description="Run `!help [command]` for more detailed description and syntax.",
        colour=EMBED_COLOR,
    )

    help_dict = {}
    is_sender_officer = await client.is_officer(ctx.author.id)

    for command in client.commands:
        tags = command.extras.get("tags")
        if not tags:
            continue
        if "officer" in tags and not is_sender_officer:
            continue
        for tag in tags:
            help_dict.setdefault(tag, []).append(command.name)

    for k, v in help_dict.items():
        embed.add_field(name=k.title(), value=", ".join(v))

    await ctx.channel.send(embed=embed)
