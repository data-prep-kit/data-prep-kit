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

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from dpk_folder2parquet.runtime import Folder2ParquetPythonTransformConfiguration


class TestPythonF2PTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        cli_params = {
            "data_files_to_use": [".txt", ".zip"],
        }
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))
        fixtures = []
        # this is added as a fixture to remove these columns from comparison
        ignore_columns = ["document_uuid"]
        launcher = PythonTransformLauncher(Folder2ParquetPythonTransformConfiguration())
        fixtures.append((launcher, cli_params, basedir + "/input", basedir + "/expected", ignore_columns))
        fixtures.append(
            (
                launcher,
                {**cli_params, "f2p_fewer_parquets": True},
                basedir + "/input",
                basedir + "/expected2",
                ignore_columns,
            )
        )
        return fixtures
