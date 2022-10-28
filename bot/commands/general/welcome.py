import discord
from discord.ext import commands

from bot import client


# @client.register("!welcome", (0, 0), {"dm": False})
@discord.guild_only()
@client.slash_command(
    name="welcome",
    description="Display the welcome message."
)
async def do_welcome(ctx: discord.ApplicationContext):
    """!welcome
    Send the welcome message"""

    # TODO: Make this configurable
    await ctx.respond(
        """Welcome to B01lers!
    
The best way to get started is to come every weekend, play, and ask questions along the way to see what skills you
need as you play. If you don't know something, learn it while you work or take the next week to learn if you can't
figure it out!

At the beginning of the semester, we stream a 'bootcamp' with training content on various categories. Those were
recorded: <https://youtube.com/c/b01lers>. We highly suggest watching those in chunks and working along with the
videos. You'll notice we use a docker container....just ignore that and use Ubuntu!

We have an internal CTF server for practice too: <https://internal.b01lers.com/home>. This has challenges from our
own past CTFs and bootcamps! Ask questions in #internal-ctf about that and we will help out!

If you're interested in learning certain categories or specific skills, there are a couple good learning resources:
* Cryptography: <https://cryptohack.org/> 
* Binary Exploitation: <https://pwn.college/> 
* Web: there's no obvious winner here that I know of... :( <https://overthewire.org/wargames/natas/ is okay,
  maybe someone else has a better resource

Picoctf is an easier competition with many categories that is always on and generally really good.

Overthewire bandit is a great intro to bash and thinking like a ctfer: https://overthewire.org/wargames/bandit/ once
it starts getting really weird it becomes less useful though. """
    )
