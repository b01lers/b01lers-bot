import sqlite3
import itertools

from bot import logging
from bot.constants import *


def initialize_db():
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error:
        print("Could not open the database!")
        exit(1)
    c = conn.cursor()
    c.execute(CREATE_MEMBERS_TABLE)
    c.execute(CREATE_BOOTCAMP_REGISTER_TABLE)
    c.execute(CREATE_POINTS_TABLE)
    c.execute(CREATE_POINTS_LOG_TABLE)
    c.execute(CREATE_COMMAND_APPROVALS_TABLE)
    c.execute(CREATE_LINKS_TABLE)
    conn.commit()
    return conn, c


db, c = initialize_db()


def column_name_index(name, columns, record):
    return record[columns.index(name)]


def get_student_by_email(email):
    c.execute(GET_USER_BY_EMAIL, (email,))
    return c.fetchone()


def get_student_by_discord(uid):
    c.execute(GET_USER_BY_DISCORD, (uid,))
    return c.fetchone()


def verify_student(uid):
    c.execute(VERIFY_USER, (uid,))
    db.commit()
    logging.info("Updated student record in database")
    return


def add_student(record):
    c.execute(ADD_USER, record)
    db.commit()
    logging.info("Added student record to database {0}".format(record))
    return


### ctf registration ###


def get_ctf_teammember_registration(email):
    c.execute(
        GET_CTF_TEAMMEMBER_REGISTRATION,
        (
            email,
            email,
            email,
        ),
    )
    return c.fetchone()


def get_ctf_registration(email):
    c.execute(GET_CTF_REGISTRATION, (email,))
    return c.fetchone()


def get_all_ctf_registrations():
    return c.execute(GET_CTF_REGISTRATIONS)


def update_ctf_team(args):
    c.execute(CTF_UPDATE_TEAM, args)
    db.commit()
    return


def register_ctf_team(args):
    c.execute(CTF_REGISTER_TEAM, args)
    db.commit()
    return


### participation points ###


def add_user_to_points(uid):
    c.execute(ADD_USER_TO_POINTS, (uid,))
    db.commit()
    return


def log_point_transaction(uid, ptype, subtype, description, points, timestamp):
    c.execute(
        ADD_POINT_TRANSACTION, (uid, ptype, subtype, description, points, timestamp)
    )
    db.commit()
    return


def update_user_points(uid, points):
    add_user_to_points(uid)
    c.execute(UPDATE_USER_POINTS, (points, uid))
    db.commit()
    return


def get_points(uid):
    add_user_to_points(uid)
    return column_name_index(
        "points", POINTS_COLUMNS, c.execute(GET_USER_POINTS, (uid,)).fetchone()
    )


def get_recent_user_points(uid, ptype, mintime):
    if ptype[1]:
        return c.execute(
            GET_RECENT_USER_POINTS, (uid, ptype[0], ptype[1], mintime)
        ).fetchone()[0]
    else:
        return c.execute(
            GET_RECENT_USER_POINTS_NO_SUBTYPE, (uid, ptype[0], mintime)
        ).fetchone()[0]


def get_all_user_points(uid, ptype):
    if ptype[1]:
        return c.execute(GET_ALL_USER_POINTS, (uid, ptype[0], ptype[1])).fetchone()[0]
    else:
        return c.execute(GET_ALL_USER_POINTS_NO_SUBTYPE, (uid, ptype[0])).fetchone()[0]


def get_transaction_count(uid, ptype):
    return c.execute(GET_NUMBER_OF_TRANSACTIONS, (uid, ptype[0], ptype[1])).fetchone()[
        0
    ]


def get_user_yeets_on_message(uid, ptype):
    return c.execute(GET_USER_YEETS_ON_MESSAGE, (ptype[1], uid)).fetchall()


def get_top_scorers(num):
    return c.execute(GET_TOP_POINTS, (num,)).fetchall()


### command approvals ###


def add_new_approval(ptype, description):
    c.execute(ADD_NEW_APPROVAL, (ptype, description))
    db.commit()
    return c.lastrowid


def get_approval(aid):
    return c.execute(GET_APPROVAL, (aid,)).fetchone()


def update_approve_message(aid, msgid):
    c.execute(UPDATE_APPROVE_MESSAGE, (msgid, aid))
    db.commit()
    return


def accept_request(aid):
    c.execute(ACCEPT_REQUEST, (aid,))
    db.commit()
    return


def reject_request(aid):
    c.execute(REJECT_REQUEST, (aid,))
    db.commit()
    return


def purge_links():
    c.execute(PURGE_LINKS)
    db.commit()
    return


def insert_link(cid, url):
    c.execute(ADD_NEW_LINK, (cid, url))
    db.commit()
    return


def get_links(cid):
    return c.execute(GET_LINKS, (cid,)).fetchall()


def insert_links(cid, urls):
    c.executemany(ADD_NEW_LINK, zip(itertools.repeat(cid), urls))
    db.commit()
    return
