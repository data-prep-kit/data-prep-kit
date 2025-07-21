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

import time, datetime
import torch
from argparse import ArgumentParser, Namespace
from typing import Any
import numpy as np
import random
import lance
import os
import ray
import json
from lance.fragment import write_fragments

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_logger
from sentence_transformers import SentenceTransformer
from data_processing.data_access import DataAccess


short_name = "text_encoder"
cli_prefix = f"{short_name}_"
model_name_key = "model_name"
content_column_name_key = "content_column_name"
output_embeddings_column_name_key = "output_embeddings_column_name"
lanceDB_data_uri_key="lanceDB_data_uri"
lanceDB_batch_size_key="lanceDB_batch_size"
embedding_batch_size_key="embedding_batch_size"
fragments_json_folder_key="fragments_json_folder"
dataset_name_key="dataset_name"
embeddings_exist_key="embeddings_exist"

model_name_cli_param = f"{cli_prefix}{model_name_key}"
content_column_name_cli_param = f"{cli_prefix}{content_column_name_key}"
output_embeddings_column_name_cli_param = f"{cli_prefix}{output_embeddings_column_name_key}"
lanceDB_data_uri_cli_param = f"{cli_prefix}{lanceDB_data_uri_key}"
lanceDB_batch_size_cli_param = f"{cli_prefix}{lanceDB_batch_size_key}"
embedding_batch_size_cli_param = f"{cli_prefix}{embedding_batch_size_key}"
fragments_json_folder_cli_param = f"{cli_prefix}{fragments_json_folder_key}"
dataset_name_cli_param = f"{cli_prefix}{dataset_name_key}"
embeddings_exist_cli_param = f"{cli_prefix}{embeddings_exist_key}"

default_model_name = "ibm-granite/granite-embedding-30m-english"
default_content_column_name = "contents"
default_output_embeddings_column_name = "embeddings"
default_lanceDB_data_uri_name = ""
default_lanceDB_batch_size = 1048576
default_embedding_batch_size = 16
default_fragments_json_folder = ""
default_dataset_name = ""
default_embeddings_exist = False


class TextEncoderTransform(AbstractTableTransform):
    """
    This class is used to encode text into embeddings. It uses the sentence-transformers library.
    The config dictionary should contain the following keys:
        model_name: str,
        content_column_name: str,
        output_embeddings_column_name: str,
        lancedb_data_uri: str,
        lancedb_batch_size: int,
        embedding_batch_size: int,
        fragments_json_folder: str,
        dataset_name: str
    """

    def __init__(self, config: dict[str, Any]):
        """ 
        Make sure that the param name corresponds to the name used in apply_input_params method
        of TextEncoderTransform class
        """
        super().__init__(config)

        self.logger = get_logger(__name__)

        self.model_name = config.get(model_name_key, default_model_name)
        self.content_column_name = config.get(content_column_name_key, default_content_column_name)
        self.output_embeddings_column_name = config.get(
            output_embeddings_column_name_key, default_output_embeddings_column_name
        )
        # keep the actor_id for creating part of the frangments_json file written by individual workers
        self.actor_id = ray.get_runtime_context().get_actor_id()

        if torch.cuda.is_available():
            self.logger.info(f"GPU is available!")
            self.model.half()
            device = torch.device("cuda")  # Use GPU
        else:
            self.logger.info(f"GPU is not available. Using CPU.")
            device = torch.device("cpu")   # Use CPU
        self.embeddings_exist = config.get(embeddings_exist_key, default_embeddings_exist)
        self.logger.info(f"{self.embeddings_exist=}")
        if not self.embeddings_exist:
            self.model = SentenceTransformer(self.model_name)
            self.model = self.model.to(device)

        # settign up data_access, input_folder, output_folder, and fragments_json_folder
        self.data_access: DataAccess = config.get("data_access", None)
        assert self.data_access is not None, f"data_access is missing."
        self.input_folder = self.data_access.get_input_folder()
        assert self.input_folder is not None, f"input_folder is missing."
        self.input_folder = self.input_folder if self.input_folder.endswith("/") else self.input_folder + "/"
        self.output_folder = self.data_access.get_output_folder()
        assert self.output_folder is not None, f"output_folder is missing."
        self.output_folder = self.output_folder if self.output_folder.endswith("/") else self.output_folder + "/"
        if not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder, exist_ok=True)
            except OSError as e:
                self.logger.error(f"Cannot create directories for {self.output_folder}: {e}")

        self.fragments_json_folder = config.get(fragments_json_folder_key, default_fragments_json_folder)
        assert bool(self.fragments_json_folder.strip()), f"fragments_json_folder is missing."
        self.fragments_json_folder = self.fragments_json_folder if self.fragments_json_folder.endswith("/") else self.fragments_json_folder + "/"
        if not os.path.exists(self.fragments_json_folder):
            try:
                os.makedirs(self.fragments_json_folder, exist_ok=True)
            except OSError as e:
                self.logger.error(f"Cannot create directories for {self.fragments_json_folder}: {e}")

        # setting up lanceDB_data_URI, lanceDB_batch_size, lanceDB_buffer, output_files_buffer, lanceDB_total_rows, embedding_batch_size, fragments_count, dataset_name
        self.lanceDB_data_URI = config.get(lanceDB_data_uri_key, default_lanceDB_data_uri_name)
        assert bool(self.lanceDB_data_URI.strip()), f"lanceDB_data_URI is missing."
        if not os.path.exists(self.lanceDB_data_URI):
            try:
                os.makedirs(self.lanceDB_data_URI, exist_ok=True)
            except OSError as e:
                self.logger.error(f"Cannot create directories for {self.lanceDB_data_URI}: {e}")
        self.lanceDB_batch_size = config.get(lanceDB_batch_size_key, default_lanceDB_batch_size)
        self.lanceDB_buffer = []
        self.output_files_buffer = []
        self.lanceDB_total_rows = 0
        self.embedding_batch_size = config.get(embedding_batch_size_key, default_embedding_batch_size)
        self.fragments_count = 0
        self.dataset_name = config.get(dataset_name_key, default_dataset_name)
        assert bool(self.dataset_name.strip()), f"dataset_name is missing."
        

    def _lanceDB_add_table_2_buffer(self, table: pa.Table, file: str):
        self.lanceDB_buffer.append(table)
        self.lanceDB_total_rows += table.num_rows
        self.output_files_buffer.append(file)
        
        if self.lanceDB_total_rows >= self.lanceDB_batch_size:
            self._lanceDB_flush()
    
    def _rearrange_table_order(self, table: pa.Table, desired_order: list[str]) -> pa.Table:
        selected_columns = [table.field(col) for col in desired_order]
        selected_arrays = [table.column(col) for col in desired_order]
        return pa.Table.from_arrays(selected_arrays, schema=pa.schema(selected_columns))

    # This function is used to reorder the schema order in a table for some special cases
    # The cases are due to the last few snapshots of the Gneissweb dataset.
    def _reorder_table_lanceDB_buffer(self):
        buffer = []
        for table in self.lanceDB_buffer:
            # find the schema that starts with "text"
            if 'text' == table.schema.names[0]:
                desired_order = table.column_names
                break
        for table in self.lanceDB_buffer:
            if table.column_names != desired_order:
                table = self._rearrange_table_order(table, desired_order)
            buffer.append(table)
        self.lanceDB_buffer = buffer


    def _cast_columns_in_schema(self, columns_to_cast):
        buffer = []
        for table in self.lanceDB_buffer:
            for col_name in columns_to_cast:
                col_index = table.column_names.index(col_name)
                original_field = table.schema.field(col_name)
                original_array = table.column(col_name)

                if original_field.type != pa.string():
                    # print(f"  Casting '{col_name}' from {original_field.type} to {pa.string()}")
                    # 1. Cast the array data
                    casted_array = original_array.cast(pa.string())
                    
                    # 2. Create the new field definition for this column
                    # Preserve nullability from the original field
                    new_field = pa.field(col_name, pa.string(), nullable=original_field.nullable)
                    
                    # 3. Replace the column in the table (creates a new table)
                    table = table.set_column(col_index, new_field, casted_array)
                # else:
                #     print(f"  Column '{col_name}' already {target_type}, no cast needed.")
                #     pass
            buffer.append(table)        
        self.lanceDB_buffer = buffer



    def _lanceDB_flush(self):
        """Flush the accumulated table data to LanceDB when buffer is full."""
        if not self.lanceDB_buffer:
            return  # No data to flush
        
        # reorder the schema order in a few tables in the lanceDB_buffer.
        # if self.dataset_name == "gneissweb":
        #     self._reorder_table_lanceDB_buffer()

        # casting watsonnlp_top_category0 and others to string as some of them might be null

        # Concatenate all buffered tables
        try:
            if self.dataset_name == "gneissweb":
                columns_to_cast = ['watsonnlp_top_category0', 'watsonnlp_top_category1', 'watsonnlp_top_category2', 'watsonnlp_top_category3']
                self._cast_columns_in_schema(columns_to_cast)
            combined_table = pa.concat_tables(self.lanceDB_buffer)
        except Exception as e:
            self.logger.error(f"pa.concat_tables failed: {e}")

        assert combined_table.num_rows == self.lanceDB_total_rows, f"combined_table num_rows not equal to buffered lanceDB_total_rows"
        
        # write fragments to lanceDB_data_URI
        try:
            fragments = write_fragments(combined_table, self.lanceDB_data_URI, schema=combined_table.schema)
        except Exception as e:
            self.logger.error(f"write_fragments failed: {e}")
                
        # collect fragments json
        fragments_json = [json.dumps(fragment.to_json()) for fragment in fragments]
        frags = {}
        frags["dataset"] = self.dataset_name
        frags["fragment"] = fragments_json       
        frags_bytes = json.dumps(frags).encode("utf-8")     
        frag_path = f"{self.fragments_json_folder}{self.actor_id}_{str(self.fragments_count)}.json"
        # write fragments_json to the fragments_json_folder
        try:
            self.data_access.save_file(frag_path, frags_bytes)
            self.fragments_count += 1
        except Exception as e:
            self.logger.error(f"write frag_json to {self.fragments_json_folder=} failed: {e}")
        # write an empty parquet table to the output folder, to allow DPK checkpointing=True
        empty_batches = []
        empty_table = pa.Table.from_batches(empty_batches, schema=combined_table.schema)
        try:
            for file in self.output_files_buffer:
                file = file.replace(self.input_folder, self.output_folder)
                self.data_access.save_table(file, empty_table)
        except Exception as e:
            self.logger.error(f"write empty pyarrow to {self.output_folder=} failed: {e}")
        
        current_time = datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')
        self.logger.info(f"{self.actor_id} at {current_time} writes {combined_table.num_rows} rows to {self.lanceDB_data_URI}.")

        # Reset buffer
        self.lanceDB_buffer = []
        self.lanceDB_total_rows = 0
        self.output_files_buffer = []
        del combined_table

    # This function is used to create embeddings for a list of documents
    def _compute_embeddings(self, docs: list, embed_batch_size: int) -> list[list[float]]:
        """ given a list of documents, compute their embeddings as a list of list, using sentence_transformer API """
        embeddings = []
        for i in range(0, len(docs), embed_batch_size):
            embed_text_batch = docs[i : i + embed_batch_size]
            try:
                with torch.no_grad():
                    embeddings_batch = self.model.encode(embed_text_batch)
                    embeddings += embeddings_batch.tolist()
            except Exception as e:
                self.logger.error(f"Error: No embeddings created for this batch. Exception: {e}")
                pass
        return embeddings
    
    def _converting_embeddings_list_to_pa_array(self, embeddings_list: list) -> pa.Array:
        assert len(embeddings_list) > 0, f"Empty embeddings_list to convert to pa_array"
        embedding_dtype = pa.list_(pa.float16(), len(embeddings_list[0]))
        embeddings_float16 =  [np.array(emb, dtype=np.float16) for emb in embeddings_list]
        embeddings_pa_array = pa.array(embeddings_float16, type=embedding_dtype)
        return embeddings_pa_array

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """ """
        self.logger.debug(f"Transforming one table with {table.num_rows} rows")

        # make sure that the content column exists
        TransformUtils.validate_columns(table=table, required=[self.content_column_name])

        if not self.embeddings_exist:
            documents = table.column(self.content_column_name).to_pylist()
            embeddings = self._compute_embeddings(documents, self.embedding_batch_size)
            # embedding_dtype = pa.list_(pa.float16(), len(embeddings[0]))
            # embeddings_float16 = [np.array(emb, dtype=np.float16) for emb in embeddings]
            # embeddings_pa_array = pa.array(embeddings_float16, type=embedding_dtype)
            embeddings_pa_array = self._converting_embeddings_list_to_pa_array(embeddings)
            new_table = table.add_column(len(table.schema), self.output_embeddings_column_name, embeddings_pa_array)
        else:
            embeddings = table.column(self.output_embeddings_column_name).to_pylist()
            assert len(embeddings) > 0, f"No embbeddings are loaded from input parquet, {file_name=}"
            embeddings_pa_array = self._converting_embeddings_list_to_pa_array(embeddings)
            new_table = table.set_column(len(table.schema)-1, self.output_embeddings_column_name, embeddings_pa_array)

        self._lanceDB_add_table_2_buffer(new_table, file_name)
        metadata = {"nfiles": 1, "num_rows": new_table.num_rows}
        del new_table
        del table
        return [], metadata
    
    def flush(self) -> tuple[list[pa.Table], dict[str, Any]]:
        self._lanceDB_flush()
        return [], {}


class TextEncoderTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=TextEncoderTransform,
            # remove_from_metadata=[pwd_key],
        )

        self.logger = get_logger(__name__ + "cfg")  # workaround issue #481

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the TextEncoderTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{content_column_name_cli_param}",
            default=default_content_column_name,
            help="Name of the column containing the text to be encoded",
        )
        parser.add_argument(
            f"--{output_embeddings_column_name_cli_param}",
            default=default_output_embeddings_column_name,
            help="Column name to store the embeddings",
        )
        parser.add_argument(
            f"--{model_name_cli_param}",
            default=default_model_name,
            help=f"Name of the HF model to use for encoding the text. The default model is {default_model_name}",
        )
        parser.add_argument(
            f"--{lanceDB_data_uri_cli_param}",
            type=str,
            default=default_lanceDB_data_uri_name,
            required=False,
            help="LanceDB data URI",
        )
        parser.add_argument(
            f"--{lanceDB_batch_size_cli_param}",
            type=int,
            required=False,
            default=default_lanceDB_batch_size,
            help="LanceDB batch size",
        )
        parser.add_argument(
            f"--{embedding_batch_size_cli_param}",
            type=int,
            required=False,
            default=default_embedding_batch_size,
            help="Embedding batch size",
        )
        parser.add_argument(
            f"--{fragments_json_folder_cli_param}",
            type=str,
            required=False,
            default=default_fragments_json_folder,
            help="Fragments JSON file folder",
        )
        parser.add_argument(
            f"--{dataset_name_cli_param}",
            type=str,
            required=False,
            default=default_dataset_name,
            help="Dataset name used to label list of fragment json objects",
        )
        parser.add_argument(
            f"--{embeddings_exist_cli_param}",
            type=bool,
            required=False,
            default=default_embeddings_exist,
            help="A flag indicating whether or not embeddings exist in parquet",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)

        self.params = self.params | captured
        self.logger.info(f"text_encoder parameters are : {self.params}")
        return True
