import discord
import email_validator
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
@commands.dm_only()
@client.command(
    name="verify",
    brief="Verify yourself as a Purdue student.",
    description="Sends user a verification email to verify them as a Purdue student.",
    extras={"tags": ["general"]},
)
async def verify_email(ctx: commands.Context, email: str):
    """!verify <youremail@purdue.edu>
    Sends user a verification email to verify them as a Purdue student."""

    discord_user = get_member_by_discord(ctx.author.id)
    if discord_user and discord_user.email:
        await ctx.reply("You have already verified!")
        return

    # Validate if it is a valid email address
    try:
        validated_email = email_validator.validate_email(email)
    except email_validator.EmailNotValidError as e:
        await ctx.reply(embed=create_embed("**INVALID EMAIL**: {0}".format(str(e))))
        return

    # Check if it is a Purdue email
    # TODO: Make this configurable since we are open sourced
    if validated_email.domain != "purdue.edu":
        await ctx.reply(
            embed=create_embed(
                "**INVALID EMAIL**: The email must be a purdue.edu email address."
            )
        )
        return

    # Check if it is already validated or started the validation process
    member = members.get_member_by_email(email)

    # When they started validation
    if member:
        # If already validated
        if member.validated == 1:
            await ctx.reply(
                embed=create_embed(
                    "This email is already verified. If you believe that this is an error, please contact an officer."
                )
            )
        else:
            await ctx.reply(
                embed=create_embed(
                    "You have already received a token, please check your spam and use `!validate <token>`!"
                )
            )
        # Escape this tab hell
        return

    # Start verification process
    notification_message = await ctx.reply(
        embed=create_embed("Sending verification email to {0}...".format(email))
    )

    # Lookup student from Purdue directory
    student_name, error = await get_student_name_from_email_from_directory(email)

    # If student does not exist
    if error:
        await ctx.reply(embed=create_embed(error))
        await client.update_channel.send(embed=create_embed(error))
        return

    # TODO: Optimize this
    # Send email and add them to database
    token = generate_hash(email)

    send_result = await mail.send_mail(
        email, MAIL_SUBJECT, "<br>".join(MAIL_TEMPLATE).format(student_name, token)
    )

    if not send_result:
        await notification_message.edit(
            embed=create_embed(
                "There was an error sending email! Please try again or notify an officer."
            )
        )
        return

    await notification_message.edit(
        embed=create_embed("Done! Please check your inbox.")
    )

    members.add_member(student_name, ctx.author.id, email, token, False)
    logging.debug(f"Verified student {student_name}")


# @client.register("!validate", (1, 1), {"channel": False})
@commands.dm_only()
@client.command(
    name="validate",
    brief="Validate yourself as a Purdue student.",
    description="Completes verification of a user as a Purdue student.",
    extras={"tags": ["general"]},
)
async def validate_email(ctx: commands.Context, vhash: str):
    """!validate <token>
    Completes verification of a user as a Purdue student.
    <token> is sent to the user through email upon running `!verify`."""

    member = members.get_member_by_discord(ctx.author.id)
    if member is None:
        await ctx.reply(
            embed=create_embed(
                "It seems that you haven't started the verification process yet. You can type `!verify <your_purdue_email>` to start it."
            )
        )

    # If they are already validated
    if member.validated:
        await ctx.author.send(embed=create_embed("You are already verified!"))
        # discord_user = await client.get_member(ctx.author.id)
        # await discord_user.add_roles(discord.utils.get(client.guild.roles, name="members"))
        return

    # If not, check if hash matches
    if not compare_digest(member.token, vhash):
        await ctx.author.send(
            embed=create_embed(
                "Incorrect token, please make sure you entered correct token or try again."
            )
        )
        return

    # Verify member
    members.verify_member(ctx.author.id)
    discord_member = await client.get_member(ctx.author.id)
    await discord_member.add_roles(
        discord.utils.get(client.guild.roles, name="members")
    )
    await ctx.reply(
        embed=create_embed(
            "You are now verified. Join our discussion with a member role now!"
        )
    )
    await client.update_channel.send(
        embed=create_embed("Validated user {0}".format(ctx.author.mention))
    )
    logging.debug("Validated user {0}")


# @client.register("!member", (1, 1), {"dm": False, "officer": True})
@commands.guild_only()
@commands.has_role("officer")
@client.command(
    name="member",
    brief="Displays member registration data.",
    description="Displays member registration data.",
    extras={"tags": ["general", "officer"]},
)
async def member_data(ctx: commands.Context, mentioned_user: discord.Member):
    """!member <@user>
    Displays member registration data.
    TODO: `@user` can be replaced with just `USERID`."""

    logging.debug(mentioned_user)

    if mentioned_user is None:
        await ctx.reply(embed=create_embed("Make sure this member is in the server!"))
        return

    name = mentioned_user.name
    uid = mentioned_user.id
    data = members.get_member_by_discord(uid)
    embed = discord.Embed(title=f"Member data for {name}", color=EMBED_COLOR)
    if data is not None:
        for field in data.__dict__["__data__"]:
            embed.add_field(
                name=field,
                value=data.__dict__["__data__"][field],
            )
    else:
        embed.description = f"{name} has not yet started the verification process."

    await ctx.reply(embed=embed)


@commands.dm_only()
@decorators.officer_only()
@client.command(
    name="lookup",
    brief="Lookup student with specified email address",
    extras={"tags": ["general", "officer"]},
)
async def lookup(ctx: commands.Context, email: str) -> None:
    name, err = await get_student_name_from_email_from_directory(email)
    if err:
        await ctx.reply("Error: " + err)
        return
    await ctx.reply(name)
