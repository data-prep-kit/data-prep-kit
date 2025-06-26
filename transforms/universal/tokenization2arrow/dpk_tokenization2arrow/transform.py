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


import os
from argparse import ArgumentParser, Namespace
from typing import Any

import pyarrow as pa
from data_processing.data_access import DataAccess
from data_processing.transform import TransformConfiguration
from data_processing.utils import TransformUtils
from dpk_tokenization.transform import (
    TokenizationTransform,
    TokenizationTransformConfiguration,
)


class Tokenization2ArrowTransform(TokenizationTransform):
    def __init__(self, config: dict[str, Any]):
        """
        This class is used to transform an input table to an arrow file and meta files  utilizing a tokenizer.
        The input table must contain at least two columns, with default names set as `document_id` and `contents`.
        The tokenizer will tokenize each row in `contents` into a sequence of token_ids and write it to `tokens` column
        in the output table, along with the document id and token count stored respectively in `document_id` and `token_count` column.
        """
        self.data_access: DataAccess = config.get("data_access")
        super().__init__(config)
        # we will tokenize the content only if language column value is in lang_filters
        self.output_folder = self.data_access.get_output_folder()
        self.output_folder = self.output_folder if self.output_folder.endswith("/") else f"{self.output_folder}/"
        self.logger.info(f"Tokenizer {config['tokenizer'] = } loaded.")

    def _transform_to_arrow(
        self, table: pa.Table, file_name: str = None, tokenization_metadata: dict[str, Any] = {}
    ) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:
        """
        table: pa.Table which contains tokenized data
        file_name: name of the input file which is used for creating metadata files
        This method,
            - Creates new medata data file .docs - contains one row with content arrow file name, number of documents, number of tokens
            - Creates new medata data file .docs.ids - document_id, token count of that document
            - Loads the token into bytes array and return buffer
        """
        self.logger.debug(f"Processing tokenized data in table with {len(table)} rows")
        token_count_column = table.column("token_count")
        tokens_column = table.column("tokens")
        document_id_column = table.column(self.doc_id_column)
        del table
        token_count_column = token_count_column.to_pylist()
        total_token_counts = sum(token_count_column)
        document_id_column = document_id_column.to_pylist()

        # Save .docs file
        output_parquet_name = self.data_access.get_output_location(file_name)
        full_docs_file_path = output_parquet_name.replace(f"{self.output_folder}", f"{self.output_folder}meta/")
        full_docs_file_path = full_docs_file_path.replace(".parquet", ".docs")
        docs_file_content = (
            f"{os.path.basename(file_name)}, documents: {len(token_count_column)}, tokens: {total_token_counts}"
        )
        self.logger.debug(f"{full_docs_file_path = } {docs_file_content = }")
        self.data_access.save_file(full_docs_file_path, docs_file_content.encode("utf-8"))

        # Save .docs.ids file
        full_docs_ids_file_path = f"{full_docs_file_path}.ids"
        self.logger.debug(f"{full_docs_ids_file_path = }")
        docs_ids_file_rows: str = ""
        for idx, document_id in enumerate(document_id_column):
            docs_ids_file_rows += f"{document_id}, {token_count_column[idx]}\n"
        # remove last \n
        docs_ids_file_rows = docs_ids_file_rows[:-1]
        # Remove quotes and parentheses
        docs_ids_file_rows = docs_ids_file_rows.replace("'", "").replace("(", "").replace(")", "")
        self.logger.debug(f"{self.data_access}")
        self.data_access.save_file(full_docs_ids_file_path, docs_ids_file_rows.encode("utf-8"))
        self.logger.debug(f"Saved file {full_docs_ids_file_path = }")
        del docs_ids_file_rows

        # Gather .arrow file content in buffer and return
        schema = pa.schema([("tokens", pa.uint32())])
        # <class 'pyarrow.lib.Schema'>, tokens: uint32
        # Write it to buffer
        with pa.BufferOutputStream() as bos:
            with pa.ipc.new_file(bos, schema=schema) as writer:
                for token_line in tokens_column:
                    writer.write(pa.record_batch([pa.array(token_line)], schema=schema))
        # self.data_access.save_file(arrow_file_path, bos.getvalue().to_pybytes())

        # TODO: check if we should add anything to tokenization_metadata
        return [(bos.getvalue().to_pybytes(), ".arrow")], tokenization_metadata

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
        self.logger.info(f"Tokenization2ArrowTransform.transform_binary {file_name = }")
        # validate extension
        if TransformUtils.get_file_extension(file_name)[1] != ".parquet":
            self.logger.warning(f"Only .parquet is supported as input file type.")
            return [], {"wrong file type": 1}
        # convert to table
        table = TransformUtils.convert_binary_to_arrow(data=byte_array)
        if table is None:
            self.logger.warning("Transformation of file to table failed")
            return [], {"failed_reads": 1}
        # Ensure that table is not empty
        if table.num_rows == 0:
            self.logger.warning(f"table is empty, skipping processing")
            return [], {"skipped empty tables": 1}

        # transform table
        out_tables, metadata = self.transform(table=table, file_name=file_name)
        # Add to metadata
        self.logger.debug(f"{metadata = }")
        return self._transform_to_arrow(table=out_tables[0], file_name=file_name, tokenization_metadata=metadata)

    def _check_and_convert_tables(
        self, out_tables: list[pa.Table], stats: dict[str, Any]
    ) -> tuple[list[tuple[bytes, str]], dict[str, Any]]:

        out_files = [tuple[bytes, str]] * len(out_tables)
        out_docs = 0
        for i in range(len(out_tables)):
            if not TransformUtils.verify_no_duplicate_columns(table=out_tables[i], file=""):
                self.logger.warning("Transformer created file with the duplicate columns")
                return [], {"duplicate columns result": 1}
            out_binary = TransformUtils.convert_arrow_to_binary(table=out_tables[i])
            if out_binary is None:
                self.logger.warning("Failed to convert table to binary")
                return [], {"failed_writes": 1}
            out_docs += out_tables[i].num_rows
            out_files[i] = (out_binary, ".parquet")
        return out_files, stats | {"result_doc_count": out_docs}


class Tokenization2ArrowTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(name="Tokenization2Arrow", transform_class=Tokenization2ArrowTransform)
        self.params = {}
        self.base_config = TokenizationTransformConfiguration()

    def add_input_params(self, parser: ArgumentParser) -> None:
        self.base_config.add_input_params(parser)

    def apply_input_params(self, args: Namespace) -> bool:
        self.base_config.apply_input_params(args)
        self.params = self.base_config.params
        return True
