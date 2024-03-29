import logging

from bot.helpers import participation
from bot.constants import *


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Setup logging
import logging

discord_logger = logging.getLogger()
discord_logger.setLevel(logging.DEBUG)
discord_logger.addHandler(InterceptHandler())

from loguru import logger

logger.add(
    "logs/bot-{time}.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
)

# Bootstrap
from bot.bot import client

# Load up listeners
from bot.listeners import *

# Load up commands
from bot.commands import *

# Load up scheduled tasks
from bot.tasks import *

logging.info("Initialization completed.")
