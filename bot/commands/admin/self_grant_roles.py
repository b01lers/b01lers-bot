import logging

import discord
from discord import commands, Option, Role, Interaction
from discord.ui import Button
from peewee import IntegrityError

from bot import client
from bot.database.self_grant_roles import get_all_roles, insert_single_role, get_roles_count, update_single_role
from bot.helpers import decorators

BUTTON_STYLE_NAMES = [button_style.name for button_style in discord.ButtonStyle]
BUTTON_STYLE_NAMES.remove("link")

roles_command_group = client.create_group(name="roles", description="All commands about roles")


@decorators.officer_only()
@commands.guild_only()
@roles_command_group.command(
    name="add",
    description="Add a role to the self-grant list."
)
async def add_to_self_grant_list(
        ctx: discord.ApplicationContext,
        role: Option(Role, "Role to add"),
        label: Option(str, "Button label"),
        color: Option(str, "Button color", autocomplete=discord.utils.basic_autocomplete(
            BUTTON_STYLE_NAMES
        )),
        emoji: Option(str, "Emoji shown on the button", required=False, default=None),
):
    if get_roles_count() >= 20:
        await ctx.respond("Discord only allows up to 20 buttons to be added, and we are at the limit!", ephemeral=True)
        return

    if color not in BUTTON_STYLE_NAMES:
        await ctx.respond("Invalid color!", ephemeral=True)
        return

    if role.name == "officer" or role.permissions.administrator or role.permissions.manage_guild:
        await ctx.respond("You don't wanna give out the whole server, right?", ephemeral=True)
        return

    try:
        insert_single_role(role.id, label, color, emoji)
    except IntegrityError:
        update_single_role(role.id, label, color, emoji)
        await ctx.respond("This role already exists! Updating...",
                          ephemeral=True)
        return

    await ctx.respond("Role added! Please remember that this list will be cleared after bot restarts.",
                      ephemeral=True)


async def button_callback(interaction: Interaction):
    try:
        role_id = int(interaction.custom_id)
    except:
        await interaction.response.send_message("Cannot parse role from id, please contact an officer.",
                                                ephemeral=True)
        return

    role: Role = interaction.guild.get_role(role_id)
    if not role:
        await interaction.response.send_message("Invalid role, please contact an officer.", ephemeral=True)
        return

    all_roles = get_all_roles()
    available_roles_id = set([r.role_id for r in all_roles])
    if set(interaction.user.roles).isdisjoint(available_roles_id):
        await interaction.response.send_message("You have already selected a role!", ephemeral=True)
        return

    await interaction.user.add_roles(role, reason="Self-grant role.")
    await interaction.response.send_message(f"You have been granted {role.mention} role!", ephemeral=True)


class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for role in get_all_roles():
            button = Button(
                label=role.label,
                style=discord.ButtonStyle[role.color],
                emoji=role.emoji,
                custom_id=f"{role.role_id}"
            )
            button.callback = button_callback
            self.add_item(button)


@decorators.officer_only()
@commands.guild_only()
@roles_command_group.command(
    name="announce",
    description="Create a message to announce all available roles to self-grant."
)
async def send_grant_roles_message(
        ctx: discord.ApplicationContext,
        message: Option(str, "Message to include")
):
    if get_roles_count() == 0:
        await ctx.respond("There is no available self-grant roles set.", ephemeral=True)
        return

    view = RoleView()
    logging.debug(view.is_persistent())
    message = await ctx.channel.send(message, view=view)
    client.add_view(view, message_id=message.id)
    await ctx.respond("Message created!", ephemeral=True)


async def reset_message_view(msg: discord.message) -> bool:
    if msg.author.id != client.me.id:
        return False
    await msg.edit(view=RoleView())
    return True


@decorators.officer_only()
@client.message_command(name="Reset role messsage")
async def reset_role_message(ctx: discord.ApplicationContext, msg: discord.Message):
    if not reset_message_view(msg):
        await ctx.respond("I can only edit messages of myself!", ephemeral=True)
        return

    await ctx.respond("Message has been updated.", ephemeral=True)
