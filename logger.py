import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter


def init_log_config():
    logger = logging.getLogger(__name__)
    handler = TimedRotatingFileHandler(
        filename="log/contest_schedule.log",
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        delay=False,
    )
    formatter = Formatter(fmt="%(asctime)s [%(levelname)s][%(name)s]  %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


logger = init_log_config()
