import os
import logging
import sys

# logging setup
def logging_setup(file_name: str, folder_name: str = "logs"):
    # makes sure the folder exists
    os.makedirs(folder_name, exist_ok=True)

    # init logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # file handler
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(folder_name + "/" + file_name + ".log")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # stream handler
    stream_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    return logger


# logger
logger = logging_setup(file_name="game")
