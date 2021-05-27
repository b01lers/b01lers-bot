import discord
import time
import json

from bot import logging
from bot import database, utils
from bot.constants import *


def add_points(uid, point_delta):
    total = database.get_points(uid)
    database.update_user_points(uid, total + point_delta)

    return


def give_message_points(message):
    timestamp = utils.get_time()
    uid = message.author.id
    recent = (
        database.get_recent_user_points(uid, MESSAGE_TYPE(), timestamp - MESSAGE_DELAY)
        or 0
    )
    today = (
        database.get_recent_user_points(
            uid, MESSAGE_TYPE(), timestamp - SECONDS_PER_DAY
        )
        or 0
    )
    if recent == 0 and today < MAX_MESSAGE_POINTS_PER_DAY:
        database.log_point_transaction(
            uid, *MESSAGE_TYPE(), "", POINTS_PER_MESSAGE, timestamp
        )
        add_points(uid, POINTS_PER_MESSAGE)

    return


def give_ctf_message_points(message):
    timestamp = utils.get_time()
    uid = message.author.id
    channel = message.channel.id
    recent = (
        database.get_recent_user_points(
            uid, CTF_MESSAGE_TYPE(channel), timestamp - MESSAGE_DELAY
        )
        or 0
    )
    ctf_total = database.get_all_user_points(uid, CTF_MESSAGE_TYPE(channel)) or 0
    if recent == 0 and ctf_total < MAX_CTF_POINTS_PER_CTF:
        database.log_point_transaction(
            uid, *CTF_MESSAGE_TYPE(channel), "", POINTS_PER_CTF_MESSAGE, timestamp
        )
        add_points(uid, POINTS_PER_CTF_MESSAGE)

    return


def give_solve_points(uid, category, chaldata):
    timestamp = utils.get_time()
    database.log_point_transaction(
        uid, *SOLVE_TYPE(category), chaldata, POINTS_PER_SOLVE, timestamp
    )
    add_points(uid, POINTS_PER_SOLVE)

    logging.info(f"Gave user {uid} credit for solving {chaldata} in {category}.")

    return


def give_yeet_points(message, reacter):
    timestamp = utils.get_time()
    uid = message.author.id
    if (
        len(
            database.get_user_yeets_on_message(
                reacter, YEET_TYPE(message.channel.id, message.id)
            )
        )
        == 0
    ):
        database.log_point_transaction(
            uid,
            *YEET_TYPE(message.channel.id, message.id),
            reacter,
            POINTS_PER_YEET,
            timestamp,
        )
        add_points(uid, POINTS_PER_YEET)

    return


def give_voice_points(member):
    timestamp = utils.get_time()
    uid = member.id
    today = (
        database.get_recent_user_points(
            uid, VOICE_MINUTE_TYPE(), timestamp - SECONDS_PER_DAY
        )
        or 0
    )
    if today < MAX_VOICE_POINTS_PER_DAY:
        database.log_point_transaction(
            uid, *VOICE_MINUTE_TYPE(), "", POINTS_PER_VOICE_MINUTE, timestamp
        )
        add_points(uid, POINTS_PER_VOICE_MINUTE)
