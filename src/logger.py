import logging
import os

from .constants import constants

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", constants.DEFAULT_LOG_LEVEL)),
    format=constants.DEFAULT_LOG_FORMAT,
    datefmt=constants.DEFAULT_DATE_FORMAT,
)

logger = logging.getLogger(constants.LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
