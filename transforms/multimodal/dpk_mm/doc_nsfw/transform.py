from argparse import ArgumentParser, Namespace
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from dpk_mm.abstract_transform import (
    AbstractMultimodalTransform,
    AbstractMultimodalTransformConfiguration,
)
from docling_core.types.doc import PictureClassificationData, PictureItem
from docling.datamodel.base_models import InputFormat
# from docling.datamodel.base_models import BoundingBox, ConversionStatus, CoordOrigin
from docling.datamodel.document import (
    ConversionResult,
    DocumentStream,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from dpk_mm.doc_nsfw.docling_extras.pipeline import NsfwPipeline, NsfwPipelineOptions
from dpk_mm.util import JsonUtils


shortname = "doc_nsfw"
cli_prefix = f"{shortname}_"


class DocNsfwTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        artifacts_path = Path("models/docling")
        NsfwPipeline.download_models_hf(local_dir=artifacts_path)

        # Configuration option of the full pipeline
        pipeline_options = NsfwPipelineOptions()
        pipeline_options.artifacts_path = artifacts_path
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_picture_images = True

        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_cls=NsfwPipeline, pipeline_options=pipeline_options)
            }
        )

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
            img = JsonUtils.convert_bytes_to_image(image)
            if img.height == 1 or img.width == 1:
                raise RuntimeError(f"Image has size we cannot process. {img.width=}, {img.height=}")
            # img.show()

            num_has_nsfw = 0
            cumulative_nsfw = 0.
            try:
                buf = BytesIO()
                img.save(buf, format="PDF")
                doc_input = DocumentStream(name="file.pdf", stream=buf)

                result = self._converter.convert(doc_input)

                for element, _level in result.document.iterate_items():
                    if not isinstance(element, PictureItem):
                        continue
                    
                    # element.image.pil_image.show()
                    
                    nsfw_score = 0.
                    normal_score = 0.
                    for annot in element.annotations:
                        if isinstance(annot, PictureClassificationData) and annot.provenance.startswith("nsfw-"):
                            for cl in annot.predicted_classes:
                                print(cl)
                                if cl.class_name == "nsfw":
                                    nsfw_score = cl.confidence
                                if cl.class_name == "normal":
                                    normal_score = cl.confidence
                    
                    cumulative_nsfw += nsfw_score
                    if nsfw_score > normal_score:
                        num_has_nsfw += 1

            except Exception as err:
                self.logger.warning(f"Failed document conversion.")
                image_annotations = None
                annotations_batch.append(image_annotations)
                continue

            image_annotations = {"nsfw": int(num_has_nsfw), "nsfw_score": cumulative_nsfw}
            annotations_batch.append(image_annotations)
        return annotations_batch


class DocNsfwTransformConfiguration(AbstractMultimodalTransformConfiguration):

    def __init__(self):
        super().__init__(shortname, DocNsfwTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        super().add_input_params(parser)
        # Get model reference

    def apply_input_params(self, args: Namespace) -> bool:
        return super().apply_input_params(args)
