# SPDX-License-Identifier: Apache-2.0
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

import enum
import io
import json
import time
import uuid
import zipfile
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import filetype
import pandas as pd
try:
    from pandas.io.json import ujson_dumps
except:
    from pandas.io.json import dumps as ujson_dumps
import pyarrow as pa
import numpy as np
from data_processing.transform import AbstractBinaryTransform, TransformConfiguration
from data_processing.utils import TransformUtils, get_logger, str2bool
from data_processing.utils.cli_utils import CLIArgumentProvider
from data_processing.utils.multilock import MultiLock
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import DocumentStream, MimeTypeToFormat
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    OcrOptions,
    PdfPipelineOptions,
    TesseractCliOcrOptions,
    TesseractOcrOptions,
)
from docling.document_converter import DocumentConverter, InputFormat, PdfFormatOption
from docling.models.base_ocr_model import OcrOptions


logger = get_logger(__name__)
# logger = get_logger(__name__, level="DEBUG")

shortname = "docling2parquet"
cli_prefix = f"{shortname}_"
docling2parquet_batch_size_key = f"batch_size"
docling2parquet_artifacts_path_key = f"artifacts_path"
docling2parquet_contents_type_key = f"contents_type"
docling2parquet_do_table_structure_key = f"do_table_structure"
docling2parquet_do_ocr_key = f"do_ocr"
docling2parquet_ocr_engine_key = f"ocr_engine"
docling2parquet_bitmap_area_threshold_key = f"bitmap_area_threshold"
docling2parquet_pdf_backend_key = f"pdf_backend"
docling2parquet_double_precision_key = f"double_precision"


class docling2parquet_contents_types(str, enum.Enum):
    MARKDOWN = "text/markdown"
    TEXT = "text/plain"
    JSON = "application/json"

    def __str__(self):
        return str(self.value)


class docling2parquet_pdf_backend(str, enum.Enum):
    PYPDFIUM2 = "pypdfium2"
    DLPARSE_V1 = "dlparse_v1"
    DLPARSE_V2 = "dlparse_v2"

    def __str__(self):
        return str(self.value)


class docling2parquet_ocr_engine(str, enum.Enum):
    EASYOCR = "easyocr"
    TESSERACT_CLI = "tesseract_cli"
    TESSERACT = "tesseract"

    def __str__(self):
        return str(self.value)


docling2parquet_batch_size_default = -1
docling2parquet_contents_type_default = docling2parquet_contents_types.MARKDOWN
docling2parquet_do_table_structure_default = True
docling2parquet_do_ocr_default = True
docling2parquet_bitmap_area_threshold_default = 0.05
docling2parquet_ocr_engine_default = docling2parquet_ocr_engine.EASYOCR
docling2parquet_pdf_backend_default = docling2parquet_pdf_backend.DLPARSE_V2
docling2parquet_double_precision_default = 8

docling2parquet_batch_size_cli_param = f"{cli_prefix}{docling2parquet_batch_size_key}"
docling2parquet_artifacts_path_cli_param = f"{cli_prefix}{docling2parquet_artifacts_path_key}"
docling2parquet_contents_type_cli_param = f"{cli_prefix}{docling2parquet_contents_type_key}"
docling2parquet_do_table_structure_cli_param = (
    f"{cli_prefix}{docling2parquet_do_table_structure_key}"
)
docling2parquet_do_ocr_cli_param = f"{cli_prefix}{docling2parquet_do_ocr_key}"
docling2parquet_bitmap_area_threshold__cli_param = (
    f"{cli_prefix}{docling2parquet_bitmap_area_threshold_key}"
)
docling2parquet_ocr_engine_cli_param = f"{cli_prefix}{docling2parquet_ocr_engine_key}"
docling2parquet_pdf_backend_cli_param = f"{cli_prefix}{docling2parquet_pdf_backend_key}"
docling2parquet_double_precision_cli_param = (
    f"{cli_prefix}{docling2parquet_double_precision_key}"
)


class Docling2ParquetTransform(AbstractBinaryTransform):
    """ """

    def __init__(self, config: dict):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, LangSelectorTransformRuntime.  If running inside the RayMutatingDriver,
        these will be provided by that class with help from the RayMutatingDriver.
        """

        super().__init__(config)

        self.batch_size = config.get(docling2parquet_batch_size_key, docling2parquet_batch_size_default)
        self.artifacts_path = config.get(docling2parquet_artifacts_path_key, None)
        if self.artifacts_path is not None:
            self.artifacts_path = Path(self.artifacts_path)
        self.contents_type = config.get(
            docling2parquet_contents_type_key, docling2parquet_contents_types.MARKDOWN
        )
        if not isinstance(self.contents_type, docling2parquet_contents_types):
            self.contents_type = docling2parquet_contents_types[self.contents_type]
        self.do_table_structure = config.get(
            docling2parquet_do_table_structure_key, docling2parquet_do_table_structure_default
        )
        self.do_ocr = config.get(docling2parquet_do_ocr_key, docling2parquet_do_ocr_default)
        self.ocr_engine_name = config.get(
            docling2parquet_ocr_engine_key, docling2parquet_ocr_engine_default
        )
        if not isinstance(self.ocr_engine_name, docling2parquet_ocr_engine):
            self.ocr_engine_name = docling2parquet_ocr_engine[self.ocr_engine_name]
        self.bitmap_area_threshold = config.get(
            docling2parquet_bitmap_area_threshold_key,
            docling2parquet_bitmap_area_threshold_default,
        )
        self.pdf_backend_name = config.get(
            docling2parquet_pdf_backend_key, docling2parquet_pdf_backend_default
        )
        if not isinstance(self.pdf_backend_name, docling2parquet_pdf_backend):
            self.pdf_backend_name = docling2parquet_pdf_backend[self.pdf_backend_name]
        self.double_precision = config.get(
            docling2parquet_double_precision_key, docling2parquet_double_precision_default
        )

        logger.info("Initializing models")
        pipeline_options = PdfPipelineOptions(
            artifacts_path=self.artifacts_path,
            do_table_structure=self.do_table_structure,
            do_ocr=self.do_ocr,
            ocr_options=self._get_ocr_engine(self.ocr_engine_name),
        )
        pipeline_options.ocr_options.bitmap_area_threshold = self.bitmap_area_threshold

        lock = MultiLock("dpk_docling2parquet_init")
        try:
            logger.debug(
                f"Going to acquire lock {lock.lock_filename} for synchronizing global filesystem operations."
            )
            locked = lock.acquire()
            logger.debug(f"Lock {lock.lock_filename} acquired.")

            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                        backend=self._get_pdf_backend(self.pdf_backend_name),
                    )
                }
            )
            self._converter.initialize_pipeline(InputFormat.PDF)
        finally:
            lock.release()
            logger.debug(f"Lock {lock.lock_filename} released.")
        
        self.buffer = []

    def _get_ocr_engine(self, engine_name: docling2parquet_ocr_engine) -> OcrOptions:
        if engine_name == docling2parquet_ocr_engine.EASYOCR:
            return EasyOcrOptions()
        elif engine_name == docling2parquet_ocr_engine.TESSERACT_CLI:
            return TesseractCliOcrOptions()
        elif engine_name == docling2parquet_ocr_engine.TESSERACT:
            return TesseractOcrOptions()

        raise RuntimeError(f"Unknown OCR engine `{engine_name}`")

    def _get_pdf_backend(self, backend_name: docling2parquet_pdf_backend):
        if backend_name == docling2parquet_pdf_backend.DLPARSE_V1:
            return DoclingParseDocumentBackend
        elif backend_name == docling2parquet_pdf_backend.DLPARSE_V2:
            return DoclingParseV2DocumentBackend
        elif backend_name == docling2parquet_pdf_backend.PYPDFIUM2:
            return PyPdfiumDocumentBackend

        raise RuntimeError(f"Unknown PDF backend `{backend_name}`")

    def _update_metrics(self, num_pages: int, elapse_time: float):
        # This is implemented in the ray version
        pass

    def _convert_docling2parquet(
        self, doc_filename: str, ext: str, content_bytes: bytes
    ) -> dict:
        # Convert PDF to Markdown
        start_time = time.time()
        buf = io.BytesIO(content_bytes)
        input_doc = DocumentStream(name=doc_filename, stream=buf)

        conv_res = self._converter.convert(input_doc)
        doc = conv_res.document
        elapse_time = time.time() - start_time

        if self.contents_type == docling2parquet_contents_types.MARKDOWN:
            content_string = doc.export_to_markdown()
        elif self.contents_type == docling2parquet_contents_types.TEXT:
            content_string = doc.export_to_text()
        elif self.contents_type == docling2parquet_contents_types.JSON:
            content_string = ujson_dumps(
                doc.export_to_dict(), double_precision=self.double_precision
            )
        else:
            raise RuntimeError(f"Uknown contents_type {self.contents_type}.")
        num_pages = len(doc.pages)
        num_tables = len(doc.tables)
        num_doc_elements = len(doc.texts)
        document_hash = str(doc.origin.binary_hash)  # we turn the uint64 hash into str, because it is easier to handle for pyarrow

        self._update_metrics(num_pages=num_pages, elapse_time=elapse_time)

        file_data = {
            "filename": TransformUtils.get_file_basename(doc_filename),
            "contents": content_string,
            "num_pages": num_pages,
            "num_tables": num_tables,
            "num_doc_elements": num_doc_elements,
            "document_id": str(uuid.uuid4()),
            "document_hash": document_hash,
            "ext": ext,
            "hash": TransformUtils.str_to_hash(content_string),
            "size": len(content_string),
            "date_acquired": datetime.now().isoformat(),
            "document_convert_time": elapse_time,
        }

        return file_data

    def _detect_mime(self, file_name: str, content_bytes: bytes) -> tuple[str|None, str]:
        kind = filetype.guess(content_bytes)
        ext = TransformUtils.get_file_extension(file_name)[1].lower() 
        if kind is not None:
            mime = kind.mime
            ext = kind.extension
        elif ext == ".xml":
            mime = "application/xml"
        elif ext == ".html" or ext == ".htm":
            mime = "text/html"
        elif ext == ".md":
            mime = "text/markdown"
        else:
            mime = None
        
        return mime, ext

    def transform_binary(
        self, file_name: str, byte_array: bytes
    ) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        """
        If file_name is detected as a PDF file, it generates a pyarrow table with a single row
        containing the document converted in markdown format.
        If file_name is detected as a ZIP archive, it generates a pyarrow table with a row
        for each PDF file detected in the archive.
        """

        data = [*self.buffer]
        success_doc_id = []
        failed_doc_id = []
        skipped_doc_id = []
        number_of_rows = 0

        try:
            # TODO: Docling has an inner-function with a stronger type checking.
            # Once it is exposed as public, we can use it here as well.
            root_mime, root_ext = self._detect_mime(file_name, byte_array)

            # Process single documents
            if root_mime is not None and root_mime in MimeTypeToFormat:
                logger.debug(f"Detected root file {file_name=} as {root_mime}.")

                try:
                    file_data = self._convert_docling2parquet(
                        doc_filename=file_name, ext=root_ext, content_bytes=byte_array
                    )

                    file_data["source_filename"] = TransformUtils.get_file_basename(
                        file_name
                    )

                    data.append(file_data)
                    number_of_rows += 1
                    success_doc_id.append(file_name)

                except Exception as e:
                    failed_doc_id.append(file_name)
                    logger.warning(
                        f"Exception {str(e)} processing file {file_name}, skipping"
                    )

            # Process ZIP archive of documents
            elif root_mime == "application/zip":
                logger.debug(
                    f"Detected root file {file_name=} as ZIP. Iterating through the archive content."
                )

                with zipfile.ZipFile(io.BytesIO(byte_array)) as opened_zip:
                    zip_namelist = opened_zip.namelist()

                    for archive_doc_filename in zip_namelist:

                        logger.info("Processing " f"{archive_doc_filename=} ")

                        with opened_zip.open(archive_doc_filename) as file:
                            try:
                                # Read the content of the file
                                content_bytes = file.read()

                                # Detect file type
                                mime, ext = self._detect_mime(archive_doc_filename, content_bytes)

                                if mime is None or mime not in MimeTypeToFormat:
                                    logger.info(
                                        f"File {archive_doc_filename=} is not detected as valid format {mime=}. Skipping."
                                    )
                                    skipped_doc_id.append(archive_doc_filename)
                                    continue

                                file_data = self._convert_docling2parquet(
                                    doc_filename=archive_doc_filename,
                                    ext=ext,
                                    content_bytes=content_bytes,
                                )
                                file_data["source_filename"] = (
                                    TransformUtils.get_file_basename(file_name)
                                )

                                data.append(file_data)
                                success_doc_id.append(archive_doc_filename)
                                number_of_rows += 1

                            except Exception as e:
                                failed_doc_id.append(archive_doc_filename)
                                logger.warning(
                                    f"Exception {str(e)} processing file {archive_doc_filename}, skipping"
                                )

            else:
                logger.warning(
                    f"File {file_name=} is not detected as a supported type nor as ZIP but {root_mime=}. Skipping."
                )

            
            metadata = {
                "nrows": number_of_rows,
                "nsuccess": len(success_doc_id),
                "nfail": len(failed_doc_id),
                "nskip": len(skipped_doc_id),
            }

            batch_results = []
            self.buffer = []
            if self.batch_size <= 0:
                # we do a single batch
                table = pa.Table.from_pylist(data)
                batch_results.append((TransformUtils.convert_arrow_to_binary(table=table), ".parquet"))
            else:
                # we create result files containing batch_size rows/documents
                num_left = len(data)
                start_row = 0
                while num_left >= self.batch_size:
                    table = pa.Table.from_pylist(data[start_row:self.batch_size])
                    batch_results.append((TransformUtils.convert_arrow_to_binary(table=table), ".parquet"))
                    
                    start_row += self.batch_size
                    num_left = num_left - self.batch_size
                
                if num_left >= 0:
                    self.buffer = data[start_row:]

            return batch_results, metadata
        except Exception as e:
            logger.error(f"Fatal error with file {file_name=}. No results produced.")
            raise

    def flush_binary(self) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        result = []
        if len(self.buffer) > 0:
            logger.debug(f"flushing buffered table with {len(self.buffer)} rows.")
            table = pa.Table.from_pylist(self.buffer)
            result.append((TransformUtils.convert_arrow_to_binary(table=table), ".parquet"))
            self.buffer = None
        else:
            logger.debug(f"Empty buffer. nothing to flush.")
        return result, {}


class Docling2ParquetTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(
        self, transform_class: type[AbstractBinaryTransform] = Docling2ParquetTransform
    ):
        super().__init__(
            name=shortname,
            transform_class=transform_class,
        )

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{docling2parquet_batch_size_cli_param}",
            type=int,
            help="Number of documents to be saved in the same result table. A value of -1 will generate one result file for each input file.",
            default=docling2parquet_batch_size_default,
        )
        parser.add_argument(
            f"--{docling2parquet_artifacts_path_cli_param}",
            type=str,
            help="Path where to models artifacts are located, if unset they will be downloaded in the HF_CACHE folder.",
            default=None,
        )
        parser.add_argument(
            f"--{docling2parquet_contents_type_cli_param}",
            type=docling2parquet_contents_types,
            choices=list(docling2parquet_contents_types),
            help="Content type to use for the contents column.",
            default=docling2parquet_contents_types.MARKDOWN,
        )
        parser.add_argument(
            f"--{docling2parquet_do_table_structure_cli_param}",
            type=str2bool,
            help="If true, detected tables will be processed with the table structure model.",
            default=docling2parquet_do_table_structure_default,
        )
        parser.add_argument(
            f"--{docling2parquet_do_ocr_cli_param}",
            type=str2bool,
            help="If true, optical character recognition (OCR) will be used to read the PDF content.",
            default=docling2parquet_do_ocr_default,
        )
        parser.add_argument(
            f"--{docling2parquet_ocr_engine_cli_param}",
            type=docling2parquet_ocr_engine,
            choices=list(docling2parquet_ocr_engine),
            help="The OCR engine to use.",
            default=docling2parquet_ocr_engine.EASYOCR,
        )
        parser.add_argument(
            f"--{docling2parquet_bitmap_area_threshold__cli_param}",
            type=float,
            help="Threshold for running OCR on bitmap figures embedded in document. The threshold is computed as the fraction of the area covered by the bitmap, compared to the whole page area.",
            default=docling2parquet_bitmap_area_threshold_default,
        )
        parser.add_argument(
            f"--{docling2parquet_pdf_backend_cli_param}",
            type=docling2parquet_pdf_backend,
            choices=list(docling2parquet_pdf_backend),
            help="The PDF backend to use.",
            default=docling2parquet_pdf_backend.DLPARSE_V2,
        )
        parser.add_argument(
            f"--{docling2parquet_double_precision_cli_param}",
            type=int,
            required=False,
            help="If set, all floating points (e.g. bounding boxes) are rounded to this precision. For tests it is advised to use 0.",
            default=docling2parquet_double_precision_default,
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """

        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        logger.info(f"docling2parquet parameters are : {self.params}")
        return True
