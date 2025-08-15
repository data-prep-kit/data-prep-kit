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

import os

import pyarrow as pa
import pyarrow.parquet as pq

from data_processing.test_support.transform.table_transform_test import AbstractTableTransformTest
from data_processing.transform import get_transform_config
from dpk_dom2parquet.transform import (
    default_disable_tab_str,
    default_html_column_name,
    default_text_column_name,
    disable_tab_str_cli_param,
    html_column_name_cli_param,
    text_column_name_cli_param,
    CodeDocCleanerTransform,
    CodeDocCleanerTransformConfiguration,
)


class TestCodeDocCleanerTransform(AbstractTableTransformTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        fixtures = []

        transformConfig = CodeDocCleanerTransformConfiguration()

        basedir = "../test-data"
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), basedir))

        inputfile = os.path.join(basedir, "input", "test.parquet")
        table = pq.read_table(inputfile)

        expecteddir = os.path.join(basedir, "expected")

        # default setting
        cli_params = [
            f"--{disable_tab_str_cli_param}", str(default_disable_tab_str),
            f"--{html_column_name_cli_param}", default_html_column_name,
            f"--{text_column_name_cli_param}", default_text_column_name,
        ]
        config = get_transform_config(transformConfig, cli_params)
        transform = CodeDocCleanerTransform(config)

        expectedfile = os.path.join(expecteddir, "default", "test.parquet")
        expected_table = pq.read_table(expectedfile)

        fixtures.append((transform, [table], [expected_table], [{}, {}]))

        # disabled table structure setting
        cli_params = [
            f"--{disable_tab_str_cli_param}", "True",
            f"--{html_column_name_cli_param}", default_html_column_name,
            f"--{text_column_name_cli_param}", default_text_column_name,
        ]
        config = get_transform_config(transformConfig, cli_params)
        transform = CodeDocCleanerTransform(config)

        expectedfile = os.path.join(expecteddir, "dts", "test.parquet")
        expected_table = pq.read_table(expectedfile)

        fixtures.append((transform, [table], [expected_table], [{}, {}]))

        return fixtures