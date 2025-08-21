import logging

from src.settings import Settings

logging.basicConfig(
    level=getattr(logging, Settings().LOG_LEVEL),
    format="[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("kube-sherlock")

