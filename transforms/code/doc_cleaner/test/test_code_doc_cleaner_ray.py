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

from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from data_processing_ray.runtime.ray import RayTransformLauncher
from dpk_doc_cleaner.transform import (
    default_disable_tab_str,
    default_html_column_name,
    default_text_column_name,
    disable_tab_str_cli_param,
    html_column_name_cli_param,
    text_column_name_cli_param,
)
from dpk_doc_cleaner.ray.runtime import (
    CodeDocCleanerRayTransformConfiguration,
)


class TestRayCodeDocCleanerTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        fixtures = []
        launcher = RayTransformLauncher(CodeDocCleanerRayTransformConfiguration())

        basedir = "../test-data"
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), basedir))

        inputdir = os.path.join(basedir, "input")
        expecteddir = os.path.join(basedir, "expected")

        # default setting
        cli_params = {
            "run_locally": True,
            disable_tab_str_cli_param: default_disable_tab_str,
            html_column_name_cli_param: default_html_column_name,
            text_column_name_cli_param: default_text_column_name,
        }
        fixtures.append((launcher, cli_params, inputdir, os.path.join(expecteddir, "default")))

        # disabled table structure setting
        cli_params = {
            "run_locally": True,
            disable_tab_str_cli_param: True,
            html_column_name_cli_param: default_html_column_name,
            text_column_name_cli_param: default_text_column_name,
        }
        fixtures.append((launcher, cli_params, inputdir, os.path.join(expecteddir, "dts")))

        return fixtures
