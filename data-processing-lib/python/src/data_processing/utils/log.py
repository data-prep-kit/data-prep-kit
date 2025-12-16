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
from datetime import datetime
import shutil
import sys

from pythonjsonlogger.json import JsonFormatter
import os
import traceback

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
console = Console(theme=theme, force_terminal=True, color_system="auto", width=columns)

class PrefectStyleRichHandler(RichHandler):
    """
    RichHandler that builds the full log line (time, [LEVEL], fileName:lineno - message)
    with styles pulled from the console theme.
    """
    level_map = {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warning",
        logging.ERROR: "error",
        logging.CRITICAL: "critical",
    }

    def emit(self, record: logging.LogRecord):
        try:
            # --- Time ---
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            t = Text(ts, style="color(255)")

            # --- Level ---
            level_style = self.level_map.get(record.levelno, "info")
            lvl = Text(f" [{record.levelname}]", style=level_style)

            if self.level <= logging.DEBUG or record.levelno >= logging.ERROR:
                location = f"{record.pathname}:{record.lineno}"
            else:
                location = f"{record.filename}:{record.lineno}"

            # --- Logger + line ---
            logger_part = Text(f" {location} - ", style="logger")

            # --- Message ---
            msg = Text(str(record.getMessage()), style="color(255)")

            # --- Extras ---
            ignore = {
                "name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module",
                "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName", "processName", "process", "message",
                "asctime",
            }
            extras = [(k, v) for k, v in record.__dict__.items()
                      if k not in ignore and v is not None]

            extras_text = Text()
            if extras:
                extras_line = "\n" + "\n".join(f"{k}={v}" for k, v in extras)
                extras_text.append(extras_line, style="extra")

            # --- Assemble full line ---
            full_text = Text.assemble(t, lvl, logger_part, msg, extras_text)

            # Print log line
            console.print(full_text)

            # --- Print exception traceback (plain) ---
            if record.exc_info:
                traceback.print_exception(*record.exc_info)

        except Exception:
            self.handleError(record)

def get_dpk_logger(name = DPK_LOGGER_NAME ) -> logging.Logger:
    dpk_log_level = os.environ.get(DPK_LOG_LEVEL, DEFAULT_LOG_LEVEL).upper()
    dpk_log_file = os.environ.get(DPK_LOG_FILE, None)
    dpk_json_log_handler = os.environ.get(DPK_LOG_JSON_HANDLER, "").lower() in ("true", "1", "yes", "on")
    dpk_log_propagation = os.environ.get(DPK_LOG_PROPAGATION, "").lower() in ("true", "1", "yes", "on")

    logger = logging.getLogger(name)
    logger.propagate = dpk_log_propagation
    logger.setLevel(dpk_log_level)


    json_formatter = JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        rename_fields={"asctime": "time", "name": "logger", "levelname": "logLevel"}
    )

    def add_handler_once(handler, tag_name):
        if not any(getattr(h, "_tag", None) == tag_name for h in logger.handlers):
            handler._tag = tag_name
            logger.addHandler(handler)

    if dpk_json_log_handler :
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(dpk_log_level)
        stream_handler.setFormatter(json_formatter)
        add_handler_once(stream_handler, "dpk_stream_handler")
    else:
        rich_handler = PrefectStyleRichHandler(
            console=console,
            tracebacks_extra_lines=3,
            tracebacks_suppress=[logging],
            log_time_format="%H:%M:%S",
        )
        rich_handler.setLevel(dpk_log_level)
        add_handler_once(rich_handler, "dpk_rich_handler")
    if dpk_log_file:
        os.makedirs(os.path.dirname(dpk_log_file) or ".", exist_ok=True)
        file_handler = logging.FileHandler( filename=dpk_log_file, mode="a")
        file_handler.setFormatter(json_formatter)
        add_handler_once(file_handler, "dpk_file_handler")
    return logger


# Test logging
# logger = get_dpk_logger()
# logger.info("Hello, JSON world!", extra={"transaction_ID": "TRANSACTION999", "user_id": "USER999"})
#
# logger2 = get_dpk_logger()
# logger2.debug("debug message")
# logger2.info("info message")
# logger2.warning("warning message")
# logger.error("error message")
#
# try:
#     1/0
# except Exception as e:
#     logger2.exception(e)

