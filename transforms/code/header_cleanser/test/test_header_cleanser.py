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

import json
import os

import pyarrow as pa
import pyarrow.parquet as pq
from data_processing.test_support.transform import AbstractTableTransformTest
from data_processing.runtime.pure_python import PythonTransformLauncher
from dpk_header_cleanser.runtime import HeaderCleanserRuntime
from dpk_header_cleanser.transform import (
    COLUMN_KEY,
    COPYRIGHT_KEY,
    LICENSE_KEY,
    HeaderCleanserTransform,
)


class TestHeaderCleanserTransform(AbstractTableTransformTest):
    
    #Extends the super-class to define the test data for the tests defined there.
    #The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    
    def create_header_cleanser_test_fixture(
        self,
        column: str,
        license: bool,
        copyright: bool,
        input_dir: str,
        expected_output_dir: str,
    ):
        config = {
            COLUMN_KEY: column,
            LICENSE_KEY: license,
            COPYRIGHT_KEY: copyright,
        }
        input_df = pq.read_table(os.path.join(input_dir, "test1.parquet"))
        expected_output_df = pq.read_table(os.path.join(expected_output_dir, "test1.parquet"))
        with open(os.path.join(expected_output_dir, "metadata.json"), "r") as meta_file:
            expected_metadata = json.load(meta_file)
        expected_metadata_list = [expected_metadata, {}]
        return config, input_df, expected_output_df, expected_metadata_list

    def get_test_transform_fixtures(self):
        fixtures = []
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))
        column_name = "contents"
        launcher = PythonTransformLauncher(HeaderCleanserRuntime())

        # Case 1: both license & copyright
        config, input_df, expected_df, expected_metadata = self.create_header_cleanser_test_fixture(
            column_name, True, True,
            os.path.join(basedir, "input"),
            os.path.join(basedir, "expected", "license-and-copyright-local")
        )
        fixtures.append((launcher, config, input_df, expected_df, expected_metadata))

        # Case 2: license only
        config, input_df, expected_df, expected_metadata = self.create_header_cleanser_test_fixture(
            column_name, True, False,
            os.path.join(basedir, "input"),
            os.path.join(basedir, "expected", "license-local")
        )
        fixtures.append((launcher, config, input_df, expected_df, expected_metadata))

        # Case 3: copyright only
        config, input_df, expected_df, expected_metadata = self.create_header_cleanser_test_fixture(
            column_name, False, True,
            os.path.join(basedir, "input"),
            os.path.join(basedir, "expected", "copyright-local")
        )
        fixtures.append((launcher, config, input_df, expected_df, expected_metadata))

        return fixtures

