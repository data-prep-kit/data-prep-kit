# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2025.
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

import json
import logging
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from data_processing.utils.log import get_dpk_logger, DPK_LOG_FILE, DPK_LOG_LEVEL, DPK_LOG_JSON_HANDLER


class TestDPKLogger():

    @patch.dict(os.environ, {DPK_LOG_LEVEL: "DEBUG"})
    def test_debug_message_output(self, capsys):
        """
        Verify that:
        1. Logger level matches DPK_LOG_LEVEL
        2. A debug message is actually emitted
        """

        logger = get_dpk_logger("dpk_test")
        expected_level = getattr(logging, os.environ["DPK_LOG_LEVEL"].upper(), logging.INFO)
        assert logger.level == expected_level, "Logger level does not match DPK_LOG_LEVEL"

        test_message = "debug_test_message"
        logger.debug(test_message)

        captured = capsys.readouterr()
        output = captured.out + captured.err  # combine stdout + stderr
        assert test_message in output

    def test_logger_writes_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_path = os.path.join(tmp, "log.txt")

            with patch.dict(os.environ, {DPK_LOG_FILE: temp_path}):
                logger = get_dpk_logger()
                logger.info("File test")

                with open(temp_path, "r") as f:
                    content = f.read()

                assert "File test" in content
            os.remove(temp_path)

    @patch.dict(os.environ, {DPK_LOG_LEVEL: "DEBUG", DPK_LOG_JSON_HANDLER: "true"})
    def test_dpk_logger_two_json_handlers(self, capsys):
        """DPK_LOG_JSON_HANDLER=true → output must be JSON formatted."""
        with tempfile.TemporaryDirectory() as tmp:
            temp_path = os.path.join(tmp, "log.txt")

            with patch.dict(os.environ, {DPK_LOG_FILE: temp_path}):
                logger = get_dpk_logger()
                # Remove all old handlers
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()

                logger = get_dpk_logger()
                test_message = "json test"
                logger.debug(test_message)

                captured = capsys.readouterr()
                stream_output = captured.out.strip()
                assert stream_output, "Stream (stdout) output is empty"
                print("\nSTREAM OUTPUT:", repr(stream_output))
                try:
                    stream_data = json.loads(stream_output)
                except json.JSONDecodeError as e:
                    raise AssertionError(f"Stream handler produced invalid JSON: {e}\nOutput: {stream_output!r}")

                path = Path(temp_path)
                assert path.exists(), "Expected JSON file to be created"
                file_output = path.read_text().strip()
                assert file_output, "File log is empty"
                print("FILE OUTPUT:", repr(file_output))
                try:
                    file_data = json.loads(file_output)
                except json.JSONDecodeError as e:
                    raise AssertionError(f"File handler produced invalid JSON: {e}\nOutput: {file_output!r}")

                for data in (file_data, stream_data):
                    assert isinstance(data, dict), f"Expected dict, got {type(data)}"
                    assert data.get("message", data.get("msg")) == test_message
                    assert any(k in data for k in ("time", "timestamp")), \
                        f"Missing timestamp field in {data}"

                assert file_data == stream_data, "Handlers produced different JSON outputs"
            os.remove(temp_path)
