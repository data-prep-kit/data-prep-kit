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
from dpk_code_quality.runtime import CodeQualityRuntime

class TestCodeQualityTransform(AbstractTransformLauncherTest):

    def get_test_transform_fixtures(self):
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../transforms/universal/code_quality/test-data"))
        fixtures = []
        transform_config = {
            "run_locally": True,
            "code_quality_params": {
                "contents_column_name": "contents",
                "language_column_name": "language",
                "tokenizer": "codeparrot/codeparrot",
                "hf_token": os.getenv("HF_TOKEN"),
            }
        }
        launcher = PythonTransformLauncher(CodeQualityRuntime())
        fixtures.append((launcher, transform_config, 
                         basedir + "/input", 
                         basedir + "/expected"))
        return fixtures
