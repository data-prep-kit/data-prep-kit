# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import os

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from dpk_yara.runtime import YaraPythonTransformConfiguration
from dpk_yara.transform import INPUT_COLUMN_KEY, RULES_DIR_KEY


class TestPythonYaraTransform(AbstractTransformLauncherTest):
    def get_test_transform_fixtures(self) -> list[tuple]:
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data"))
        rules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-rules"))
        fixtures = [
            (
                PythonTransformLauncher(YaraPythonTransformConfiguration()),
                {
                    INPUT_COLUMN_KEY: "binary_contents",
                    RULES_DIR_KEY: rules_dir,
                },
                basedir + "/input",
                basedir + "/expected",
            )
        ]
        return fixtures
