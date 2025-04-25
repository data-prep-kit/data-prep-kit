
from dpk_mm.doc_nsfw.docling_extras.nsfw import NsfwAnnotationModel
from docling_ibm.pipeline.full_pipeline import FullPipeline, FullPipelineOptions


class NsfwPipelineOptions(FullPipelineOptions):
    do_ocr: bool = False
    do_picture_classification: bool = True
    do_molecule_annotation: bool = False
    do_equation_translation: bool = False
    do_nsfw_annotation: bool = True


class NsfwPipeline(FullPipeline):

    def __init__(self, pipeline_options: NsfwPipelineOptions):
        super().__init__(pipeline_options=pipeline_options)
        self.pipeline_options: NsfwPipelineOptions

        self.enrichment_pipe.append(
            NsfwAnnotationModel(enabled=self.pipeline_options.do_nsfw_annotation)
        )

    @classmethod
    def get_default_options(cls) -> NsfwPipelineOptions:
        return NsfwPipelineOptions()
