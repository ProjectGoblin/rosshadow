import logging
import sys


def generate_handler(name):
    """
    Just wrapping original `logging` module for now.
    @param name:
    @return:
    """
    out = logging.StreamHandler(sys.stdout)
    out.setFormatter(logging.Formatter('[%(name)s][%(levelname)05s] %(message)s'))
    logger = logging.getLogger(name)
    logger.addHandler(out)
    logger.setLevel(logging.DEBUG)
    return logger
