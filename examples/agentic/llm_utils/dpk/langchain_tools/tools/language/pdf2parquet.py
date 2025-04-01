import logging
from typing import Optional, Type
import sys

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from llm_utils.dpk.dpk_common import (
    DPKDataAccessInput,
    DPKRuntimeInput,
    add_runtime_params,
    add_data_access_params,
)
from data_processing.utils import ParamsUtils


class Pdf2parquetInput(BaseModel, DPKDataAccessInput, DPKRuntimeInput):
    """Input for Pdf2parquetTransform."""

    pdf2parquet_batch_size: Optional[int] = Field(
        None,
        description="Number of documents to be saved in the same result table. A value of -1 will generate one result file for each input file.",
    )
    pdf2parquet_artifacts_path: Optional[str] = Field(
        None,
        description="Path where to Docling models artifacts are located, if unset they will be downloaded and fetched from the [HF_HUB_CACHE](https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache) folder.",
    )
    pdf2parquet_contents_type: Optional[str] = Field(
        None,
        description="The output type for the `contents` column. Valid types are `text/markdown`, `text/plain` and `application/json`.",
    )
    pdf2parquet_do_table_structure: Optional[str] = Field(
        None,
        description="If true, detected tables will be processed with the table structure model.",
    )
    pdf2parquet_do_ocr: Optional[str] = Field(
        None,
        description="If true, optical character recognition (OCR) will be used to read the content of bitmap parts of the document.",
    )
    pdf2parquet_ocr_engine: Optional[str] = Field(
        None,
        description=" The OCR engine to use. Valid values are `easyocr`, `tesseract`, `tesseract_cli`.",
    )
    pdf2parquet_bitmap_area_threshold: Optional[float] = Field(
        None,
        description="Threshold for running OCR on bitmap figures embedded in document. The threshold is computed as the fraction of the area covered by the bitmap, compared to the whole page area.",
    )
    pdf2parquet_pdf_backend: Optional[str] = Field(
        None,
        description="The PDF backend to use. Valid values are `dlparse_v2`, `dlparse_v1`, `pypdfium2`",
    )
    pdf2parquet_double_precision: Optional[int] = Field(
        None,
        description="If set, all floating points (e.g. bounding boxes) are rounded to this precision. For tests it is advised to use 0.",
    )


def add_transform_params(transform_params: dict, kwargs):
    """Add transform specific params"""
    fields = list(Pdf2parquetInput.__annotations__.keys())
    for field in fields:
        if field in kwargs and kwargs[field] is not None:
            transform_params[field] = kwargs[field]


class Pdf2parquetTransform(BaseTool):
    """Tool that apples pdf2parquet transform."""

    name: str = "pdf2parquet"
    args_schema: Type[BaseModel] = Pdf2parquetInput
    description: str = "Apply pdf2parquet transform on files in input folder"

    def _run(
        self,
        input_folder: str = "",
        output_folder: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs,
    ) -> str:
        if input_folder == "" or output_folder == "":
            return "Error: input folder or output folder are missing"
        try:
            runtime_type = kwargs.get("runtime_type", "python")
            data_type = kwargs.get("data_type", "local")
            transform_params = {
                "input_folder": input_folder,
                "output_folder": output_folder,
            }
            add_runtime_params(transform_params, runtime_type, kwargs)
            add_data_access_params(transform_params, data_type, kwargs)
            add_transform_params(transform_params, kwargs)

            if runtime_type.strip().lower() == "ray":
                from data_processing_ray.runtime.ray import RayTransformLauncher
                from dpk_pdf2parquet.ray.transform import Pdf2ParquetRayTransformConfiguration

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = RayTransformLauncher(Pdf2ParquetRayTransformConfiguration())

            elif runtime_type.strip().lower() == "python":
                from dpk_pdf2parquet.transform_python import Pdf2ParquetPythonTransformConfiguration
                from data_processing.runtime.pure_python import PythonTransformLauncher

                sys.argv = ParamsUtils.dict_to_req(d=transform_params)
                launcher = PythonTransformLauncher(
                    Pdf2ParquetPythonTransformConfiguration()
                )

            else:
                return f"Error: Unrecognizable type of TransformRuntimeConfiguration  in pdf2parquet transform - {runtime_type}."
            return_code = launcher.launch()
            if return_code != 0:
                return "Error pdf2parquet Job Failed"

            return f"pdf2parquet transform successfully applied with input_folder {input_folder} output_folder {output_folder}."
        except Exception as e:
            return "Error: " + str(e)
