import os

import discord
import email_validator

from bot import client, database, logging, utils
from bot.constants import *


@client.register("!competition", (4, 4), {"officer": True})
async def make_competition(message, *args):
    """!competition "<channel name>" "<description>" "<username>" "<password>"
    Creates a competition channel."""

    title, description, username, password = args
    if client.ctfs in client.guild.categories:
        channel = await client.ctfs.create_text_channel(
            title,
            position=0,
            topic=f"{title}\n==========\n{description}\n==========\nusername: {username}\n==========\nOfficers, type !archive to archive this channel.",
        )
        embed = discord.Embed(title=title, description=description, color=EMBED_COLOR)
        for k, v in zip(("Username", "Password"), (f"`{username}`", f"`{password}`")):
            embed.add_field(name=k, value=v, inline=False)
        pinmessage = await channel.send(embed=embed)
        await pinmessage.pin()
        await message.delete()
        return

    await message.channel.send(
        embed=utils.create_embed("The `live ctfs` category cannot be found.")
    )
    return


@client.register("!chal", (1, 1), {"dm": False})
async def make_chal_channel(message, *args):
    """!chal "<challenge name>"
    Creates a channel for a single challenge during a CTF."""

    (chalname,) = args
    channame = chalname.replace(" ", "-")

    if message.channel.category_id == client.ctfs.id:
        ctf = message.channel.name
        cat = None
        live_ctf_position = 0

        for category in client.guild.categories:
            if live_ctf_position <= 0:
                live_ctf_position += -1
            if category.name.lower() == "live ctfs":
                live_ctf_position *= -1
            if category.name.lower() == message.channel.name.lower() + " challenges":
                cat = category
                break
        if cat is None:
            permissions = message.channel.overwrites
            cat = await client.guild.create_category(
                message.channel.name.lower() + " challenges",
                overwrites=permissions,
                position=live_ctf_position,
            )

        for chan in category.text_channels:
            if chan.name.lower() == channame.lower():
                await message.channel.send(
                    embed=utils.create_embed(
                        f"A channel for this challenge has already been created! Click [here](https://discordapp.com/channels/{GUILD}/{chan.id}/) to join the discussion."
                    )
                )
                return

        chan = await cat.create_text_channel(
            channame,
            position=len(cat.text_channels),
            topic=f"{message.channel.name}: {chalname}",
        )
        await message.channel.send(
            embed=utils.create_embed(
                f"Channel created! Click [here](https://discordapp.com/channels/{GUILD}/{chan.id}/) to go there."
            )
        )
        return

    await message.channel.send(
        embed=utils.create_embed(
            "This command can only be used in a `live ctfs` channel."
        )
    )
    return


@client.register("!archive", (0, 0), {"dm": False, "officer": True})
async def archive_competition(message, *args):
    """!archive
    Archives the current competition channel from the Live CTFs category, as well as challenge channels if they exist.
    If used in a challenge-specific channel, deletes the channel and sends a log of the chat to the main competition channel."""

    if message.channel.category_id == client.ctfs.id:
        for category, chal_channels in client.guild.by_category():
            if message.channel.name.lower() + " challenges" == category.name.lower():
                for channel in chal_channels:
                    await archive_channel(channel, message.channel)
                break

        await message.channel.edit(category=client.archive)
        await message.channel.edit(position=0)
    elif message.channel.category.name.endswith(" challenges"):
        ctf = message.channel.category.name[:-len(" challenges")].replace(" ", "-")
        for chan in client.ctfs.text_channels:
            if chan.name.lower() == ctf.lower():
                await archive_channel(message.channel, chan)
                return
        
        await message.channel.send(
            embed=utils.create_embed(f"Could not find live CTF channel {ctf}. Was it accidentally moved?")
        )
        return

    return


async def archive_channel(channel, ctf_channel):
    fname = f"{ctf_channel.name}_{channel.name}_log.txt"
    f = open(fname, "w")
    async for m in channel.history(limit=10000, oldest_first=True):
        f.write(f"[{m.created_at.replace().strftime('%Y-%m-%d %I:%M %p')} UTC] {m.author.display_name}: {m.content}\n{' '.join(map(lambda x: x.url, m.attachments))}\n")
    f.close()

    f = open(fname, "rb")
    await ctf_channel.send(
        embed = utils.create_embed(f"Discussion for the challenge {channel.name} has been archived. A text log of the conversation is attached."),
        file = discord.File(f)
    )
    f.close()

    os.remove(fname)

    cat = channel.category
    await channel.delete()
    if len(cat.text_channels) == 0:
        await cat.delete()


@client.register("!invite", (1, 4), {"dm": False, "officer": True})
async def invite(message, *args):
    """!invite <@mention-1> [@mention-2] [@mention-3] [@mention-4]
    Gives roles or users access to a CTF channel."""

    if not message.channel.category.name.lower() == "live ctfs":
        await message.channel.send(
            embed=utils.create_embed(
                "Please use this command in a live ctfs channel only!"
            )
        )
        return

    successful_joins = []
    for obj in args:
        try:
            obj_id = int(utils.parse_uid(obj))
            role = client.guild.get_role(obj_id)
            user = client.guild.get_member(obj_id)
            if role == None and user == None:
                raise Exception()  # totally a hack lmao
            await message.channel.set_permissions(
                role or user, read_messages=True, send_messages=True
            )
            successful_joins.append(obj)
        except:
            await message.channel.send(
                embed=utils.create_embed(f"Could not invite {obj} to channel.")
            )

    await message.channel.send(
        embed=utils.create_embed(f"Have fun, {', '.join(successful_joins)}!")
    )


@client.register("!uninvite", (1, 4), {"dm": False, "officer": True})
async def uninvite(message, *args):
    """!uninvite <@mention-1> [@mention-2] [@mention-3] [@mention-4]
    Removes roles' or users' access from a CTF channel."""

    if not message.channel.category.name.lower() == "live ctfs":
        await message.channel.send(
            embed=utils.create_embed(
                "Please use this command in a live ctfs channel only!"
            )
        )
        return

    successful_leaves = []
    for obj in args:
        try:
            obj_id = int(utils.parse_uid(obj))
            role = client.guild.get_role(obj_id)
            user = client.guild.get_member(obj_id)
            if role == None and user == None:
                raise Exception()  # totally a hack lmao
            await message.channel.set_permissions(
                role or user, read_messages=False, send_messages=False
            )
            successful_leaves.append(obj)
        except:
            await message.channel.send(
                embed=utils.create_embed(f"Could not remove {obj} from channel.")
            )

    await message.channel.send(
        embed=utils.create_embed(f"Goodbye, {', '.join(successful_leaves)}. :pensive:")
    )


@client.register("!ctfregister", (1, 4), {"channel": False})
async def ctf_register(message, *args):
    """!ctfregister <youremail@purdue.edu> [teammate1@purdue.edu] [teammate2@purdue.edu] [teammate3@purdue.edu]
    Registers a team for the b00tcamp CTF with you and up to three more teammates."""

    user_email = args[0]
    try:
        valid = email_validator.validate_email(user_email)
        if valid.domain != "purdue.edu":
            await message.author.send(
                embed=utils.create_embed(
                    "Your email must be a purdue.edu email address."
                )
            )
            return
    except email_validator.EmailNotValidError:
        await message.author.send(
            embed=utils.create_embed("Please enter a valid email for yourself.")
        )
        return

    teammates = []
    for email in args[1:]:
        try:
            valid = email_validator.validate_email(email)
            if valid.domain != "purdue.edu":
                await message.author.send(
                    embed=utils.create_embed(
                        "{} is not a @purdue.edu email.".format(email)
                    )
                )
                return
            teammates.append(email)
        except email_validator.EmailNotValidError:
            await message.author.send(
                embed=utils.create_embed("{} is not a valid email.".format(email))
            )
            return

    teammember_records = database.get_ctf_teammember_registration(user_email)
    registerer_records = database.get_ctf_registration(user_email)
    record = database.get_student_by_discord(str(message.author.id))
    if record is None:
        await message.author.send(
            embed=utils.create_embed(
                "You haven't registered with me yet! Use `!verify <your-email@purdue.edu>` to verify yourself."
            )
        )
        return
    elif database.column_name_index("email", MEMBERS_COLUMNS, record) != user_email:
        await message.author.send(
            embed=utils.create_embed(
                "Your provided email does not match the record for your username. Try using {0} instead.".format(
                    database.column_name_index("email", MEMBERS_COLUMNS, record)
                )
            )
        )
        return

    if len(teammates) == 0:
        if registerer_records is not None:
            await message.author.send(
                embed=utils.create_embed(
                    "You are already registered as the registering email for the registration {0}. I am updating this registration to be just you. If this is an error, just run it again with the right people.".format(
                        registerer_records
                    )
                )
            )
            database.update_ctf_team(
                (
                    user_email,
                    " ",
                    " ",
                    " ",
                    user_email,
                )
            )
            logging.info("Registered solo student {0}".format(user_email))
        elif teammember_records is not None:
            await message.author.send(
                embed=utils.create_embed(
                    "You are already registered as a team member for the team {0}. Removing you from that team and re-registering you solo.".format(
                        teammember_records
                    )
                )
            )
            record = teammember_records
            new_record = []
            for r in record:
                if r == user_email:
                    new_record.append(" ")
                else:
                    new_record.append(r)
            database.update_ctf_team(
                (
                    *new_record,
                    new_record[0],
                )
            )
            database.register_ctf_team(
                (
                    user_email,
                    " ",
                    " ",
                    " ",
                )
            )
        else:
            await message.author.send(
                embed=utils.create_embed(
                    "Looks like you're playing by yourself! That's perfectly fine, we're sure you'll get a lot out of it. If you change your mind, you can run this command again with any teammates."
                )
            )
            database.register_ctf_team(
                (
                    user_email,
                    " ",
                    " ",
                    " ",
                )
            )
            logging.info("Registered solo student {0}".format(user_email))

        await message.author.send("You're all signed up. :)")
    else:
        if registerer_records is not None:
            await message.author.send(
                embed=utils.create_embed(
                    "You have already registered a team. I'm updating your team registration now. If this is an error, just re-register the original one."
                )
            )
            teammates += [" ", " ", " "]
            teammates = teammates[:3]
            database.update_ctf_team(
                (
                    user_email,
                    *teammates,
                    user_email,
                )
            )
            await message.author.send("Updated your record.")
        elif teammember_records is not None:
            await message.author.send(
                embed=utils.create_embed(
                    "You have already been registered as a member of a team. I'm removing you from that team and registering your new one."
                )
            )
            record = teammember_records[0]
            new_record = []
            for r in record:
                if r == user_email:
                    new_record.append(" ")
                else:
                    new_record.append(r)
            database.update_ctf_team(
                (
                    *new_record,
                    new_record[0],
                )
            )

            teammates += [" ", " ", " "]
            teammates = teammates[:3]
            database.register_ctf_team(
                (
                    user_email,
                    *teammates,
                )
            )
            await message.author.send(
                embed=utils.create_embed("Registered your new team.")
            )
        else:
            teammates += [" ", " ", " "]
            teammates = teammates[:3]
            database.register_ctf_team(
                (
                    user_email,
                    *teammates,
                )
            )
            logging.info("Registered students {0}".format((user_email, *teammates)))
            await message.author.send(
                embed=utils.create_embed("You're all signed up. :)")
            )

    return


@client.register("!registrations", (0, 0), {"channel": False, "officer": True})
async def show_registrations(message, *args):
    """!registrations
    Prints a list of registered b00tcamp CTF teams."""

    records = database.get_all_ctf_registrations()
    for record in records:
        await message.author.send(str(record))

    return
