# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import logging
import os
import sys
import shutil
import traceback
from datetime import datetime
from typing import Iterable, Optional
from pythonjsonlogger.json import JsonFormatter
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from rich.text import Text

DPK_LOGGER_NAME = "dpk"
DPK_LOG_LEVEL = "DPK_LOG_LEVEL"
DPK_LOG_FILE = "DPK_LOG_FILE"
DPK_LOG_JSON_HANDLER = "DPK_LOG_JSON_HANDLER"
DPK_LOG_PROPAGATION = "DPK_LOG_PROPAGATION"
DEFAULT_LOG_LEVEL = "INFO"

# ------------------------------------------------------------------------------
# Rich console + theme
# ------------------------------------------------------------------------------

theme = Theme({
    "debug": "white",
    "info": "cyan dim",
    "warning": "yellow",
    "error": "red",
    "critical": "red",
    "time": "white",
    "logger": "dim",
    "message": "white",
    "extra": "magenta",
})

columns, _ = shutil.get_terminal_size(fallback=(200, 20))
console = Console(
    theme=theme,
    force_terminal=True,
    color_system="auto",
    width=columns,
)

# ------------------------------------------------------------------------------
# Custom Rich handler
# ------------------------------------------------------------------------------

class PrefectStyleRichHandler(RichHandler):
    level_map = {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warning",
        logging.ERROR: "error",
        logging.CRITICAL: "critical",
    }

    def emit(self, record: logging.LogRecord):
        try:
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            time_text = Text(ts, style="time")

            level_style = self.level_map.get(record.levelno, "info")
            level_text = Text(f" [{record.levelname}]", style=level_style)

            location = (
                f"{record.pathname}:{record.lineno}"
                if self.level <= logging.DEBUG or record.levelno >= logging.ERROR
                else f"{record.filename}:{record.lineno}"
            )
            logger_text = Text(f" {location} - ", style="logger")
            msg_text = Text(str(record.getMessage()), style="message")

            ignore = {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName",
                "processName", "process", "message", "asctime",
            }

            extras = {
                k: v for k, v in record.__dict__.items()
                if k not in ignore and v is not None
            }

            extras_text = Text()
            if extras:
                extras_text.append(
                    "\n" + "\n".join(f"{k}={v}" for k, v in extras.items()),
                    style="extra",
                )

            console.print(
                Text.assemble(
                    time_text,
                    level_text,
                    logger_text,
                    msg_text,
                    extras_text,
                )
            )

            if record.exc_info:
                # noinspection PyArgumentList
                traceback.print_exception(*record.exc_info)

        except Exception:
            self.handleError(record)

# ------------------------------------------------------------------------------
# Formatter factory
# ------------------------------------------------------------------------------

def create_json_formatter() -> JsonFormatter:
    return JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        rename_fields={
            "asctime": "time",
            "name": "logger",
            "levelname": "logLevel",
        },
    )

# ------------------------------------------------------------------------------
# Handler factories
# ------------------------------------------------------------------------------

def create_rich_handler(level: str) -> logging.Handler:
    handler = PrefectStyleRichHandler(
        console=console,
        tracebacks_extra_lines=3,
        tracebacks_suppress=[logging],
    )
    handler.setLevel(level)
    return handler


def create_json_stream_handler(level: str) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(create_json_formatter())
    return handler


def create_file_handler(path: str, level: str) -> logging.Handler:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    handler = logging.FileHandler(path, mode="a")
    handler.setLevel(level)
    handler.setFormatter(create_json_formatter())
    return handler

# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------

def get_dpk_logger(
    name: str = DPK_LOGGER_NAME,
    *,
    handlers: Optional[Iterable[logging.Handler]] = None,
    replace_handlers: bool = False,
) -> logging.Logger:
    """
    Create or retrieve a DPK logger.

    - If `handlers` is provided, they are used verbatim.
    - If `replace_handlers` is True, existing handlers are removed.
    - Otherwise, handlers are derived from environment variables.
    """

    log_level = os.environ.get(DPK_LOG_LEVEL, DEFAULT_LOG_LEVEL).upper()
    log_file = os.environ.get(DPK_LOG_FILE)
    use_json = os.environ.get(DPK_LOG_JSON_HANDLER, "").lower() in {"1", "true", "yes", "on"}
    propagate = os.environ.get(DPK_LOG_PROPAGATION, "").lower() in {"1", "true", "yes", "on"}

    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = propagate

    if replace_handlers:
        logger.handlers.clear()

    if handlers is not None:
        for handler in handlers:
            logger.addHandler(handler)
        return logger

    if logger.handlers:
        return logger  # already configured

    # Default env-based configuration
    if use_json:
        logger.addHandler(create_json_stream_handler(log_level))
    else:
        logger.addHandler(create_rich_handler(log_level))

    if log_file:
        logger.addHandler(create_file_handler(log_file, log_level))

    return logger
