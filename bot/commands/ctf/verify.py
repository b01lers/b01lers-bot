import discord
import email_validator
from discord import Option
from discord.ext import commands

from bot import client, logging
from bot.utils import mail
from bot.constants import *
from bot.database import members
from secrets import compare_digest

from bot.database.members import get_member_by_discord
from bot.helpers import decorators
from bot.utils.messages import create_embed
from bot.utils.validation import (
    get_student_name_from_email_from_directory,
    generate_hash,
)


# @client.register("!verify", (1, 1), {"channel": False})
@client.slash_command(
    name="verify",
    description="Verify yourself as a certified Purdue student.",
)
async def verify_email(ctx: discord.ApplicationContext, email: Option(str, "Your Purdue Email")):
    """!verify <youremail@purdue.edu>
    Sends user a verification email to verify them as a Purdue student."""

    discord_user = get_member_by_discord(ctx.author.id)
    if discord_user and discord_user.email:
        if discord_user.validated == 1:
            await ctx.respond("You have already verified!", ephemeral=True)
        else:
            await ctx.respond("You have already received a token, please check your spam and use `/validate <token>`!",
                              ephemeral=True)
        return

    # Validate if it is a valid email address
    try:
        validated_email = email_validator.validate_email(email)
    except email_validator.EmailNotValidError as e:
        await ctx.respond(embed=create_embed("**INVALID EMAIL**: {0}".format(str(e))), ephemeral=True)
        return

    # Check if it is a Purdue email
    # TODO: Make this configurable since we are open sourced
    if validated_email.domain != "purdue.edu":
        await ctx.respond(
            embed=create_embed(
                "**INVALID EMAIL**: The email must be a purdue.edu email address."
            ), ephemeral=True
        )
        return

    # Check if it is already validated or started the validation process
    member = members.get_member_by_email(email)

    # When they started validation
    if member:
        await ctx.respond(
            "This email is already verified. If you believe that this is an error, please contact an officer.",
            ephemeral=True
        )
        # Escape this tab hell
        return

    # Start verification process
    interaction = await ctx.respond(
        "Sending verification email to {0}...".format(email),
        ephemeral=True
    )

    # Lookup student from Purdue directory
    student_name, error = await get_student_name_from_email_from_directory(email)

    # If student does not exist
    if error:
        await ctx.respond(embed=create_embed(error), ephemeral=True)
        await client.update_channel.send(embed=create_embed(error))
        return

    # TODO: Optimize this
    # Send email and add them to database
    token = generate_hash(email)

    send_result = await mail.send_mail(
        email, MAIL_SUBJECT, "<br>".join(MAIL_TEMPLATE).format(student_name, token)
    )

    if not send_result:
        await interaction.followup.send(
            embed=create_embed(
                "There was an error sending email! Please try again or notify an officer."
            ),
            ephemeral=True
        )
        return

    await interaction.followup.send(
        "Done! Please check your inbox.",
        ephemeral=True
    )

    members.add_member(student_name, ctx.author.id, email, token, False)
    logging.debug(f"Added student {student_name} to validation database.")


# @client.register("!validate", (1, 1), {"channel": False})
@client.slash_command(
    name="validate",
    description="Submit your token to complete the verification of you being a Purdue student."
)
async def validate_email(ctx: discord.ApplicationContext,
                         token: Option(str, "Token you received in the verification email")):
    """!validate <token>
    Completes verification of a user as a Purdue student.
    <token> is sent to the user through email upon running `!verify`."""

    member = members.get_member_by_discord(ctx.author.id)
    if member is None:
        await ctx.respond(
            "It seems that you haven't started the verification process yet. You can use `/verify <your_purdue_email>` to start it.",
            ephemeral=True
        )
        return

    # If they are already validated
    if member.validated:
        await ctx.respond(
            embed=create_embed(
                "You are already verified!"
            ),
            ephemeral=True
        )
        # discord_user = await client.get_member(ctx.author.id)
        # await discord_user.add_roles(discord.utils.get(client.guild.roles, name="members"))
        return

    # If not, check if hash matches
    if not compare_digest(member.token, token):
        await ctx.respond(
            embed=create_embed(
                "Incorrect token, please make sure you entered correct token or try again."
            ),
            ephemeral=True
        )
        return

    # Verify member
    members.verify_member(ctx.author.id)
    discord_member = await client.get_member(ctx.author.id)
    await discord_member.add_roles(
        discord.utils.get(client.guild.roles, name="members")
    )
    await ctx.respond(
        "You are now verified. Join our discussion with a member role now!",
        ephemeral=True
    )
    await client.update_channel.send(
        embed=create_embed("Validated user {0}".format(ctx.author.mention))
    )
    logging.debug("Validated user {0}")


# @client.register("!member", (1, 1), {"dm": False, "officer": True})
@commands.has_role("officer")
@client.slash_command(
    name="member",
    description="Displays a member's registration data.",
)
async def member_data(ctx: discord.ApplicationContext, user: Option(discord.Member, "Member to show data.", required=False)):
    """!member <@user>
    Displays member registration data.
    TODO: `@user` can be replaced with just `USERID`."""

    user = user or ctx.author

    name = user.name
    uid = user.id
    data = members.get_member_by_discord(uid)
    embed = discord.Embed(title=f"Member data for {name}", color=EMBED_COLOR)
    if data is not None:
        for field in data.__dict__["__data__"]:
            if field == "alias":
                data.__dict__["__data__"][field] = user.mention

            embed.add_field(
                name=field.title(),
                value=data.__dict__["__data__"][field],
            )
    else:
        embed.description = f"{user.mention} has not yet started the verification process."

    await ctx.respond(embed=embed, ephemeral=True)
