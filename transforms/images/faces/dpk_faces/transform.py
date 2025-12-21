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

import copy
from typing import Any

from argparse import Namespace, ArgumentParser

from data_processing.multimodal.abstract_transform import (
    AbstractMultimodalTransform,
    AbstractMultimodalTransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider, load_model

from data_processing.multimodal.util import JsonUtils
import os

shortname = "faces"
cli_prefix = f"{shortname}_"
model_url_key = "model_url"
model_credential_key = "model_credential"
model_url_cli_param = f"{cli_prefix}{model_url_key}"
model_credential_cli_param = f"{cli_prefix}{model_credential_key}"
model_credential_from_env = os.environ.get("HF_READ_ACCESS_TOKEN", "")


class FacesTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        # load model

        self.model = load_model(
            config.get(model_url_key), "yolo", config.get(model_credential_key)
        )  # load a pretrained model (recommended for training)
        # self.model = None

    def _merge_annotations(
        self, merged: dict, addend: dict, past_merge_count: int
    ) -> dict:
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        new_dict = {}

        for key, value in merged.items():
            new_dict[key] = value + addend[key]

        return new_dict  # TODO: needs implementation

    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        return {"faces": -1}

    def _annotate_images(
        self, image_batch: list[bytes], image_paths: list[str]
    ) -> list[dict]:
        annotations_batch = []
        # Use self.model to annotate all images.

        print(f"{len(image_batch)=}")

        for image in image_batch:
            # An appended set of columns for this image.

            annotations = {}

            image = JsonUtils.convert_bytes_to_image(image)
            results = self.model(image)
            print(f"{len(results[0].boxes)=}")

            image_annotations = {"faces": len(results[0].boxes)}

            # TODO: accumulate this into annotations across all images.
            annotations = image_annotations
            annotations_batch.append(annotations)

        return annotations_batch


class FacesTransformConfiguration(AbstractMultimodalTransformConfiguration):
    def __init__(self):
        super().__init__("faces", FacesTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the NOOPTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{model_credential_cli_param}",
            required=False,
            default=model_credential_from_env,
            help="Credential to access model for faces detection placed in url",
        )
        parser.add_argument(
            f"--{model_url_cli_param}",
            required=True,
            help="Url to model for faces detection",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        params_no_creds = copy.deepcopy(self.params)
        if model_credential_key not in params_no_creds:
            self.logger.warning(f"{model_credential_key} are missing")
        else:
            if params_no_creds[model_credential_key] != "":
                params_no_creds[model_credential_key] = "****"
        self.logger.info(f"yolov8n-face parameters are : {params_no_creds}")
        return True
