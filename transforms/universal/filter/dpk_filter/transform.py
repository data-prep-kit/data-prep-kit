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

import argparse
import ast
import json
import pandas as pd
from typing import Dict
import duckdb
import pyarrow as pa
import os
import string
from data_processing.data_access import DataAccess
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_logger


short_name = "filter"
cli_prefix = short_name + "_"

filter_criteria_key = "criteria_list"
""" AST Key holds the list of filter criteria (in SQL WHERE clause format)"""
filter_logical_operator_key = "logical_operator"
""" Key holds the logical operator that joins filter criteria (AND or OR)"""
filter_columns_to_drop_key = "columns_to_drop"
""" AST Key holds the list of columns to drop after filtering"""
filter_input_arrow_folder_key = "input_arrow_folder"
filter_output_arrow_folder_key = "output_arrow_folder"
""" Additional AST Key to hold input and output folders to arrow and meta files"""
filter_doc_id_column_name_key = "doc_id_column_name"


filter_criteria_cli_param = f"{cli_prefix}{filter_criteria_key}"
""" AST Key holds the list of filter criteria (in SQL WHERE clause format)"""
filter_logical_operator_cli_param = f"{cli_prefix}{filter_logical_operator_key}"
""" Key holds the logical operator that joins filter criteria (AND or OR)"""
filter_columns_to_drop_cli_param = f"{cli_prefix}{filter_columns_to_drop_key}"
""" AST Key holds the list of columns to drop after filtering"""
filter_input_arrow_folder_cli_param = f"{cli_prefix}{filter_input_arrow_folder_key}"
filter_output_arrow_folder_cli_param = f"{cli_prefix}{filter_output_arrow_folder_key}"
""" Additional AST Keys to hold input and output paths to the arrow and meta files"""
filter_doc_id_column_name_cli_param = f"{cli_prefix}{filter_doc_id_column_name_key}"


captured_arg_keys = [filter_criteria_key, 
                     filter_columns_to_drop_key, 
                     filter_input_arrow_folder_key,
                     filter_output_arrow_folder_key,
                     filter_doc_id_column_name_key]
""" The set of keys captured from the command line """

# defaults
filter_criteria_default = ast.literal_eval("[]")
""" The default list of filter criteria (in SQL WHERE clause format)"""
filter_logical_operator_default = "AND"
filter_columns_to_drop_default = ast.literal_eval("[]")
""" The default list of columns to drop"""
filter_doc_id_column_name_default = "id"


class FilterTransform(AbstractTableTransform):
    """
    Implements filtering - select from a pyarrow.Table a set of rows that
    satisfy a set of filtering criteria
    """

    def __init__(self, config: dict):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, FilterTransformRuntime.  If running from the Ray orchestrator,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.data_access: DataAccess = config.get("data_access", None)
        if self.data_access is None:
            self.logger.warning(f"data_access is not provided.")

        self.filter_criteria = config.get(filter_criteria_key, filter_criteria_default)
        self.logical_operator = config.get(filter_logical_operator_key, filter_logical_operator_default)
        self.columns_to_drop = config.get(filter_columns_to_drop_key, filter_columns_to_drop_default)
        self.doc_id_column_name = config.get(filter_doc_id_column_name_key, filter_doc_id_column_name_default)

        # ensure the path endswith("/") if they are not None
        self.input_arrow_folder = config.get(filter_input_arrow_folder_key, "")
        if bool(self.input_arrow_folder.strip()):
            self.input_arrow_folder = self.input_arrow_folder if self.input_arrow_folder.endswith("/") else f"{self.input_arrow_folder}/"
        self.output_arrow_folder = config.get(filter_output_arrow_folder_key, "")
        if bool(self.output_arrow_folder.strip()):
            self.output_arrow_folder = self.output_arrow_folder if self.output_arrow_folder.endswith("/") else f"{self.output_arrow_folder}/"
        

        # Need to extract the parquet input folder names, especially it needs to end with '/'
        self.parquet_input_folder = None
        if self.data_access is not None:
            self.parquet_input_folder = self.data_access.get_input_folder()
        if self.parquet_input_folder is not None:
            self.parquet_input_folder = self.parquet_input_folder if self.parquet_input_folder.endswith("/") else f"{self.parquet_input_folder}/"
        # ref: https://duckdb.org/docs/stable/guides/python/multiple_threads.html
        duckdb_con = duckdb.connect()
        self.local_con = duckdb_con.cursor()
    
    def _construct_arrow_meta_file_path(self, parquet_file_name: str):
        """
        use parquet_file_name to construct all the input and output arrow and meta data file paths
        """
        parquet_file_name_wo_folder = parquet_file_name[len(self.parquet_input_folder):]
        arrow_file_name_wo_folder = parquet_file_name_wo_folder.replace(".parquet", ".arrow")
        docs_file_name_wo_folder = arrow_file_name_wo_folder.replace(".arrow", ".docs")
        ids_file_name_wo_input_folder = docs_file_name_wo_folder.replace(".docs", ".docs.ids")
        self.input_arrow_file = os.path.join(self.input_arrow_folder, arrow_file_name_wo_folder)
        self.input_ids_file = os.path.join(self.input_arrow_folder, "meta/", ids_file_name_wo_input_folder)
        self.output_arrow_file = os.path.join(self.output_arrow_folder, arrow_file_name_wo_folder)
        self.output_docs_file = os.path.join(self.output_arrow_folder, "meta/", docs_file_name_wo_folder)
        self.output_ids_file = os.path.join(self.output_arrow_folder, "meta/", ids_file_name_wo_input_folder)
    
    def _filter_arrow_and_meta_files(self, file_name: str, filtered_ids_list: list):
        # read in the arrow and meta data
        try:
            input_ids_bytes, _ = self.data_access.get_file(self.input_ids_file)
            input_ids_data = input_ids_bytes.decode('utf-8')
            arrow_bytes, _ = self.data_access.get_file(self.input_arrow_file)
            arrow_reader = pa.ipc.open_file(arrow_bytes)
            _ = arrow_reader.read_all()
            input_arrow_tokens_batches = [arrow_reader.get_batch(i)["tokens"].to_pylist() for i in range(arrow_reader.num_record_batches)]
        except Exception as e:
            self.logger.error(f"Error reading input arrow or meta files: {e}")
        input_ids_lines = [line for line in input_ids_data.split('\n')]
        input_ids_list = [line.split(',')[0].strip() for line in input_ids_lines]
        input_token_count_list = [int(line.split(',')[1].strip()) for line in input_ids_lines]

        # construct output arrow and output meta file contents
        output_arrow_tokens_batches = []
        total_docs = 0
        total_tokens = 0
        output_token_count_list = []
        for i, doc_id in enumerate(input_ids_list):
            if doc_id in filtered_ids_list:
                batch_tokens = input_arrow_tokens_batches[i]
                token_count = input_token_count_list[input_ids_list.index(doc_id)]
                assert token_count == len(batch_tokens), f"{doc_id=} {token_count=} not matching that in .arrow"
                output_arrow_tokens_batches.append(batch_tokens)
                output_token_count_list.append(token_count)
                total_docs += 1
                total_tokens += token_count

        # print(f"{output_arrow_tokens_batches=}")
        
        # prepare the output arrow and meta data file contents for pyarrow to write out
        output_ids_lines = [f"{doc_id}, {token_count}\n" for doc_id, token_count in zip(filtered_ids_list, output_token_count_list)]
        # print(f"{output_ids_lines=}")
        output_docs_line = f"{os.path.basename(file_name)}, documents: {total_docs}, tokens: {total_tokens}"
        output_ids_data = "".join(output_ids_lines)
        # print(f"{output_ids_data=}")
        output_ids_data = output_ids_data[:-1]
        # Remove quotes and parentheses
        output_ids_data = output_ids_data.replace("'", "").replace("(", "").replace(")", "")
        try:
            # create missing directories
            arrow_directories = os.path.dirname(self.output_arrow_file)
            docs_directories = os.path.dirname(self.output_docs_file)
            os.makedirs(arrow_directories, exist_ok=True)  # Create directories recursively
            os.makedirs(docs_directories, exist_ok=True)
            # write out the meta data files
            self.data_access.save_file(self.output_docs_file, output_docs_line.encode("utf-8"))
            self.data_access.save_file(self.output_ids_file, output_ids_data.encode("utf-8"))
            # write the output arrow file
            schema = pa.schema([("tokens", pa.uint32())])
            output_arrow_tokens_array =[pa.array(batch_tokens) for batch_tokens in output_arrow_tokens_batches]
            output_arrow_record_batches = [pa.RecordBatch.from_arrays([array], schema=schema) for array in output_arrow_tokens_array]
            with pa.ipc.RecordBatchFileWriter(self.output_arrow_file, schema) as writer:
                for record_batch in output_arrow_record_batches:
                    writer.write_batch(record_batch)
        except Exception as e:
            self.logger.error(f"Error writing arrow or meta files: {e}")

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict]:
        """
        This implementation filters the input table using a SQL statement and
        returns the filtered table and execution stats
        :param table: input table
        :return: list of output tables and custom statistics
        """
        if bool(self.input_arrow_folder.strip()):
            TransformUtils.validate_columns(table=table, required=[self.doc_id_column_name])
        if file_name is not None:
            if not file_name.endswith(".parquet"):
                self.logger.error(f"Error: input_file name doesn't end with '.parquet': {file_name}")
                return [], {"wrong file tpye": 1}
        # move table under a different name, to avoid SQL query parsing error
        input_table = table
        total_docs = input_table.num_rows
        total_columns = input_table.num_columns
        total_bytes = input_table.nbytes

        # initialize the metadata dictionary
        metadata = {
            "total_docs_count": total_docs,
            "total_bytes_count": total_bytes,
            "total_columns_count": total_columns,
        }

        # initialize the SQL statement used for filtering
        sql_statement = "SELECT * FROM input_table"
        if len(self.filter_criteria) > 0:
            # populate metadata with filtering stats for each filter criterion
            for filter_criterion in self.filter_criteria:
                criterion_sql = f"{sql_statement} WHERE {filter_criterion}"
                filter_table = self.local_con.execute(criterion_sql).arrow()
                docs_filtered = total_docs - filter_table.num_rows
                bytes_filtered = total_bytes - filter_table.nbytes
                metadata[f"docs_filtered_out_by '{filter_criterion}'"] = docs_filtered
                metadata[f"bytes_filtered_out_by '{filter_criterion}'"] = bytes_filtered

            # use filtering criteria to build the SQL query for filtering
            filter_clauses = [f"({x})" for x in self.filter_criteria]
            where_clause = f" {self.logical_operator} ".join(filter_clauses)
            sql_statement = f"{sql_statement} WHERE {where_clause}"

            # filter using SQL statement
            try:
                filtered_table = self.local_con.execute(sql_statement).arrow()
            except Exception as ex:
                self.logger.error(f"FilterTransform::transform failed: {ex}")
                raise ex
        else:
            filtered_table = table

        # drop any columns requested from the final result
        if len(self.columns_to_drop) > 0:
            filtered_table_cols_dropped = filtered_table.drop_columns(self.columns_to_drop)
        else:
            filtered_table_cols_dropped = filtered_table

        # add global filter stats to metadata
        metadata["docs_after_filter"] = filtered_table.num_rows
        metadata["columns_after_filter"] = filtered_table_cols_dropped.num_columns
        metadata["bytes_after_filter"] = filtered_table.nbytes
        
        if filtered_table_cols_dropped.num_rows == 0:
            return [], metadata
        else:
            # before returning the filtered table (parquet files) also filter the corresponding arrow and meta files
            if bool(self.input_arrow_folder.strip()):
                assert bool(self.output_arrow_folder.strip()), f"ERROR: filter_output_arrow_folder is needed"
                self._construct_arrow_meta_file_path(file_name)
                filtered_id_list = filtered_table_cols_dropped.column(self.doc_id_column_name).to_pylist()
                self._filter_arrow_and_meta_files(file_name, filtered_id_list)
            else:
                self.logger.warning(f"NOTE: no input_arrow_folder provided. Only parquet files are filtered.")
        
            return [filtered_table_cols_dropped], metadata


class FilterTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=FilterTransform,
        )

    def add_input_params(self, parser: argparse.ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the FilterTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """

        sample_sql = [
            "docq_total_words > 100 AND docq_total_words < 200",
            "docq_perplex_score < 230",
            "date_acquired BETWEEN '2023-07-04' AND '2023-07-08'",
            "title LIKE 'https://%%'",
            "document_id IN ('doc-id-1', 'doc-id-2', 'doc-id-3')",
        ]
        columns_to_drop_example = ["column1", "column2"]

        parser.add_argument(
            f"--{filter_criteria_cli_param}",
            type=ast.literal_eval,
            required=True,
            default=ast.literal_eval("[]"),
            help=f"list of filter criteria (in SQL WHERE clause format), for example: {json.dumps(sample_sql, indent=2, default=str)}",
        )
        parser.add_argument(
            f"--{filter_columns_to_drop_cli_param}",
            type=ast.literal_eval,
            required=False,
            default=ast.literal_eval("[]"),
            help=f"list of columns to drop after filtering, for example: {json.dumps(columns_to_drop_example)}",
        )
        parser.add_argument(
            f"--{filter_logical_operator_cli_param}",
            type=str,
            required=False,
            default="AND",
            choices=["AND", "OR"],
            help="logical operator (AND or OR) that joins filter criteria",
        )
        parser.add_argument(
            f"--{filter_input_arrow_folder_cli_param}",
            type=str,
            required=False,
            default="",
            help="the input path to the .arrow files"
        )
        parser.add_argument(
            f"--{filter_output_arrow_folder_cli_param}",
            type=str,
            required=False,
            default="",
            help="the output path to the .arrow files"
        )
        parser.add_argument(
            f"--{filter_doc_id_column_name_cli_param}",
            type=str,
            required=False,
            default="id",
            help="the unique doc_id column name"
        )


    def apply_input_params(self, args: argparse.Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        # Capture the args that are specific to this transform
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        return True
