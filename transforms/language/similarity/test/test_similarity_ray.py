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
# from data_processing.test_support import get_tables_in_folder
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from data_processing_ray.runtime.ray import RayTransformLauncher
from dpk_similarity.transform import  ES_ENDPOINT_KEY
from dpk_similarity.ray.transform import SimilarityRayTransformRuntimeConfiguration

class TestRaySimilarityTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """
    ## Unit Test should be run from the test folder
    ## cd test && pytest .    
    def get_test_transform_fixtures(self) -> list[tuple]:
        
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data"))

        cli_params = {
            "run_locally": True,
        }
        fixtures = []
        launcher = RayTransformLauncher(SimilarityRayTransformRuntimeConfiguration())
        fixtures.append((launcher, cli_params, os.path.join(basedir, "input"), os.path.join(basedir, "expected")))
        return fixtures
