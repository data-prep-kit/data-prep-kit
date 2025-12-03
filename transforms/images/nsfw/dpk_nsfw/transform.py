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
 
from typing import Any

from argparse import Namespace, ArgumentParser

from PIL import Image
from transformers import pipeline

from data_processing.multimodal.abstract_transform import (
    AbstractMultimodalTransform,
    AbstractMultimodalTransformConfiguration,
)
from data_processing.multimodal.util import JsonUtils

shortname = "nsfw"
cli_prefix = f"{shortname}_"
model_name_key = f"model_name"
normal_class_key = f"normal_class"
nsfw_class_key = f"nsfw_class"

model_name_cli_param = f"{cli_prefix}{model_name_key}"
normal_class_cli_param = f"{cli_prefix}{normal_class_key}"
nsfw_class_cli_param = f"{cli_prefix}{nsfw_class_key}"

default_model_name = "Falconsai/nsfw_image_detection"
default_normal_class = "normal"
default_nsfw_class = "nsfw"


class NsfwTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.model_name = config.get(model_name_key, default_model_name)
        self.normal_class = config.get(normal_class_key, default_normal_class)
        self.nsfw_class = config.get(nsfw_class_key, default_nsfw_class)
        # load model
        self.model = pipeline("image-classification", model=self.model_name)

    def _merge_annotations(self, merged: dict, addend: dict, past_merge_count: int):
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        if not "nsfw" in merged:
            merged["nsfw"] = 0
        if not "nsfw_score" in merged:
            merged["nsfw_score"] = 0
        merged["nsfw"] += addend["nsfw"]
        merged["nsfw_score"] = max(merged["nsfw_score"], addend["nsfw_score"])
        return merged

    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        return { "nsfw": 0, "nsfw_score": 0 }

    def _annotate_images(self, image_batch: list[bytes], image_paths:list[str]) -> list[dict]:
        annotations_batch = []
        # Use self.model to annotate all images.
        for ix, image in enumerate(image_batch):
            try:
                img = JsonUtils.convert_bytes_to_image(image)
                if img.height == 1 or img.width == 1:
                    raise RuntimeError(f"Image has size we cannot process. {img.width=}, {img.height=}")

                # img.show()
                results = self.model(img)

                raw_annotations = {cl["label"]: cl["score"] for cl in results}
                # print(raw_annotations)

                nsfw_score = raw_annotations.get(
                    self.nsfw_class, 0.0
                )
                normal_score = raw_annotations.get(self.normal_class, 0.0)
                has_nsfw = nsfw_score > normal_score
                
                image_annotations = {"nsfw": int(has_nsfw), "nsfw_score": nsfw_score}
            except Exception as err:
                image_annotations = None
                self.logger.exception(f"Image {image_paths[ix]} triggered an exception, it will be skipped.")

            annotations_batch.append(image_annotations)
        return annotations_batch


class NsfwTransformConfiguration(AbstractMultimodalTransformConfiguration):

    def __init__(self):
        super().__init__(shortname, NsfwTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        super().add_input_params(parser)
        # Get model reference
        parser.add_argument(
            f"--{model_name_cli_param}",
            default=default_model_name,
            help=f"Name of the HF model to use for classifying the images. The default model is {default_model_name}",
        )
        parser.add_argument(
            f"--{normal_class_cli_param}",
            default=default_normal_class,
            help=f"Name of the predicted class for normal content. Default is {default_normal_class}.",
        )
        parser.add_argument(
            f"--{nsfw_class_cli_param}",
            default=default_nsfw_class,
            help=f"Name of the predicted class for NSFW content. Default is {default_nsfw_class}.",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        return super().apply_input_params(args)
