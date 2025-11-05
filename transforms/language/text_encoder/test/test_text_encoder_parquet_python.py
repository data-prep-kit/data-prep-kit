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
from dpk_text_encoder.runtime import TextEncoderPythonTransformConfiguration

basedir = os.path.abspath(os.path.dirname(__file__))
input_dir = os.path.normpath(os.path.join(basedir, "../test-data/input"))
output_dir = os.path.normpath(os.path.join(basedir, "../output"))
expected_dir = os.path.normpath(os.path.join(basedir, "../test-data/expected_parquet"))


text_encoder_params = {
    "data_local_config": {"input_folder": input_dir, "output_folder": output_dir},
    "text_encoder_model_name": "ibm-granite/granite-embedding-small-english-r2",
    "text_encoder_embeddings_in_parquet": True,
    "text_encoder_content_column_name": "contents",
    "text_encoder_output_embeddings_column_name": "embeddings",
    "text_encoder_embedding_batch_size": 5,
}


class TestPythonTextEncoderTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        fixtures = []
        launcher = PythonTransformLauncher(TextEncoderPythonTransformConfiguration())
        fixtures.append(
            (
                launcher,
                text_encoder_params,
                input_dir,
                expected_dir,
                # this is added as a fixture to remove these columns from comparison
                ["embeddings"],
            ),
        )
        return fixtures
