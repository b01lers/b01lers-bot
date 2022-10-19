import logging
import time
from shutil import copy2

from discord.ext import tasks

from bot.constants import DB_PATH, DB_BK_PATH


@tasks.loop(hours=1)
async def backup_db():
    """Backup database every one hour."""
    copy2(DB_PATH, DB_BK_PATH.format(str(int(time.time()))))
    logging.info("Database backed up.")


# Must start it immediately.
backup_db.start()
