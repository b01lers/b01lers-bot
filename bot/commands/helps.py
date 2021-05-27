import discord

from bot import client, logging
from bot.constants import *


@client.register("!help", (0, 1))
async def do_help(message, *args):
    """!help [command]
    Displays a list of commands, or info for a specific command if specified."""

    if len(args) == 0:
        embed = discord.Embed(
            title="Command List",
            description="Run `!help [command]` for more detailed description and syntax.",
            color=EMBED_COLOR,
        )
        dm_commands = []
        commands = []
        is_officer = await client.is_officer_message(message)

        for cmd in client.commands:
            if client.commands[cmd].options["officer"] and not is_officer:
                continue

            if client.commands[cmd].options["dm"]:
                dm_commands.append(f"`{cmd}`")
            if client.commands[cmd].options["channel"]:
                commands.append(f"`{cmd}`")

        embed.add_field(name="Channel Commands", value=" ".join(commands), inline=False)
        embed.add_field(name="DM Commands", value=" ".join(dm_commands), inline=False)

        await message.channel.send(embed=embed)
    else:
        (command,) = args
        if not command.startswith("!"):
            command = "!" + command

        commandobj = client.commands.get(command)
        if commandobj:
            embed = discord.Embed(
                title=command,
                description="\n".join(commandobj.description)
                + ("\nFor officer use only." if commandobj.options["officer"] else ""),
                color=EMBED_COLOR,
            )
            embed.add_field(
                name="Syntax",
                value='`{0}`\n*ARGUMENTS: `<required>`, `[optional]`. Include any `""` you see.*'.format(
                    commandobj.syntax
                ),
                inline=False,
            )
            await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(
                title=command, description="Command not found.", color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)

    return
