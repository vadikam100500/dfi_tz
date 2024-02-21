import logging
import sys

FORMATTER = logging.Formatter(fmt="%(levelname)s: %(asctime)s %(name)s: %(message)s",
                              datefmt='%Y-%m-%d %H:%M:%S')


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.propagate = False
    return logger
