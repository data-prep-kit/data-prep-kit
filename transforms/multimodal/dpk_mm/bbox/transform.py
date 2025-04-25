from argparse import ArgumentParser, Namespace
from io import BytesIO
from typing import Any, Optional

from dpk_mm.abstract_transform import (
    AbstractMultimodalTransform,
    AbstractMultimodalTransformConfiguration,
)
from docling.datamodel.base_models import BoundingBox, ConversionStatus, CoordOrigin
from docling.datamodel.document import (
    ConversionResult,
    DocumentConversionInput,
    DocumentStream,
)
from docling.document_converter import DocumentConverter
from docling.pipeline.standard_model_pipeline import PipelineOptions
from docling_core.types.doc.base import Ref
from dpk_mm.util import JsonUtils


shortname = "bbox"
cli_prefix = f"{shortname}_"
allow_labels_key = f"allow_labels"

allow_labels_key_cli_param = f"{cli_prefix}{allow_labels_key}"

default_allow_labels = "picture"


class BboxTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.allow_labels: list[str] = [
            l.strip()
            for l in config.get(allow_labels_key, default_allow_labels).split(",")
        ]

        self._converter = DocumentConverter(
            pipeline_options=PipelineOptions(do_ocr=False),
        )

        self._labels_mapping = {
            "title": "title",
            "table-of-contents": "document_index",
            "subtitle-level-1": "section_header",
            "checkbox-selected": "checkbox_selected",
            "checkbox-unselected": "checkbox_unselected",
            "caption": "caption",
            "page-header": "page_header",
            "page-footer": "page_footer",
            "footnote": "footnote",
            "table": "table",
            "formula": "formula",
            "list-item": "list_item",
            "code": "code",
            "figure": "picture",
            "picture": "picture",
            "reference": "text",
            "paragraph": "text",
            "text": "text",
        }

    def _merge_annotations(self, merged: dict, addend: dict, past_merge_count: int):
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        new_dict = {**merged}
        new_dict["embedded_im_bbox"].extend(addend.get("embedded_im_bbox", []))
        return new_dict

    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        return {"embedded_im_bbox": []}

    def _annotate_images(self, image_batch: list[bytes], image_paths:list[str]) -> list[dict]:
        annotations_batch = []

        for image in image_batch:
            img = JsonUtils.convert_bytes_to_image(image)
            # img.show()

            buf = BytesIO()
            img.save(buf, format="PDF")
            docs = [DocumentStream(filename="file.pdf", stream=buf)]
            conv_input = DocumentConversionInput.from_streams(docs)

            results = self._converter.convert(conv_input)
            doc_result: ConversionResult = next(results)

            if doc_result is None or doc_result.status != ConversionStatus.SUCCESS:
                self.logger.warning(f"Failed document conversion. {doc_result=}")
                continue
            doc = doc_result.output

            segments = []
            for orig_item in doc.main_text:
                item = (
                    doc._resolve_ref(orig_item)
                    if isinstance(orig_item, Ref)
                    else orig_item
                )
                if item is None or item.prov is None or len(item.prov) == 0:
                    continue
                obj_type = item.obj_type
                label = self._labels_mapping.get(obj_type, "text")
                if label not in self.allow_labels:
                    self.logger.debug(f"Skipping page segment of type {label}")
                    continue

                bbox = BoundingBox.from_tuple(
                    item.prov[0].bbox, origin=CoordOrigin.BOTTOMLEFT
                )
                crop_bbox = bbox.to_top_left_origin(page_height=img.height)
                segments.append(
                    {
                        "bbox": crop_bbox.as_tuple(),
                        "label": label,
                    }
                )

                # cropped_im = img.crop(crop_bbox.as_tuple())
                # cropped_im.show()

            image_annotations = {"embedded_im_bbox": [segments]}
            annotations_batch.append(image_annotations)
        return annotations_batch


class BboxTransformConfiguration(AbstractMultimodalTransformConfiguration):

    def __init__(self):
        super().__init__(shortname, BboxTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        super().add_input_params(parser)
        # Get model reference
        parser.add_argument(
            f"--{allow_labels_key_cli_param}",
            default=default_allow_labels,
            help=f"Allow list of document labels to keep. The list must be provided as a comma-separated text. The default model is {default_allow_labels}",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        return super().apply_input_params(args)
