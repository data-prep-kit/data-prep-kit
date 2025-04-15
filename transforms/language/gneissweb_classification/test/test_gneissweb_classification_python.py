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
from dpk_gneissweb_classification.transform_python import ClassificationPythonTransformConfiguration


class TestPythonClassificationTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        cli_params = {
            "gcls_model_credential": os.environ.get('HF_READ_ACCESS_TOKEN', "PUT YOUR OWN HUGGINGFACE CREDENTIAL"),
            "gcls_model_file_name": ["fasttext_medical.bin"],
            "gcls_model_url":["ibm-granite/GneissWeb.Med_classifier"],
            "gcls_content_column_name": "text",
            "gcls_output_label_column_name": ["label_med"],
            "gcls_output_score_column_name": ["score"],
        }
    

        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))
        fixtures = []
        launcher = PythonTransformLauncher(ClassificationPythonTransformConfiguration())
        fixtures.append((launcher, cli_params, basedir + "/input", basedir + "/expected"))
        return fixtures

