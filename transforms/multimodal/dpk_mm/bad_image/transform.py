import ast
from typing import Any

from argparse import Namespace, ArgumentParser

from dpk_mm.abstract_transform import AbstractMultimodalTransform, AbstractMultimodalTransformConfiguration
from data_processing.utils import CLIArgumentProvider

from dpk_mm.util import JsonUtils
from dpk_mm.people.peopledetect import PeopleDetect
from dpk_mm.people.faceblur import *
from PIL import Image
import time
import random

shortname = "bad_image"
cli_prefix = f"{shortname}_"
bad_indexes_key = "bad_indexes"
bad_indexes_default = [0]
bad_indexex_cli_key = f"{cli_prefix}{bad_indexes_key}"

class BadIndexTransform(AbstractMultimodalTransform):
    """
    A transform that allows emulating errors on image annotation generation for testing
    AbstractMultimodalTransform's handling of erroring images.
    """
    def __init__(self, config: dict[str,Any]):
        super().__init__(config)
        self.bad_indexes = config.get(bad_indexes_key,bad_indexes_default)


    def _merge_annotations(self, merged: dict, addend: dict, past_merge_count: int) -> dict:
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        return merged   # Not testing this.


    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        return {"dummy": 1}

    def _annotate_images(self, image_batch: list[bytes], image_paths:list[str]) -> list[dict]:
        """
        Emulates failure of image processing to return None as the dictionary of
        attributes for the image indexes in self.bad_indexes.
        """
        annotations = []
        for index in range(len(image_batch)):
            if index in self.bad_indexes:
                annotation = None   # Emulate an error in annotation generation
            else:
                annotation = self._get_dummy_annotations()
            annotations.append(annotation)
        return annotations


# class BadIndexTransformConfiguration(AbstractMultimodalTransformConfiguration):
#
#     def __init__(self):
#         super().__init__(shortname, BadIndexTransform)
#
#     def add_input_params(self, parser: ArgumentParser) -> None:
#         """
#         Add Transform-specific arguments to the given  parser.
#         This will be included in a dictionary used to initialize the NOOPTransform.
#         By convention a common prefix should be used for all transform-specific CLI args
#         (e.g, noop_, pii_, etc.)
#         """
#         parser.add_argument(
#             f"--{bad_indexex_cli_key}",
#             type=ast.literal_eval,
#             default=bad_indexes_default,
#             help=f"The path to the people model to load. Default {bad_indexes_default}.",
#         )
#
#     def apply_input_params(self, args: Namespace) -> bool:
#         """
#         Validate and apply the arguments that have been parsed
#         :param args: user defined arguments.
#         :return: True, if validate pass or False otherwise
#         """
#         captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
#         self.params = self.params | captured
#         self.logger.info(f"parameters are : {self.params}")
#         return True