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
from pythonjsonlogger.json import JsonFormatter
import os

DPK_LOGGER_NAME = "dpk"


def get_dpk_logger() -> logging.Logger:
    dpk_log_level = os.environ.get("DPK_LOG_LEVEL", "INFO")
    dpk_log_file = os.environ.get("DPK_LOG_FILE", None)
    dpk_log_propagation = os.environ.get("DPK_LOG_PROPAGATION", False)

    logger = logging.getLogger(DPK_LOGGER_NAME)
    logger.propagate = dpk_log_propagation
    logger.setLevel(dpk_log_level.upper())


    formatter = JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        rename_fields={"asctime": "time", "name": "logger", "levelname": "logLevel"}
    )

    def add_handler_once(handler_cls, tag_name, **kwargs):
        if not any(getattr(h, "_tag", None) == tag_name for h in logger.handlers):
            handler = handler_cls(**kwargs)
            handler.setFormatter(formatter)
            handler._tag = tag_name  # custom attribute to identify it later
            logger.addHandler(handler)

    add_handler_once(logging.StreamHandler, "stream_handler")
    if dpk_log_file:
        os.makedirs(os.path.dirname(dpk_log_file) or ".", exist_ok=True)
        add_handler_once(logging.FileHandler, "file_handler", filename=dpk_log_file, mode="a")
    return logger


# Test logging
# logger = get_dpk_logger()
# logger.info("Hello, JSON world!", extra={"transaction_ID": "TRANSACTION999", "user_id": "USER999"})
#
# logger2 = get_dpk_logger()
# logger2.debug("debug message")
# logger2.info("info message")
# logger2.warning("warning message")
# logger2.error("error message")
