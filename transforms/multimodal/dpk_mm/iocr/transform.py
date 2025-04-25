from io import BytesIO
import os
from typing import Any
from PIL import Image

from argparse import Namespace, ArgumentParser

from dpk_mm.abstract_transform import (
    AbstractMultimodalTransform,
    AbstractMultimodalTransformConfiguration,
)

from ultralytics import YOLO
from data_processing.utils import CLIArgumentProvider

from dpk_mm.util import JsonUtils

from hrl_ocr.pipeline.ibm_ocr.ibm_ocr_util.ocr_components_config_provider import (  # pyright: ignore[reportMissingImports]
    OcrComponentsConfigProvider,
)
from hrl_ocr.pipeline.ibm_ocr.ocr_inference import ( # pyright: ignore[reportMissingImports]
    OCRInference
)

from hrl_ocr.models.block_structure.block_structure_analyzer import BlockStructureAnalyzer # type: ignore

shortname = "iocr"
cli_prefix = f"{shortname}_"
model_path_key = "model_path"
model_path_default = "models/ocr_iocr/artifacts"
model_path_cli_key = f"{cli_prefix}{model_path_key}"

text_joiner = " "
block_joiner = "\n\n"
image_joiner = "\n\n"

class IocrTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str,Any]):
        super().__init__(config)
        
        # load model
        model_path = config.get(model_path_key,model_path_default)
        os.environ["IOCR_WEIGHTS_LOCATION"] = model_path
        self.logger.info(f"Loading model from {model_path}")
        self.model = OCRInference()

    def _merge_annotations(self, merged: dict, addend: dict, past_merge_count: int) -> dict:
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        new_dict = {}

        for key, value in merged.items():
             new_dict[key] = value + image_joiner + addend[key]

        return new_dict


    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        return {"iocr": ""}

    def _annotate_images(self, image_batch:list[bytes], image_paths:list[str]) -> list[dict]:

        annotations_batch = []
        # Use self.model to annotate all images.

        # print(f"{len(image_batch)=}")

        index = -1;
        for image in image_batch:
            index += 1

            # An appended set of columns for this image.
            annotations = {}

            runtime_config = OcrComponentsConfigProvider.get_runtime_config()
            #disable font recognition
            runtime_config["fonts_style_recognition"][
                "is_enabled"
            ] = False
            runtime_config["block_structure_analyzer"][
                "is_enabled"
            ] = True


            try:
                pil_image = JsonUtils.convert_bytes_to_image(image)
                #pil_image.show()
                if pil_image.height == 1 or pil_image.width == 1:
                    raise RuntimeError(f"Image has size we cannot process. {pil_image.width=}, {pil_image.height=}")
                (
                    boxes_info_list,
                    processed_image,
                    rotation_angle,
                    graphical_lines,
                    timing_info,
                ) = self.model.do_predict(
                    image_name="n/a",
                    img=pil_image,
                    languages_list=["latn"],
                    runtime_config=runtime_config,
                )
                image_annotations = {}

                # TODO: How OCR text should be structured such the HAP can be applied effectively?
                # Option1.1: By BlockStructure reading order with space between lines and new line at the end of block
                text_lines_info = BlockStructureAnalyzer().get_text_lines_info(boxes_info_list)
                text_lines_blocks = BlockStructureAnalyzer().get_text_lines_containing_blocks(boxes_info_list)
                reading_order = ""
                prev_block_id = 0
                for line_id, (line_info, block_id) in enumerate(zip(text_lines_info, text_lines_blocks)):
                    # print(f'{block_id} {line_id} {line_info["line_id"]} {line_info["text"]}')
                    if not reading_order:
                        reading_order = line_info["text"]
                    elif block_id != prev_block_id:
                        # Concatenate with a newline character if block_id is the different from the previous one
                        reading_order += f'{block_joiner}{line_info["text"]}'
                    else:
                        # Concatenate with a space if block_id is same from the previous one
                        reading_order += f'{text_joiner}{line_info["text"]}'

                    # Update the previous block_id
                    prev_block_id = block_id

                # Option1.2: By BlockStructure reading order with space between lines
                # reading_order = ' '.join([line_info["text"] for line_info in text_lines_info])

                # Option2: Token based sort by Top-Bottom-Left-right with space between words
                # sorted_words_tblr = sorted(boxes_info_list, key=lambda x: (x["bbox"][1], x["bbox"][3], x["bbox"][0], x["bbox"][2]))
                # reading_order = ' '.join([word["word"] for word in sorted_words_tblr])

                # raw_annotations = [{"text": token["word"], "bbox":token["bbox"]} for token in boxes_info_list]

                raw_annotations = reading_order
                #print(f"{raw_annotations=}")

                image_annotations = {"iocr": raw_annotations}

                annotations = image_annotations
            except Exception as exc:
                self.logger.warning(f"Exception processing image {image_paths[index]}: {exc}")
                annotations = None      # Indicates an error on this image to the caller.

            annotations_batch.append(annotations)

        return annotations_batch

class IocrTransformConfiguration(AbstractMultimodalTransformConfiguration):

    def __init__(self):
        super().__init__("iocr", IocrTransform)

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
            help=f"The path to the faces model to load. Default {model_path_default}.",
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