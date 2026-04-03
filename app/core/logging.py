from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="INFO")


def get_logger():
    return logger
