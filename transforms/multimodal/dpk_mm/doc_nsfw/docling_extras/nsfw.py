from typing import Any, Iterable

from docling.models.base_model import BaseEnrichmentModel
from docling_core.types.doc import (
    DoclingDocument,
    NodeItem,
    PictureClassificationData,
    PictureItem,
)
from docling_core.types.doc.document import PictureClassificationClass


class NsfwAnnotationModel(BaseEnrichmentModel):
    def __init__(self, enabled: bool):
        self.enabled = enabled

        self.model_name = "Falconsai/nsfw_image_detection"
        if self.enabled:
            from transformers import pipeline
            # load models
            self.model = pipeline("image-classification", model=self.model_name)

    def is_processable(self, doc: DoclingDocument, element: NodeItem) -> bool:
        if not self.enabled or not isinstance(element, PictureItem):
            return False
        classification = next(
            (
                annot
                for annot in element.annotations
                if isinstance(annot, PictureClassificationData)
            ),
            None,
        )
        if classification is None:
            return False
        return (
            classification.predicted_classes[0].class_name
            == "other"
        )

    def __call__(
        self, doc: DoclingDocument, element_batch: Iterable[NodeItem]
    ) -> Iterable[Any]:
        if not self.enabled:
            yield from element_batch
            return

        for element in element_batch:
            assert isinstance(element, PictureItem)

            predictions = self.model(element.image.pil_image)

            element.annotations.append(
                PictureClassificationData(
                    predicted_classes=[
                        PictureClassificationClass(
                            class_name=cl["label"],
                            confidence=cl["score"],
                        )
                        for cl in predictions
                    ],
                    provenance=f"nsfw-{self.model_name}",
                )
            )

            yield element
