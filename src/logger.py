import logging
import os

from .constants import constants

logger = logging.getLogger(constants.LOGGER_NAME)
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", constants.DEFAULT_LOG_LEVEL)))

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt=constants.DEFAULT_LOG_FORMAT, datefmt=constants.DEFAULT_DATE_FORMAT))
logger.addHandler(handler)
