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
from data_processing.runtime.pure_python import PythonTransformLauncher
from dpk_header_cleanser.runtime import HeaderCleanserRuntime
from dpk_header_cleanser.transform import (
    COLUMN_KEY,
    LICENSE_KEY,
    COPYRIGHT_KEY,
)


class TestHeaderCleanserTransform(AbstractTransformLauncherTest):
    """
    Folder-based test for HeaderCleanser using PythonTransformLauncher.
    CLI arguments are passed via config dict (must be registered in HeaderCleanserConfiguration).
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))
        launcher = PythonTransformLauncher(HeaderCleanserRuntime())
        fixtures = []

        # Case 1: both license & copyright
        config1 = {
            "header_cleanser_contents_column_name": "contents",
            "header_cleanser_license": "true",
            "header_cleanser_copyright": "true",
        }
        fixtures.append((
            launcher,
            config1,
            os.path.join(basedir, "input"),
            os.path.join(basedir, "expected", "license-and-copyright-local")
        ))

        # Case 2: license only
        config2 = {
            "header_cleanser_contents_column_name": "contents",
            "header_cleanser_license": "true",
            "header_cleanser_copyright": "false",
        }
        fixtures.append((
            launcher,
            config2,
            os.path.join(basedir, "input"),
            os.path.join(basedir, "expected", "license-local")
        ))

        # Case 3: copyright only
        config3 = {
            "header_cleanser_contents_column_name": "contents",
            "header_cleanser_license": "false",
            "header_cleanser_copyright": "true",
        }
        fixtures.append((
            launcher,
            config3,
            os.path.join(basedir, "input"),
            os.path.join(basedir, "expected", "copyright-local")
        ))

        return fixtures