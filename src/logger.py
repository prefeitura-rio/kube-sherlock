import logging

from .settings import settings

logger = logging.getLogger(settings.LOGGER_NAME)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt=settings.LOG_FORMAT, datefmt=settings.DATE_FORMAT))
logger.addHandler(handler)
