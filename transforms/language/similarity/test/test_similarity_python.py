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

import os
import sys
import tempfile

import pyarrow.parquet as pq
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.utils import ParamsUtils

from dpk_similarity.transform import ES_ENDPOINT_CLI_PARAM
from dpk_similarity.transform_python import SimilarityPythonTransformConfiguration

# Reuse the representation-tolerant table comparison defined alongside the direct test.
from test_similarity import assert_tables_equivalent


class TestPythonSimilarityTransform:
    """
    Run the similarity transform through the Python launcher and compare the produced
    parquet against the expected fixture using a representation-tolerant comparison.

    We do not use AbstractTransformLauncherTest's directory comparison here because it
    asserts exact pyarrow schema equality, which is unstable for this transform: it
    round-trips data through pandas, so the output `contents` type (string vs
    large_string) and list field naming depend on the installed pyarrow/pandas versions.
    """

    def test_transform(self):
        src_file_dir = os.path.abspath(os.path.dirname(__file__))
        input_dir = os.path.join(src_file_dir, "../test-data/input")
        expected_dir = os.path.join(src_file_dir, "../test-data/expected")

        with tempfile.TemporaryDirectory(prefix="similarity", dir="/tmp") as temp_dir:
            local_config = {"input_folder": input_dir, "output_folder": temp_dir}
            sys.argv = ParamsUtils.dict_to_req(
                {
                    "data_local_config": local_config,
                    ES_ENDPOINT_CLI_PARAM: None,
                }
            )
            launcher = PythonTransformLauncher(SimilarityPythonTransformConfiguration())
            assert launcher.launch() == 0, "Launcher did not complete successfully"

            for fname in os.listdir(expected_dir):
                if not fname.endswith(".parquet"):
                    continue
                produced = pq.read_table(os.path.join(temp_dir, fname))
                expected = pq.read_table(os.path.join(expected_dir, fname))
                assert_tables_equivalent(produced, expected)
