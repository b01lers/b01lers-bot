import time

import discord

from bot.constants import ERROR_COLOR, EMBED_COLOR


def get_epoch_timestamp() -> int:
    return int(time.time())


def create_embed(message, title=None, error=False):
    if title:
        return discord.Embed(
            title=title,
            description=message,
            color=ERROR_COLOR if error else EMBED_COLOR,
        )
    else:
        return discord.Embed(
            description=message, color=ERROR_COLOR if error else EMBED_COLOR
        )
