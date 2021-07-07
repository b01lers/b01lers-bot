import re, json, base64, hashlib

try:
    CONFIG_FILE = open(
        "data/config.json", "r"
    )
    CONFIG_SECRET = open(
        "data/config.secret", "r"
    )
except:
    print(
        "Error: Could not open the config.secret file. Ensure the bot is run from the repo directory!"
    )
    exit(1)

CONFIG = {**json.load(CONFIG_FILE), **json.load(CONFIG_SECRET)}
CONFIG_FILE.close()
CONFIG_SECRET.close()

DISCORD_TOKEN = CONFIG["security"]["discord-token"]
GITHUB_TOKEN = CONFIG["security"]["github-token"]
MAILGUN_API_KEY = CONFIG["mailgun"]["key"]
MAILGUN_API_BASE_URL = CONFIG["mailgun"]["url"]
SECRET = base64.b64decode(CONFIG["security"]["secret"])
SECRET_PUB = CONFIG["security"]["secret-pub"]
GUILD = CONFIG["discord"]["guild"]
UPDATE_CHANNEL = CONFIG["discord"]["update-channel"]
APPROVAL_CHANNEL = CONFIG["discord"]["approval-channel"]
LIVE_CTF_CATEGORY = CONFIG["discord"]["ctf-category"]
ARCHIVE_CATEGORY = CONFIG["discord"]["archive-category"]
DB_PATH = CONFIG["files"]["database-path"]
DB_BK_PATH = CONFIG["files"]["backup-path"]


### CONSTANTS ###
EMBED_COLOR = 0xC1000C
ERROR_COLOR = 0x203354
SECONDS_PER_DAY = 86400
CTF_CHAL_CATEGORIES = ("re", "pwn", "web", "crypto", "forensics", "other")
APPROVAL_VALUES = ("PENDING", "ACCEPTED", "REJECTED")

### REGEXES ###
HASH_REGEX = "[a-f0-9]{64}"
# URL_REGEX = """(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

### SQL Prepared commands ###
MEMBERS_COLUMNS = ("name", "alias", "email", "token", "validated")
BOOTCAMP_COLUMNS = (
    "registered_email",
    "teammate_one",
    "teammate_two",
    "teammate_three",
)
POINTS_COLUMNS = ("uid", "points")
TRANSACTIONS_COLUMNS = ("tid", "uid", "type", "channel", "point_delta", "timestamp")
APPROVALS_COLUMNS = ("aid", "type", "description", "approved", "approve_message")

CREATE_MEMBERS_TABLE = """CREATE TABLE IF NOT EXISTS members 
    (name text, alias text, email text primary key, token text, validated integer)"""
ADD_USER = (
    """INSERT INTO members(name, alias, email, token, validated) VALUES(?,?,?,?,?)"""
)
VERIFY_USER = """UPDATE members SET validated = 1 WHERE alias IN (SELECT alias FROM members WHERE alias = ? LIMIT 1)"""
GET_USER_BY_EMAIL = """SELECT * FROM members WHERE email=?"""
GET_USER_BY_DISCORD = """SELECT * FROM members WHERE alias=?"""

CREATE_BOOTCAMP_REGISTER_TABLE = """CREATE TABLE IF NOT EXISTS bootcamp
    (registered_email text, teammate_one text, teammate_two text, teammate_three text)"""
CTF_REGISTER_TEAM = """INSERT INTO bootcamp(registered_email, teammate_one, teammate_two, teammate_three) VALUES(?,?,?,?)"""
CTF_UPDATE_TEAM = """UPDATE bootcamp SET registered_email = ?, teammate_one = ?, teammate_two = ?, teammate_three = ? WHERE registered_email IN
    (SELECT registered_email FROM bootcamp WHERE registered_email = ? LIMIT 1)"""
GET_CTF_REGISTRATION = """SELECT * FROM bootcamp WHERE registered_email = ?"""
GET_CTF_TEAMMEMBER_REGISTRATION = """SELECT * FROM bootcamp WHERE teammate_one = ? OR teammate_two = ? OR teammate_three = ?"""
GET_CTF_REGISTRATIONS = """SELECT * from bootcamp"""

### PARTICIPATION SQL ###
CREATE_POINTS_TABLE = """CREATE TABLE IF NOT EXISTS points
    (uid text primary key, points int, UNIQUE(uid))"""
CREATE_POINTS_LOG_TABLE = """CREATE TABLE IF NOT EXISTS transactions
    (tid integer primary key asc, uid text, type text, subtype text, description text, point_delta int, timestamp bigint)"""
ADD_USER_TO_POINTS = """INSERT OR IGNORE INTO points(uid, points) VALUES(?, 0)"""
ADD_POINT_TRANSACTION = """INSERT INTO transactions(uid, type, subtype, description, point_delta, timestamp) VALUES(?,?,?,?,?,?)"""
UPDATE_USER_POINTS = """UPDATE points SET points=? WHERE uid=?"""
GET_USER_POINTS = """SELECT * FROM points WHERE uid=?"""

GET_TOP_POINTS = """SELECT * FROM points ORDER BY points DESC LIMIT ?"""

GET_RECENT_USER_POINTS = """SELECT SUM(point_delta) FROM transactions WHERE uid=? AND type=? AND subtype=? AND timestamp>?"""
GET_RECENT_USER_POINTS_NO_SUBTYPE = """SELECT SUM(point_delta) FROM transactions WHERE uid=? AND type=? AND timestamp>?"""
GET_ALL_USER_POINTS = (
    """SELECT SUM(point_delta) FROM transactions WHERE uid=? AND type=? AND subtype=?"""
)
GET_ALL_USER_POINTS_NO_SUBTYPE = (
    """SELECT SUM(point_delta) FROM transactions WHERE uid=? AND type=?"""
)
GET_NUMBER_OF_TRANSACTIONS = (
    """SELECT COUNT(*) FROM transactions WHERE uid=? AND type=? AND subtype=?"""
)
GET_USER_YEETS_ON_MESSAGE = (
    """SELECT * FROM transactions WHERE type="yeet" AND subtype=? AND description=?"""
)

### COMMAND APPROVAL SQL ###
CREATE_COMMAND_APPROVALS_TABLE = """CREATE TABLE IF NOT EXISTS approvals
    (aid integer primary key asc, type text, description text, approved integer, approve_message text)"""
ADD_NEW_APPROVAL = (
    """INSERT INTO approvals(type, description, approved) VALUES(?, ?,0)"""
)
UPDATE_APPROVE_MESSAGE = """UPDATE approvals SET approve_message=? WHERE aid=?"""
ACCEPT_REQUEST = """UPDATE approvals SET approved=1 WHERE aid=?"""
REJECT_REQUEST = """UPDATE approvals SET approved=-1 WHERE aid=?"""
GET_APPROVAL = """SELECT * FROM approvals WHERE aid=?"""

### LINK GRABBING SQL ###
CREATE_LINKS_TABLE = """CREATE TABLE IF NOT EXISTS links
    (lid integer primary key, cid integer, link text)"""
ADD_NEW_LINK = """INSERT INTO links(cid, link) VALUES(?, ?)"""
GET_LINKS = """SELECT link FROM links WHERE cid=?"""
PURGE_LINKS = """DELETE FROM links"""


def MESSAGE_TYPE(subtype=""):
    return ("message", subtype)


def CTF_MESSAGE_TYPE(channel):
    return ("ctfmessage", channel)


def SOLVE_TYPE(category):
    return ("solve", category)


def YEET_TYPE(channel, message):
    return ("yeet", str(channel) + ":" + str(message))


def MANUAL_POINTS_TYPE(officer):
    return ("manual", officer)


def VOICE_MINUTE_TYPE(subtype=""):
    return ("voice", subtype)


### PARTICIPATION POINTS ###
POINTS_PER_MESSAGE = 1
POINTS_PER_CTF_MESSAGE = 3
MESSAGE_DELAY = 30  # in seconds
MAX_MESSAGE_POINTS_PER_DAY = 20
MAX_CTF_POINTS_PER_CTF = 300
POINTS_PER_YEET = 1

POINTS_PER_VOICE_MINUTE = 1
POINTS_PER_CTF_VOICE_MINUTE = 2
MAX_VOICE_POINTS_PER_DAY = 50
MAX_CTF_VOICE_POINTS_PER_DAY = 100

POINTS_PER_SOLVE = 100
POINTS_PER_WRITEUP = 200

### ENOJIS ###
EMOJINUMBERS = (
    "0️⃣",
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "🇦",
    "🇧",
    "🇨",
    "🇩",
    "🇪",
    "🇫",
)
DEFAULT_REACTIONS = ("👍", "👎", "🤷")
WAITING_EMOJI = "⏳"
DONE_EMOJI = "✅"
CANCEL_EMOJI = "❌"
