# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2025.
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
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc
from data_processing.data_access import DataAccessFactory
from data_processing.transform import AbstractTableTransform
from data_processing.utils import TransformUtils, get_logger
from dpk_extreme_tokenized.common import (
    arrow_path_cli_param,
    arrow_path_default,
    cli_prefix,
    contents_column_name_cli_param,
    contents_column_name_default,
    extreme_tokenized_data_access_key,
    extreme_tokenized_data_factory_key,
    logger,
)


logger = get_logger(__name__, level="INFO")


class ExtremeTokenizedTransform(AbstractTableTransform):
    """This annotator applies the number of tokens per document length and
    number of tokens per character length of the documents.

    Args:
        contents_column_name - the name of the column holding the document text. Default is `text`.
        arrow_folder_location - location of the folder containing the arrow files.
    """

    def __init__(self, config: dict):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, BlockListTransformRuntime.  If running from the Ray orchestrator,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        super().__init__(config)

        self.contents_column_name = config.get(contents_column_name_cli_param, contents_column_name_default)
        self.arrow_location = config.get(arrow_path_cli_param, arrow_path_default)
        if "://" in self.arrow_location:
            _, self.arrow_location = self.arrow_location.split("://")
        self.daf = config.get(extreme_tokenized_data_factory_key, DataAccessFactory(cli_prefix, False))
        self.data_access = config.get(extreme_tokenized_data_access_key)

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """Inputs: a parquet file containing text documents under the column
        `self.contents_column_name`. For each parquet file, the transform reads
        a matching arrow file under the `self.arrow_location`. The arrow file
        contains the tokens for each document in the parquet file. The transform
        gets the size and the number of characters for each document for the parquet
        file, and the number of tokens calculated for that document from the arrow
        file. The transform annotates the input table with 5 columns:
         - doc_num_tokens - number of tokens for each document
         - doc_size_kbs - document size in kb
         - doc_num_chars - number of characters in the document
         - tokens_per_doc_size - ratio between number of tokens and document size
         - tokens_per_doc_num_chars - ratio between number of tokens and number of characters in document
        """
        logger.debug(f"Transforming table with {table.num_rows} rows from file {file_name}")
        file_path = Path(file_name)
        pq_input_path = self.data_access.input_folder
        condition = pc.and_(
            pc.is_valid(table[self.contents_column_name]),  # Non-null rows
            pc.not_equal(table[self.contents_column_name], ""),  # Non-empty strings
        )
        # Apply the filter
        table = table.filter(condition)
        logger.debug(f"After filtering, input table has {table.num_rows} rows")
        data_access_for_arrow = self.daf.create_data_access()
        suffix_path = str(file_path.relative_to(pq_input_path))
        arrow_file_path = os.path.join(self.arrow_location, suffix_path.replace(".parquet", ".arrow"))
        arrow_bytes, _ = data_access_for_arrow.get_file(arrow_file_path)
        arrow_reader = pa.ipc.open_file(arrow_bytes)
        _ = arrow_reader.read_all()
        doc_tokens = [arrow_reader.get_batch(i)["tokens"].to_pylist() for i in range(arrow_reader.num_record_batches)]
        if table.num_rows != len(doc_tokens):
            logger.error(f"Cannot process {file_name} file because of mismatch between")
            logger.error(f"the number of documents {table.num_rows} and the number of token lists {len(doc_tokens)}")
            return [], {"mismatched_docs_tokens_files": 1}
        doc_num_tokens = [len(x) for x in doc_tokens]
        table_length = table.num_rows
        doc_size_kbs = [0.0] * table_length
        doc_num_chars = [0.0] * table_length
        tokens_per_doc_size = [0.0] * table_length
        tokens_per_doc_num_chars = [0.0] * table_length
        for index, doc in enumerate(table[self.contents_column_name]):
            if index % 1000 == 999:
                logger.debug(f"Processed {index + 1}/ {table_length} documents")
            doc_text = doc.as_py()
            doc_size_kbs[index] = len(doc_text.encode("utf-8")) / 1024.0
            doc_num_chars[index] = len(doc_text)
            if doc_size_kbs[index] > 0:
                tokens_per_doc_size[index] = doc_num_tokens[index] / (doc_size_kbs[index] * 1024)
            if doc_num_chars[index] > 0:
                tokens_per_doc_num_chars[index] = doc_num_tokens[index] / doc_num_chars[index]
        metadata = {
            "total_docs": table_length,
        }
        logger.debug(f"Processed {table_length}/ {table_length} documents")
        res_table = TransformUtils.add_column(table=table, name="doc_num_tokens", content=doc_num_tokens)
        res_table = TransformUtils.add_column(table=res_table, name="doc_size_kbs", content=doc_size_kbs)
        res_table = TransformUtils.add_column(table=res_table, name="doc_num_chars", content=doc_num_chars)
        res_table = TransformUtils.add_column(table=res_table, name="tokens_per_doc_size", content=tokens_per_doc_size)
        res_table = TransformUtils.add_column(
            table=res_table, name="tokens_per_doc_num_chars", content=tokens_per_doc_num_chars
        )
        return [res_table], metadata
