import ast
from typing import Any
from transformers import CLIPProcessor, CLIPModel
import numpy as np
from argparse import Namespace, ArgumentParser
import torch

from dpk_mm.abstract_transform import AbstractMultimodalTransform, AbstractMultimodalTransformConfiguration
from data_processing.utils import CLIArgumentProvider

from dpk_mm.util import JsonUtils

shortname = "child"
cli_prefix = f"{shortname}_"
model_path_key = "model_path"
model_path_default = "openai/clip-vit-base-patch32"
model_path_cli_key = f"{cli_prefix}{model_path_key}"

# Define candidate prompts
child_prompts_key = "child_prompts"
child_prompts_cli_key = f"{cli_prefix}{child_prompts_key}"
child_prompts_default = ["a photo of a young boy", "a photo of a young girl", "a photo of a child", "a photo of a kid", "a photo of a baby", "a photo of a teenager", "a photo of a toddler", "None of the Above"]

nsfw_prompts_key = "nsfw_prompts"
nsfw_prompts_cli_key = f"{cli_prefix}{nsfw_prompts_key}"
nsfw_prompts_default = ["a violent scene", "nudity", "a pornographic scene", "None of the Above"] # Need to add

class ChildTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str,Any]):
        super().__init__(config)
        self.model_path = config.get(model_path_key, model_path_default)
        self.child_prompts = config.get(child_prompts_key,child_prompts_default)
        self.nsfw_prompts = config.get(nsfw_prompts_key,nsfw_prompts_default)

        #self.detector = ChildDetector(self.model_path, self.child_prompts, self.nsfw_prompts)

        self.model = CLIPModel.from_pretrained(self.model_path)
        self.processor = CLIPProcessor.from_pretrained(self.model_path)

    def _merge_annotations(self, merged: dict, addend: dict, past_merge_count: int) -> dict:
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        new_dict = {}

        for key, value in merged.items():
             new_dict[key] = max(value,addend[key])

        return new_dict

    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        return {"prompted_child_score": 0, "prompted_nsfw_score": 0 }

    def _annotate_images(self, image_batch: list[bytes], image_paths:list[str]) -> list[dict]:

        # Use self.model to annotate all images.

        annotation_list = []

        for ix, image in enumerate(image_batch):
            try:
                child_score = 0
                nsfw_score = 0
                # An appended set of columns for this image.
                img = JsonUtils.convert_bytes_to_image(image)
                if img.height == 1 or img.width == 1:
                    raise RuntimeError(f"Image has size we cannot process. {img.width=}, {img.height=}")

                inputs = self.processor(text=self.child_prompts, images=img, return_tensors="pt", padding=True)
                # Run the model
                child_outputs = self.model(**inputs)
                # Get the similarity scores and probabilities
                logits_per_image = child_outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
                valid_probs = probs[:, :-1]  # Exclude the last column
                max_prob, max_index = torch.max(valid_probs, dim=1)
                if probs[0, -1] > max_prob:
                    child_score = 0
                else:
                    child_score =max_prob.item()

                # For nsfw detection
                inputs = self.processor(text=self.nsfw_prompts, images=img, return_tensors="pt", padding=True)
                # Run the model
                nsfw_outputs = self.model(**inputs)
                # Get the similarity scores and probabilities
                logits_per_image = nsfw_outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
                valid_probs = probs[:, :-1]  # Exclude the last column
                max_prob, max_index = torch.max(valid_probs, dim=1)
                if probs[0, -1] > max_prob:
                    nsfw_score = 0
                else:
                    nsfw_score = max_prob.item()

                annotations = { "prompted_child_score": child_score, "prompted_nsfw_score": nsfw_score}   # dictionary of prompted_nsfw_score, prompted_child_score
            except Exception as err:
                annotations = None
                self.logger.exception(f"Image {image_paths[ix]} triggered an exception, it will be skipped.")

            annotation_list.append(annotations)
            #print(annotations)
        return annotation_list

class ChildTransformConfiguration(AbstractMultimodalTransformConfiguration):

    def __init__(self):
        super().__init__(shortname, ChildTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the NOOPTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{model_path_cli_key}",
            type=str,
            default=model_path_default,
            help=f"Path to model used. Default is {model_path_default}"
        )
        parser.add_argument(
            f"--{child_prompts_cli_key}",
            type=ast.literal_eval,
            default=ast.literal_eval(f'"{str(child_prompts_default)}"'),
            help=f"Set of prompts to use to match children. Default is {child_prompts_default}"
        )
        parser.add_argument(
            f"--{nsfw_prompts_cli_key}",
            type=ast.literal_eval,
            default=ast.literal_eval(f'"{str(nsfw_prompts_default)}"'),
            help=f"Set of prompts to use to match nsfw. Default is {nsfw_prompts_default}"
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        self.logger.info(f"parameters are : {self.params}")
        return True