import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

from src.exception import MyException

# Get root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR: str = "logs"


def get_current_timestamp() -> str:
    """
    Get the current timestamp formatted as 'day-month-year_hour-minute-second'.

    Returns:
        str: Formatted current timestamp.

    Raises:
        MyException: If timestamp generation fails.
    """
    try:
        timestamp: str = datetime.now().strftime("%d-%b-%y_%H-%M-%S")
        return timestamp
    except Exception as e:
        raise MyException(e, sys) from e


LOG_FILE_FORMAT: str = f"{get_current_timestamp()}.log"

maxBytes: int = 5 * 1024 * 1024  # 5 MB
backupCount: int = 4

try:
    logs_dirpath: str = os.path.join(ROOT_DIR, LOGS_DIR)
    os.makedirs(logs_dirpath, exist_ok=True)
    log_filepath: str = os.path.join(logs_dirpath, LOG_FILE_FORMAT)
except Exception as e:
    raise MyException(e, sys) from e


def config_logger() -> None:
    """
    Configures the root logger with a colored console handler and a rotating file handler.
    """
    try:
        logger: logging.Logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        file_format: logging.Formatter = logging.Formatter(
            "[ %(asctime)s ] %(name)s - %(filename)s - %(levelname)s - %(message)s"
        )
        console_format: colorlog.ColoredFormatter = colorlog.ColoredFormatter(
            "[ %(asctime)s ] %(name)s - %(filename)s - %(log_color)s%(levelname)s%(reset)s - %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )

        if not logger.handlers:
            console_handler: logging.StreamHandler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)

            file_handler: RotatingFileHandler = RotatingFileHandler(
                log_filepath,
                maxBytes=maxBytes,
                backupCount=backupCount,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
    except Exception as e:
        raise MyException(e, sys) from e


config_logger()
