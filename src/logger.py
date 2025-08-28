import logging

from src.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("kube-sherlock")
logger.addHandler(logging.StreamHandler())
