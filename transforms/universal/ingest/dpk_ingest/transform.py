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

from argparse import ArgumentParser, Namespace
from typing import Any
import zipfile
import io
import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import (
    CLIArgumentProvider,
    UnrecoverableException,
    get_logger,
)
from data_processing.utils import TransformUtils, get_logger


logger = get_dpk_logger()

shortname = "ingest"
cli_prefix = f"{shortname}_"


class IngestTransform(AbstractTableTransform):
    """
    Implements splitting large files into smaller ones.
    Two flavours of splitting are supported - based on the amount of documents and based on the size
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        """
        super().__init__(config)
        self.curr_file=None
        self.buffer = None

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        split larger files into the smaller ones
        :param table: table
        :param file_name: name of the file
        :return: resulting set of tables
        """
        logger.error(f"Ivalid call to transform method... filename: {file_name}")
        return [], {}


    def transform_binary(self, file_name: str, byte_array: bytes) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        """
        Converts input file into o or more output files.
        If there is an error, an exception must be raised - exit()ing is not generally allowed.
        :param byte_array: contents of the input file to be transformed.
        :param file_name: the file name of the file containing the given byte_array.
        :return: a tuple of a list of 0 or more tuples and a dictionary of statistics that will be propagated
                to metadata.  Each element of the return list, is a tuple of the transformed bytes and a string
                holding the extension to be used when writing out the new bytes.
        """
        self.curr_file=file_name
        def _new_row(file_name, byte_array):
            import uuid
            return pa.Table.from_pylist([{
                'file_name': file_name,
                'docuument_id': str(uuid.uuid4()),
                'contents': byte_array 
                }])

        if TransformUtils.get_file_extension(file_name)[1] == ".zip":
            logger.info(f"Iterating through zip file {file_name=} .")
            table = None
            with zipfile.ZipFile(io.BytesIO(byte_array)) as opened_zip:
                zip_namelist = opened_zip.namelist()
                for archive_doc_filename in zip_namelist:    
                    logger.info("Processing " f"{file_name}/{archive_doc_filename} ")
                    with opened_zip.open(archive_doc_filename) as file:
                        try:
                            # Read the content of the file
                            content_bytes = file.read()
                            if table is None:
                                table = _new_row(f"{file_name}/{archive_doc_filename}", content_bytes)
                            else:
                                table = pa.concat_tables([table, _new_row(f"{file_name}/{archive_doc_filename}", content_bytes)])
                        except Exception as e:
                            logger.error(f" skipping {archive_doc_filename} in {file_name} due to {str(e)}")
                return [(TransformUtils.convert_arrow_to_binary(table=table), ".parquet")], {}

        else:
            try:
                if self.buffer is not None:
                    logger.debug(f"Added new row {file_name} to existing buffer buffer with {self.buffer.num_rows}")
                    self.buffer = pa.concat_tables([self.buffer, _new_row(file_name, byte_array)])
                else:
                    logger.debug(f"Starting buffer with {file_name}")
                    self.buffer = _new_row(file_name, byte_array)
                ## Wait for flush when folder change before writing new parquet file
            except Exception as _:  # Can happen if schemas are different
                # Raise unrecoverable error to stop the execution
                logger.warning(f"table in {file_name} can't be merged with the buffer")
                logger.warning(f"buffer columns {self.buffer.schema.names}")
                raise UnrecoverableException()
            return [], {}
        
        



    def flush(self) -> tuple[list[pa.Table], dict[str, Any]]:
        result = []
        if self.buffer is not None:
            logger.debug(f"flushing buffered table with {self.buffer.num_rows} rows of size {self.buffer.nbytes}")
            result.append(self.buffer)
            self.buffer = None
        else:
            logger.debug(f"Empty buffer. nothing to flush.")
        return result, {"parquet_file": [{self.curr_file: x.num_rows} for x in result]}


    def enforce_folder_boundary(self):
        """
        This is supporting method for transformers, that implement buffering of tables, and triggers
        a call to flush the buffer prior to switching to a new folder if so required
        :return: true if the runtime should call the flush method before processing the next folder
        """
        return True

class IngestTransformConfiguration(TransformConfiguration):

    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(name=shortname, transform_class=IngestTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the IngestTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        return

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        # Capture the args that are specific to this transform
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        logger.info(f"Ingest file parameters are : {self.params}")
        return True
