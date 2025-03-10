## (C) Copyright IBM Corp. 2024.
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

from data_processing.runtime.pure_python.transform_launcher import (
    PythonTransformLauncher,
)
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from dpk_extreme_tokenized.common import (
    arrow_path_cli_param,
    contents_column_name_cli_param,
)
from dpk_extreme_tokenized.runtime import ExtremeTokenizedPythonTransformConfiguration


class TestExtremeTokenizedPythonTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))
        config = {
            arrow_path_cli_param: os.path.join(basedir, "input", "arrow"),
            contents_column_name_cli_param: "text",
        }
        input_dir = os.path.join(basedir, "input")
        expected_output_dir = os.path.join(basedir, "expected")
        launcher = PythonTransformLauncher(ExtremeTokenizedPythonTransformConfiguration())
        fixtures = [(launcher, config, input_dir, expected_output_dir)]
        return fixtures
