"""
This is a file that defines logging for router-connectedness.
It is a separate file for Global logging.
"""
import logging
from logging.handlers import RotatingFileHandler

def log():
    """Set up Logging, handler for both console and file.
    When application is finished, console logging will be removed
    """
    logger = logging.getLogger() #The root
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        'router_connected.log',
        mode='a',
        maxBytes=100000,
        backupCount=1,
        encoding=None,
        delay=0)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
