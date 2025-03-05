# from gin/common/logging.py

"""
Module for holding logging information
"""

import logging.handlers
import os
import logging
from pathlib import Path


# ANSI SGR control codes for text formatting
TEXT = {
    "DEFAULT": "\x1b[0m",
    "BOLD": "\x1b[1m",
    "BOLD_OFF": "\x1b[22m",
    "UNDERLINE": "\x1b[4m",
    "UNDERLINE_OFF": "\x1b[24m",
    "DEFAULT_COLOR": "\x1b[39m",
    "DEFAULT_BG_COLOR": "\x1b[49m",
    "RED": "\x1b[31m",
    "YELLOW": "\x1b[33m",
    "GREEN": "\x1b[32m",
    "CYAN": "\x1b[36m",
    "BLUE": "\x1b[34m",
    "MAGENTA": "\x1b[35m",
    "BLACK": "\x1b[30m",
    "WHITE": "\x1b[37m",
    "BG_RED": "\x1b[41m",
    "BG_YELLOW": "\x1b[43m",
    "BG_GREEN": "\x1b[42m",
    "BG_CYAN": "\x1b[46m",
    "BG_BLUE": "\x1b[44m",
    "BG_MAGENTA": "\x1b[45m",
    "BG_BLACK": "\x1b[40m",
    "BG_WHITE": "\x1b[47m",
}


class Logging:
    """
    Task-dependent logger names
    """

    # logging package requires logger names must be strings, so this class
    # must not inherit from enum
    BASE = "base"
    LLM = "llm"
    AGENTIC_WORKFLOW = "agentic_workflow"
    TOOL_CALLING = "tool_calling"


class Formatter(logging.Formatter):
    """
    Custom log formatting for GIN modules.
    """

    def __init__(self):
        # Log message format
        msg_fmt = f"{TEXT['BOLD']}%(name)s:%(levelname)s:{TEXT['BOLD_OFF']}%(message)s"

        # Dictionary of formatters that add color codes (based on log level)
        self.formatters: dict[int, logging.Formatter] = {
            logging.DEBUG: logging.Formatter(TEXT["BLUE"] + msg_fmt + TEXT["DEFAULT"]),
            logging.INFO: logging.Formatter(TEXT["GREEN"] + msg_fmt + TEXT["DEFAULT"]),
            logging.WARNING: logging.Formatter(
                TEXT["YELLOW"] + msg_fmt + TEXT["DEFAULT"]
            ),
            logging.ERROR: logging.Formatter(TEXT["RED"] + msg_fmt + TEXT["DEFAULT"]),
            logging.CRITICAL: logging.Formatter(
                TEXT["BG_RED"] + TEXT["BLACK"] + msg_fmt + TEXT["DEFAULT"]
            ),
        }

        super().__init__()

    def format(self, record: logging.LogRecord):
        """
        Format the specified record as text, while adding ANSI color codes
        based on log level.
        """
        # Get the log formatter based on log level
        formatter = self.formatters[record.levelno]
        return formatter.format(record)


def prep_loggers(log_level: str, default_log_level: str = "WARNING") -> int:
    """
    Prepare the GIN loggers.

    Args:
        log_level (str): Level(s) to set loggers to. This is a comma separated
            list (without spaces) of levels for each logger in the format:
            LOGGER_NAME1=LEVEL1,LOGGER_NAME2=LEVEL2,DEFAULT_LEVEL
            The default level can be specified anywhere (or nowhere) and will
            be identified by the lack of a '=' symbol.
        default_log_level (str, optional): Default logging level, if not
            otherwise specified in log_level. Defaults to "WARNING".

    Returns:
        int: Error code (returns 0 for no error, 1 otherwise)
    """
    log_levels = {"_default": default_log_level}
    for logger_level_pair in log_level.split(","):
        if "=" in logger_level_pair:
            logger_name, level = logger_level_pair.split("=")
        else:
            # This is not a pair, but a default level
            logger_name = "_default"
            level = logger_level_pair
        logger_attrs = [attr for attr in dir(Logging) if attr[0] != "_"]
        logger_names = list(map(lambda x: getattr(Logging, x), logger_attrs))
        if logger_name not in logger_names and logger_name != "_default":
            logging.error("Invalid logger name: %s", logger_name)
            logging.error("Must be one of: %s", logger_names)
            return 1
        if level not in logging._nameToLevel:
            logging.error("Invalid logging level: %s", level)
            logging.error(
                "Must be one of: %s",
                str(list(logging._nameToLevel.keys()))[1:-1],
            )
            return 1
        log_levels[logger_name] = level

    # Set up loggers
    logging.basicConfig()
    # Set the default logging level across all loggers
    logging.getLogger().setLevel(log_levels["_default"])
    # Get handler for custom formatting, and apply to all GIN loggers
    handler = logging.StreamHandler()
    handler.setFormatter(Formatter())
    for logger_attr in [attr for attr in dir(Logging) if attr[0] != "_"]:
        logger_name = getattr(Logging, logger_attr)
        logger = logging.getLogger(logger_name)
        # Check if there is an environment override for any of the log files
        logger_env_override = f"{logger_name}_log_path".upper()
        logger_path = os.environ.get(logger_env_override, None)
        if logger_path:
            path = Path(logger_path)
            log_dir = path.parent
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = logging.handlers.RotatingFileHandler(
                logger_path, maxBytes=102400, backupCount=5
            )
        # Apply handler to logger
        logger.addHandler(handler)
        # Only use custom formatter
        logger.propagate = False
        if logger_name in log_levels:
            # Set the custom logging level
            logger.setLevel(log_levels[logger_name])
        if logger_path:
            # Make sure that the log level is set to INFO or finer
            if logger.getEffectiveLevel() > logging.INFO:
                logger.setLevel(logging.INFO)

    return 0
