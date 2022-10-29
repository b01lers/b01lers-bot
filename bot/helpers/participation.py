import discord

from bot import logging, utils
from bot.constants import *
from bot.database.points import (
    add_points_to_user,
    get_user_yeets_on_message,
    add_transaction,
    get_recent_user_points_changes,
    get_all_user_points_changes,
)


def add_points(uid: int, point_delta: int) -> None:
    add_points_to_user(uid, point_delta)


def give_message_points(message):
    uid = message.author.id
    recent = get_recent_user_points_changes(uid, MESSAGE_TYPE(), MESSAGE_DELAY)
    today = get_recent_user_points_changes(uid, MESSAGE_TYPE(), SECONDS_PER_DAY)
    if recent == 0 and today < MAX_MESSAGE_POINTS_PER_DAY:
        add_transaction(uid, MESSAGE_TYPE(), POINTS_PER_MESSAGE)
        add_points(uid, POINTS_PER_MESSAGE)


def give_ctf_message_points(message):
    uid = message.author.id
    channel = message.channel.id
    recent = get_recent_user_points_changes(
        uid, CTF_MESSAGE_TYPE(channel), MESSAGE_DELAY
    )
    ctf_total = get_all_user_points_changes(uid, CTF_MESSAGE_TYPE(channel))
    if recent == 0 and ctf_total < MAX_CTF_POINTS_PER_CTF:
        add_transaction(uid, CTF_MESSAGE_TYPE(channel), POINTS_PER_CTF_MESSAGE)
        add_points(uid, POINTS_PER_CTF_MESSAGE)


def give_solve_points(uid, category, chaldata):
    add_transaction(uid, SOLVE_TYPE(category), POINTS_PER_SOLVE, chaldata)
    add_points(uid, POINTS_PER_SOLVE)

    logging.info(f"Gave user {uid} credit for solving {chaldata} in {category}.")


def give_yeet_points(message, reacter: int) -> None:
    """Grants a Discord points for reacting yeet to a message."""
    """FIXME: Fix this!"""
    uid = message.author.id
    ptype = YEET_TYPE(message.channel.id, message.id)

    if get_user_yeets_on_message(reacter, ptype[1]):
        add_transaction(uid, ptype, POINTS_PER_YEET, reacter)
        add_points(uid, POINTS_PER_YEET)


def give_voice_points(uid: int, minutes: int):
    if minutes == 0:
        return
    today = get_recent_user_points_changes(uid, VOICE_MINUTE_TYPE(), SECONDS_PER_DAY)
    if today < MAX_VOICE_POINTS_PER_DAY:
        points = min(minutes * POINTS_PER_VOICE_MINUTE, MAX_VOICE_POINTS_PER_DAY - today)
        add_transaction(uid, VOICE_MINUTE_TYPE(), points)
        add_points(uid, points)


def is_ctf_voice_channel(channel: discord.VoiceChannel) -> bool:
    return channel.category_id == LIVE_CTF_CATEGORY or "challenges" in channel.category.name.lower()
