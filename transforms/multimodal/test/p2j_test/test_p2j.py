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

from data_processing.test_support import get_files_in_folder
from data_processing.utils import TransformUtils
from data_processing.test_support import get_tables_in_folder

from dpk_mm.p2j.transform import Parquet2JsonTransform

expected_metadata_list = [{}, {}]  # transform() result  # flush() result

from data_processing.test_support.transform.binary_transform_test import AbstractBinaryTransformTest

class TestProtoTransform(AbstractBinaryTransformTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test-data"))
        input_dir = os.path.join(test_data_dir, "j2p/expected")
        input_files = get_files_in_folder(input_dir, ".parquet")
        input_files = [(name, binary) for name, binary in input_files.items()]
        expected_metadata_list = [{}, {}]   # 2 (transform, flush) for each input file. only 1 input file for now.
        fixtures = []

        config = {"as_jsonl": False}
        expected_dir = os.path.join(test_data_dir, "p2j/expected/json")
        expected_files = get_files_in_folder(expected_dir, ".json")
        # Remove metadata.json
        tt = []
        for name,binary in expected_files.items():
            if not "metadata.json" in name:
                tt.append(
                    (binary, TransformUtils.get_file_extension(name)[1])
               )
        expected_files = tt
        expected_tables = get_tables_in_folder(expected_dir)
        fixtures.append(
            (Parquet2JsonTransform(config), input_files, expected_files, expected_metadata_list)
        )

        config = {"as_jsonl": True}
        expected_dir = os.path.join(test_data_dir, "p2j/expected/jsonl")
        expected_files = get_files_in_folder(expected_dir, ".jsonl")
        expected_files = [
            (binary, TransformUtils.get_file_extension(name)[1]) for name, binary in expected_files.items()
        ]
        expected_tables = get_tables_in_folder(expected_dir)
        fixtures.append(
            (Parquet2JsonTransform(config), input_files, expected_files, expected_metadata_list)
        )

        return fixtures
