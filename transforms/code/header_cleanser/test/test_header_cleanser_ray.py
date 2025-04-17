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

from dpk_header_cleanser.ray.runtime import HeaderCleanserRayTransformConfiguration
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from data_processing_ray.runtime.ray import RayTransformLauncher


class TestHeaderCleanserTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

def get_test_transform_fixtures(self) -> list[tuple]:
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))
    launcher = RayTransformLauncher(HeaderCleanserRayTransformConfiguration())
    fixtures = []

    # Case 1: both license & copyright
    cli1 = {
        "header_cleanser_contents_column_name": "contents",
        "header_cleanser_license": True,
        "header_cleanser_copyright": True,
        "run_locally": True,
    }
    fixtures.append((launcher, cli1, basedir + "/input", basedir + "/expected/license-and-copyright-local"))

    # Case 2: license only
    cli2 = {
        "header_cleanser_contents_column_name": "contents",
        "header_cleanser_license": True,
        "header_cleanser_copyright": False,
        "run_locally": True,
    }
    fixtures.append((launcher, cli2, basedir + "/input", basedir + "/expected/license-local"))

    # Case 3: copyright only
    cli3 = {
        "header_cleanser_contents_column_name": "contents",
        "header_cleanser_license": False,
        "header_cleanser_copyright": True,
        "run_locally": True,
    }
    fixtures.append((launcher, cli3, basedir + "/input", basedir + "/expected/copyright-local"))

    return fixtures