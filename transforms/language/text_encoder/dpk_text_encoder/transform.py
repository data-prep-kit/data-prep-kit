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

import time, datetime
import torch
from argparse import ArgumentParser, Namespace
from typing import Any
import numpy as np
import random
import lance
import os
import json
from pathlib import Path
from typing import List
from lance.fragment import write_fragments

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_dpk_logger
from sentence_transformers import SentenceTransformer
from data_processing.data_access import DataAccess

try:
    import ray
    RAY_INSTALLED = True
except ImportError:
    RAY_INSTALLED = False


short_name = "text_encoder"
cli_prefix = f"{short_name}_"

model_name_key = "model_name"
content_column_name_key = "content_column_name"
output_embeddings_column_name_key = "output_embeddings_column_name"
lanceDB_data_uri_key="lanceDB_data_uri"
lanceDB_batch_size_key="lanceDB_batch_size"
embedding_batch_size_key="embedding_batch_size"
lanceDB_fragments_json_folder_key="lanceDB_fragments_json_folder"
lanceDB_table_name_key="lanceDB_table_name"
embeddings_exist_key="embeddings_exist"
embeddings_in_lanceDB_key="embeddings_in_lanceDB"
model_max_seq_length_key="model_max_seq_length"

model_name_cli_param = f"{cli_prefix}{model_name_key}"
content_column_name_cli_param = f"{cli_prefix}{content_column_name_key}"
output_embeddings_column_name_cli_param = f"{cli_prefix}{output_embeddings_column_name_key}"
lanceDB_data_uri_cli_param = f"{cli_prefix}{lanceDB_data_uri_key}"
lanceDB_batch_size_cli_param = f"{cli_prefix}{lanceDB_batch_size_key}"
embedding_batch_size_cli_param = f"{cli_prefix}{embedding_batch_size_key}"
lanceDB_fragments_json_folder_cli_param = f"{cli_prefix}{lanceDB_fragments_json_folder_key}"
lanceDB_table_name_cli_param = f"{cli_prefix}{lanceDB_table_name_key}"
embeddings_exist_cli_param = f"{cli_prefix}{embeddings_exist_key}"
embeddings_in_lanceDB_cli_param = f"{cli_prefix}{embeddings_in_lanceDB_key}"
model_max_seq_length_cli_param = f"{cli_prefix}{model_max_seq_length_key}"

default_model_name = "ibm-granite/granite-embedding-small-english-r2"
default_content_column_name = "contents"
default_output_embeddings_column_name = "embeddings"
default_lanceDB_data_uri_name = ""
default_lanceDB_batch_size = 524288
default_embedding_batch_size = 8
default_lanceDB_fragments_json_folder = ""
default_lanceDB_table_name = ""
default_embeddings_exist = False
default_embeddings_in_lanceDB = False
default_model_max_seq_length = 2048


class TextEncoderTransform(AbstractTableTransform):
    """
    This class is used to encode text into embeddings. It uses the sentence-transformers library.
    The config dictionary should contain the following keys:
        model_name: str,
        content_column_name: str,
        output_embeddings_column_name: str,
        lanceDB_data_uri_name: str,
        lanceDB_batch_size: int,
        embedding_batch_size: int,
        lanceDB_fragments_json_folder: str,
        lanceDB_table_name: str,
        embeddings_exist: bool,
        embeddings_in_lanceDB: bool,
        model_max_seq_length: int
    """

    def __init__(self, config: dict[str, Any]):
        """ 
        Make sure that the param name corresponds to the name used in apply_input_params method
        of TextEncoderTransform class
        """
        super().__init__(config)
        from data_processing.utils import get_dpk_logger
        self.logger = get_dpk_logger()

        self.model_name = config.get(model_name_key, default_model_name)
        self.content_column_name = config.get(content_column_name_key, default_content_column_name)
        self.output_embeddings_column_name = config.get(
            output_embeddings_column_name_key, default_output_embeddings_column_name
        )
        if RAY_INSTALLED:
            if ray.is_initialized():
            # keep the actor_id for creating part of the frangments_json file written by individual workers
                self.actor_id = ray.get_runtime_context().get_actor_id()
            else:
                self.actor_id = "xxx"
        else:
            self.actor_id = "xxx"

        if torch.cuda.is_available():
            self.logger.info(f"GPU is available!")
            self.device = torch.device("cuda")  # Use GPU
        else:
            self.logger.info(f"GPU is not available. Using CPU.")
            self.device = torch.device("cpu")   # Use CPU

        self.embeddings_exist = config.get(embeddings_exist_key, default_embeddings_exist)
        self.logger.info(f"{self.embeddings_exist=}")

        self.embeddings_in_lanceDB = config.get(embeddings_in_lanceDB_key, default_embeddings_in_lanceDB)
        self.logger.info(f"{self.embeddings_in_lanceDB=}")

        self.model_max_seq_length = config.get(model_max_seq_length_key, default_model_max_seq_length)
        self.logger.info(f"{self.model_max_seq_length=}")

        if not self.embeddings_exist:
            self.model = SentenceTransformer(self.model_name)
            self.model.max_seq_length = self.model_max_seq_length
            self.model.tokenizer.model_max_length = self.model_max_seq_length
            self.model = self.model.to(self.device)
            if torch.cuda.is_available():
                self.model.half()
            
        
        self.embedding_batch_size = config.get(embedding_batch_size_key, default_embedding_batch_size)

        # creating embeddings and storing them in lanceDB
        if self.embeddings_in_lanceDB:
            # settign up data_access, input_folder, output_folder, and lanceDB_fragments_json_folder
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

            self.lanceDB_fragments_json_folder = config.get(lanceDB_fragments_json_folder_key, default_lanceDB_fragments_json_folder)
            assert bool(self.lanceDB_fragments_json_folder.strip()), f"lanceDB_fragments_json_folder is missing."
            self.lanceDB_fragments_json_folder = self.lanceDB_fragments_json_folder if self.lanceDB_fragments_json_folder.endswith("/") else self.lanceDB_fragments_json_folder + "/"
            if not os.path.exists(self.lanceDB_fragments_json_folder):
                try:
                    os.makedirs(self.lanceDB_fragments_json_folder, exist_ok=True)
                except OSError as e:
                    self.logger.error(f"Cannot create directories for {self.lanceDB_fragments_json_folder}: {e}")

            # setting up lanceDB_data_URI, lanceDB_batch_size, lanceDB_buffer, output_files_buffer, lanceDB_total_rows, embedding_batch_size, fragments_count, lanceDB_table_name
            self.lanceDB_data_URI = config.get(lanceDB_data_uri_key, default_lanceDB_data_uri_name)
            assert bool(self.lanceDB_data_URI.strip()), f"lanceDB_data_URI is missing."
            path = Path(self.lanceDB_data_URI)
            assert path.suffix == ".lance", f"{lanceDB_data_uri_key} does not end with '.lance'. Found suffix: '{path.suffix}'"
            if not os.path.exists(self.lanceDB_data_URI):
                try:
                    os.makedirs(self.lanceDB_data_URI, exist_ok=True)
                except OSError as e:
                    self.logger.error(f"Cannot create directories for {self.lanceDB_data_URI}: {e}")
            self.lanceDB_batch_size = config.get(lanceDB_batch_size_key, default_lanceDB_batch_size)
            self.fragments_count = 0
            self.lanceDB_table_name = config.get(lanceDB_table_name_key, default_lanceDB_table_name)
            assert bool(self.lanceDB_table_name.strip()), f"lanceDB_table_name is missing."
            self.lanceDB_buffer = []
            self.output_files_buffer = []
            self.lanceDB_total_rows = 0
        

    def _lanceDB_add_table_2_buffer(self, table: pa.Table, file: str):
        self.lanceDB_buffer.append(table)
        self.lanceDB_total_rows += table.num_rows
        self.output_files_buffer.append(file)
        
        if self.lanceDB_total_rows >= self.lanceDB_batch_size:
            self._lanceDB_flush()
    

    def _lanceDB_flush(self):
        """Flush the accumulated table data to LanceDB when buffer is full."""
        if not self.lanceDB_buffer:
            return  # No data to flush
        
        # Concatenate all buffered tables
        try:
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
        frags["dataset"] = self.lanceDB_table_name
        frags["fragment"] = fragments_json       
        frags_bytes = json.dumps(frags).encode("utf-8")
        frag_path = f"{self.lanceDB_fragments_json_folder}{self.actor_id}_{str(self.fragments_count)}.json"
        # write fragments_json to the lanceDB_fragments_json_folder
        try:
            self.data_access.save_file(frag_path, frags_bytes)
            self.fragments_count += 1
        except Exception as e:
            self.logger.error(f"write frag_json to {self.lanceDB_fragments_json_folder=} failed: {e}")
        # write an empty parquet table to the output folder, to allow DPK checkpointing=True
        empty_batches = []
        empty_table = pa.Table.from_batches(empty_batches, schema=combined_table.schema)
        try:
            for file in self.output_files_buffer:
                file = file.replace(self.input_folder, self.output_folder)
                self.data_access.save_table(file, empty_table)
                self.logger.info(f"{self.input_folder=} {self.output_folder=} writing empty_table to {file}")
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
        all_embeddings_batches = [] # Temporary list to hold NumPy arrays

        for i in range(0, len(docs), embed_batch_size):
            embed_text_batch = docs[i : i + embed_batch_size]
            try:
                # 1. Ensure no gradient calculation
                with torch.no_grad():
                    # self.model.encode returns a NumPy array by default
                    embeddings_batch = self.model.encode(
                        embed_text_batch,
                        device = self.model.device,
                        convert_to_numpy=True # Explicitly ensure NumPy output
                    )
                    
                    # 2. Append the NumPy array (batch) to the temporary list
                    all_embeddings_batches.append(embeddings_batch)
                    
            except Exception as e:
                self.logger.error(f"Error: No embeddings created for this batch. Exception: {e}")
                pass # Skip batch on error

        # 3. Concatenate all NumPy arrays once at the end
        if all_embeddings_batches:
            final_embeddings_array = np.concatenate(all_embeddings_batches, axis=0)
            # 4. Convert the final, complete array to a list[list[float]]
            return final_embeddings_array.tolist()
        else:
            return []
        
    
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
            self.logger.info(f"compute embeddings for {file_name}.")
            embeddings = self._compute_embeddings(documents, self.embedding_batch_size)
            embeddings_pa_array = self._converting_embeddings_list_to_pa_array(embeddings)
            new_table = table.add_column(len(table.schema), self.output_embeddings_column_name, embeddings_pa_array)
        else:
            embeddings = table.column(self.output_embeddings_column_name).to_pylist()
            assert len(embeddings) > 0, f"Embeddings are not available in parquet."
            embeddings_pa_array = self._converting_embeddings_list_to_pa_array(embeddings)
            new_table = table.set_column(len(table.schema)-1, self.output_embeddings_column_name, embeddings_pa_array)
        
        if not self.embeddings_in_lanceDB:
            metadata = {"num_rows": new_table.num_rows}
            return [new_table], metadata
        else:
            self._lanceDB_add_table_2_buffer(new_table, file_name)
            metadata = {"nfiles": 1, "num_rows": new_table.num_rows}
            del new_table
            del table
            self.logger.info(f"finished embeddings for {file_name}")
            return [], metadata
    
    def flush(self) -> tuple[list[pa.Table], dict[str, Any]]:
        if self.embeddings_in_lanceDB:
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
        from data_processing.utils import get_dpk_logger

        self.logger = get_dpk_logger() 

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the TextEncoderTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{content_column_name_cli_param}",
            type=str,
            required=False,
            default=default_content_column_name,
            help="Name of the column containing the text to be encoded",
        )
        parser.add_argument(
            f"--{output_embeddings_column_name_cli_param}",
            type=str,
            required=False,
            default=default_output_embeddings_column_name,
            help="Column name to store the embeddings",
        )
        parser.add_argument(
            f"--{model_name_cli_param}",
            type=str,
            required=False,
            default=default_model_name,
            help="Name of the HF model to use for encoding the text.",
        )
        parser.add_argument(
            f"--{model_max_seq_length_cli_param}",
            type=int,
            required=False,
            default=default_model_max_seq_length,
            help="Max number of tokens to use for the model",
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
            f"--{lanceDB_fragments_json_folder_cli_param}",
            type=str,
            required=False,
            default=default_lanceDB_fragments_json_folder,
            help="Fragments JSON file folder",
        )
        parser.add_argument(
            f"--{lanceDB_table_name_cli_param}",
            type=str,
            required=False,
            default=default_lanceDB_table_name,
            help="Dataset name used to label list of fragment json objects",
        )
        parser.add_argument(
            f"--{embeddings_exist_cli_param}",
            type=bool,
            required=False,
            default=default_embeddings_exist,
            help="A flag indicating whether or not embeddings exist in parquet",
        )
        parser.add_argument(
            f"--{embeddings_in_lanceDB_cli_param}",
            type=bool,
            required=False,
            default=default_embeddings_in_lanceDB,
            help="A flag indicating if embeddings are to be stored in lanceDB, default=False",
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
