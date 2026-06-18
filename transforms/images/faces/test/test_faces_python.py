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

import pytest
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)

from dpk_faces.runtime import FacesPythonTransformConfiguration


# Placeholder value used when no real HuggingFace token is supplied via the environment.
_HF_TOKEN_PLACEHOLDER = "PUT YOUR OWN HUGGINGFACE CREDENTIAL"


class TestRayProtoTransform(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    # This test downloads the deepghs/yolo-face model from the HuggingFace Hub at runtime,
    # which requires both outbound network and a valid HF token. When HF_READ_ACCESS_TOKEN
    # is not provided (e.g. CI without the secret, or fork PRs) the download fails and the
    # transform produces no output. Skip in that case rather than failing spuriously; the
    # test still runs wherever the token is configured.
    @pytest.mark.skipif(
        os.environ.get("HF_READ_ACCESS_TOKEN", _HF_TOKEN_PLACEHOLDER) == _HF_TOKEN_PLACEHOLDER,
        reason="HF_READ_ACCESS_TOKEN not set; requires HuggingFace access to download the face model.",
    )
    def test_transform(self, launcher, cli_params, in_table_path, expected_out_table_path, ignore_columns):
        super().test_transform(launcher, cli_params, in_table_path, expected_out_table_path, ignore_columns)

    def get_test_transform_fixtures(self) -> list[tuple]:
        cli_params = {
            "faces_model_credential": os.environ.get("HF_READ_ACCESS_TOKEN", _HF_TOKEN_PLACEHOLDER),
            "faces_model_url": "deepghs/yolo-face",
        }
        basedir = "../"
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), basedir))
        fixtures = []
        # launcher = ProtoRayLauncher()
        launcher = PythonTransformLauncher(FacesPythonTransformConfiguration())
        fixtures.append(
            (
                launcher,
                cli_params,
                basedir + "/test-data/input",
                basedir + "/test-data/expected",
            )
        )
        return fixtures