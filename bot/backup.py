from datetime import datetime, timedelta
from threading import Timer
from shutil import copy2
from .constants import DB_PATH, DB_BK_PATH
import time


def backup_db():
    now = datetime.today()
    tomorrow = now.replace(
        day=now.day, hour=1, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)
    timed = (tomorrow - now).total_seconds()

    t = Timer(timed, backup_db)
    t.start()
    copy2(DB_PATH, DB_BK_PATH.format(str(int(time.time()))))
