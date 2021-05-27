import discord
import email_validator

from bot import client, logging
from bot import database, utils, mail
from bot.constants import *


@client.register("!verify", (1, 1), {"channel": False})
async def verify_email(message, *args):
    """!verify <youremail@purdue.edu>
    Sends user a verification email to verify them as a Purdue student."""

    (email,) = args
    try:
        valid = email_validator.validate_email(email)
        email = valid.email
        domain = valid.domain
        if domain != "purdue.edu":
            await message.author.send(
                embed=utils.create_embed(
                    "**INVALID EMAIL**: The email must be a purdue.edu email address."
                )
            )
        else:
            match = database.get_student_by_email(email)
            if match:
                if database.column_name_index("validated", MEMBERS_COLUMNS, match) == 1:
                    await message.author.send(
                        embed=utils.create_embed("You have already been verified!")
                    )
                    member = await client.get_member(message.author.id)
                    await member.add_roles(
                        discord.utils.get(client.guild.roles, name="members")
                    )
                else:
                    await message.author.send(
                        embed=utils.create_embed(
                            "You have already received a token, please check your spam and use `!validate <token>`!"
                        )
                    )
            else:
                await message.author.send(
                    embed=utils.create_embed(
                        "Sending verification email to {0}...".format(email)
                    )
                )
                record = await utils.lookup_student(email, message)
                if not record.success:
                    await message.author.send(embed=utils.create_embed(record.error))
                    await client.update_channel.send(
                        embed=utils.create_embed(record.log)
                    )
                    return
                mail.send_mail(
                    database.column_name_index("email", MEMBERS_COLUMNS, record.record),
                    "b01lers discord verification",
                    "Welcome, {0}, to b01lers! Please paste the following command into your DM with b01lers-bot: '!validate {1}'".format(
                        database.column_name_index(
                            "name", MEMBERS_COLUMNS, record.record
                        ),
                        database.column_name_index(
                            "token", MEMBERS_COLUMNS, record.record
                        ),
                    ),
                )
                await message.author.send(
                    embed=utils.create_embed("Done! Please check your inbox.")
                )
                database.add_student(record.record)
                logging.debug("Verified student with record {0}".format(record.record))
    except email_validator.EmailNotValidError as e:
        await message.author.send(
            embed=utils.create_embed("**INVALID EMAIL**: {0}".format(str(e)))
        )

    return


@client.register("!validate", (1, 1), {"channel": False})
async def validate_email(message, *args):
    """!validate <token>
    Completes verification of a user as a Purdue student.
    <token> is sent to the user thru email upon running `!verify`."""

    (vhash,) = args
    user = database.get_student_by_discord(str(message.author.id))
    if user is None:
        await message.author.send(
            embed=utils.create_embed(
                "You aren't in the database. Did you use `!verify` first?"
            )
        )

    if database.column_name_index("validated", MEMBERS_COLUMNS, user) == 1:
        await message.author.send(
            embed=utils.create_embed("You have already been verified!")
        )
        member = await client.get_member(message.author.id)
        await member.add_roles(discord.utils.get(client.guild.roles, name="members"))
        return

    if database.column_name_index("token", MEMBERS_COLUMNS, user) == vhash:
        try:
            database.verify_student(str(message.author.id))
        except:
            await message.author.send(
                embed=utils.create_embed(
                    "Oops! Something went wrong. Please contact an officer."
                )
            )
            return

        member = await client.get_member(message.author.id)
        await member.add_roles(discord.utils.get(client.guild.roles, name="members"))
        await message.author.send(
            embed=utils.create_embed("Verified. You should have the Members role now.")
        )
        await client.update_channel.send(
            embed=utils.create_embed(
                "Validated user {0}".format(message.author.mention)
            )
        )
        logging.info("Validated user {0}")
    else:
        await message.author.send(
            embed=utils.create_embed("Incorrect token, please try again.")
        )

    return


@client.register("!member", (1, 1), {"dm": False, "officer": True})
async def member_data(message, *args):
    """!member <@user>
    Displays member registration data.
    `@user` can be replaced with just `USERID`."""

    (uid,) = args
    try:
        uid = int(utils.parse_uid(uid))
    except:
        await message.channel.send(
            embed=utils.create_embed(
                "Make sure you have mentioned the user correctly! You can mention users not in this channel by typing `<!@USERID>`."
            )
        )
        return

    member = await client.get_member(uid)
    name = member.name
    if name is None:
        await message.channel.send(
            embed=utils.create_embed("Make sure this member is in the server!")
        )
        return

    user = database.get_student_by_discord(uid)
    embed = discord.Embed(title=f"Member data for {name}", color=EMBED_COLOR)
    if user is not None:
        for col in MEMBERS_COLUMNS:
            embed.add_field(
                name=col,
                value=str(database.column_name_index(col, MEMBERS_COLUMNS, user)),
            )
    else:
        embed.description = f"{name} has not yet started the verification process."

    await message.channel.send(embed=embed)
    return
