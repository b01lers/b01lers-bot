import base64
import json
import sys

try:
    CONFIG_FILE = open("config/config.json", "r")
    CONFIG_SECRET = open("config/config.secret", "r")
except:
    print(
        "Error: Could not open the config.secret file. Ensure the bot is run from the repo directory!",
        file=sys.stderr,
    )
    exit(1)

CONFIG = {**json.load(CONFIG_FILE), **json.load(CONFIG_SECRET)}
CONFIG_FILE.close()
CONFIG_SECRET.close()

DISCORD_TOKEN = CONFIG["security"]["discord-token"]
GITHUB_TOKEN = CONFIG["security"]["github-token"]

MAILGUN_API_KEY: str = CONFIG["mailgun"]["key"]
MAILGUN_API_BASE_URL: str = CONFIG["mailgun"]["url"]
MAIL_SENDER_EMAIL: str = CONFIG["mail"]["email"]
MAIL_SENDER_NAME: str = CONFIG["mail"]["name"]
MAIL_SUBJECT: str = CONFIG["mail"]["subject"]
MAIL_TEMPLATE: list[str] = CONFIG["mail"]["template"]

SECRET = base64.b64decode(CONFIG["security"]["secret"])
SECRET_PUB = CONFIG["security"]["secret-pub"]

GUILD = CONFIG["discord"]["guild"]
UPDATE_CHANNEL = CONFIG["discord"]["update-channel"]
GENERAL_CHANNEL = CONFIG["discord"]["general-channel"]
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
BLOCKED_DOMAINS = ["discord", "groupme"]

### REGEXES ###
HASH_REGEX = "[a-f0-9]{64}"
# URL_REGEX = """(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"


def MESSAGE_TYPE(subtype=""):
    return "message", subtype


def CTF_MESSAGE_TYPE(channel):
    return "ctfmessage", channel


def SOLVE_TYPE(category):
    return "solve", category


def YEET_TYPE(channel, message):
    return "yeet", str(channel) + ":" + str(message)


def MANUAL_POINTS_TYPE(officer):
    return "manual", officer


def VOICE_MINUTE_TYPE(subtype=""):
    return "voice", subtype


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
