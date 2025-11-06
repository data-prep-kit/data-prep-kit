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
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_logger
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
embeddings_in_chunks_key="embeddings_in_chunks"
embeddings_max_num_chunks_key="embeddings_max_num_chunks"
embeddings_in_parquet_key="embeddings_in_parquet"
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
embeddings_in_chunks_cli_param = f"{cli_prefix}{embeddings_in_chunks_key}"
embeddings_max_num_chunks_cli_param = f"{cli_prefix}{embeddings_max_num_chunks_key}"
embeddings_in_parquet_cli_param = f"{cli_prefix}{embeddings_in_parquet_key}"
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
default_embeddings_in_chunks = False
default_embeddings_in_parquet = False
default_embeddings_max_num_chunks = 2
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
        embeddings_in_chunks: bool,
        embeddings_in_parquet: bool,
        embeddings_max_num_chunks: int,
        model_max_seq_length: int
    """

    def __init__(self, config: dict[str, Any]):
        """ 
        Make sure that the param name corresponds to the name used in apply_input_params method
        of TextEncoderTransform class
        """
        super().__init__(config)
        from data_processing.utils import get_dpk_logger
<<<<<<< HEAD

=======
>>>>>>> 8f01ca4e7 (replacing existing text_encoder with lanceDB)
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
            self.model.half()
            self.device = torch.device("cuda")  # Use GPU
        else:
            self.logger.info(f"GPU is not available. Using CPU.")
            self.device = torch.device("cpu")   # Use CPU

        self.embeddings_exist = config.get(embeddings_exist_key, default_embeddings_exist)
        self.logger.info(f"{self.embeddings_exist=}")

        self.embeddings_in_parquet = config.get(embeddings_in_parquet_key, default_embeddings_in_parquet)
        self.logger.info(f"{self.embeddings_in_parquet=}")

        self.embeddings_in_chunks = config.get(embeddings_in_chunks_key, default_embeddings_in_chunks)
        self.logger.info(f"{self.embeddings_in_chunks=}")
      
        self.model_max_seq_length = config.get(model_max_seq_length_key, default_model_max_seq_length)
        self.logger.info(f"{self.model_max_seq_length=}")

        self.embeddings_max_num_chunks = config.get(embeddings_max_num_chunks_key, default_embeddings_max_num_chunks)
        self.logger.info(f"{self.embeddings_max_num_chunks=}")

        if not self.embeddings_exist:
            self.model = SentenceTransformer(self.model_name)
            self.model.max_seq_length = self.model_max_seq_length
            self.model.tokenizer.model_max_length = self.model_max_seq_length
            self.model = self.model.to(self.device)

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

        self.embedding_batch_size = config.get(embedding_batch_size_key, default_embedding_batch_size)

        # creating embeddings and storing them in lanceDB
        if not self.embeddings_in_parquet and not self.embeddings_exist:
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
        # if self.lanceDB_table_name == "gneissweb":
        #     self._reorder_table_lanceDB_buffer()

        # casting watsonnlp_top_category0 and others to string as some of them might be null

        # Concatenate all buffered tables
        try:
            # if self.lanceDB_table_name == "gneissweb":
            #     columns_to_cast = ['watsonnlp_top_category0', 'watsonnlp_top_category1', 'watsonnlp_top_category2', 'watsonnlp_top_category3']
            #     self._cast_columns_in_schema(columns_to_cast)
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

    def _chunk_document(self, text: str, chunk_size: int, overlap_size: int) -> List[str]:
        """
        Chunk document into smaller pieces with overlap.
        
        Args:
            text: Input document text
            chunk_size: Size of each chunk in characters.
            overlap_size: overlap between chunks
            
        Returns:
            List of text chunks
        """
        
        # If document is shorter than chunk_size, return as single chunk
        if len(text) <= chunk_size:
            return [text.strip()]
        
        chunks = []
        start = 0
        
        while start < len(text) and len(chunks) < self.embeddings_max_num_chunks:
            end = start + chunk_size
            
            # If not the last chunk, try to break at word boundary
            if end < len(text):
                # Look backwards for a space to avoid breaking words
                space_pos = text.rfind(' ', start, end)
                if space_pos > start:  # Found a space
                    end = space_pos
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position (with overlap)
            start = end - overlap_size
            
            # Prevent infinite loop if overlap is too large
            if len(chunks) > 1 and start <= len(text) - len(chunks[-1]):
                start = end
        
        return chunks


    def get_chunk_embeddings(self, all_chunks: List[str], batch_size: int = 16) -> np.ndarray:
        """
        Get embeddings for all chunks in batches for better efficiency.
        
        Args:
            all_chunks: List of all text chunks
            batch_size: Number of chunks to process at once
            
        Returns:
            Array of embeddings, shape (num_chunks, embedding_dim)
        """
        if not all_chunks:
            raise ValueError("No chunks provided")
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            
            # Generate embeddings for batch
            batch_embeddings = self.model.encode(
                batch, 
                convert_to_numpy=True
            )
            all_embeddings.append(batch_embeddings)
        
        return np.vstack(all_embeddings)


    def _compute_embeddings_in_chunks(self, docs: list, batch_size: int) -> list[list[float]]:
        """
        Take a list of docs, chunk each and append them into all chunks, do embeddings for all chunks in batches and
        finally average chunks of each doc into document-level embeddings and return a list of lists 
        """
        # first phase: chunking docs into all chunks
        all_chunks = []
        doc_chunk_counts = []
        max_seq_length = self.model.max_seq_length
        chars_per_token = 4
        chunk_size = int(0.8 * max_seq_length * chars_per_token)
        overlap_size = int(0.10*chunk_size)
        for document in docs:
            chunks = self._chunk_document(document, chunk_size, overlap_size)
            all_chunks.extend(chunks)
            doc_chunk_counts.append(len(chunks))

        self.logger.info(f"{len(all_chunks)=}")
        # Second phase: process all chunks in batches into all_chunk_embeddings
        document_embeddings = []
        if all_chunks:
            all_chunk_embeddings = self.get_chunk_embeddings(all_chunks, batch_size)

            # group and average chunk-level embeddings back to document-level embeddings
            chunk_idx = 0
            for chunk_count in doc_chunk_counts:
                if chunk_count > 0:
                    doc_chunk_embeddings = all_chunk_embeddings[chunk_idx:chunk_idx + chunk_count]
                    averaged_embedding = np.mean(doc_chunk_embeddings, axis=0)
                    document_embeddings.append(averaged_embedding.tolist())
                    chunk_idx += chunk_count
        self.logger.info(f"{len(document_embeddings)=}")
        return document_embeddings

    # This function is used to create embeddings for a list of documents without chunking
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
            if self.embeddings_in_chunks:
                self.logger.info(f"compute embeddings_in_chunks for {file_name}")
                embeddings = self._compute_embeddings_in_chunks(documents, self.embedding_batch_size)
            else:
                self.logger.info(f"compute embeddings without chunking for {file_name}")
                embeddings = self._compute_embeddings(documents, self.embedding_batch_size)
            # embedding_dtype = pa.list_(pa.float16(), len(embeddings[0]))
            # embeddings_float16 = [np.array(emb, dtype=np.float16) for emb in embeddings]
            # embeddings_pa_array = pa.array(embeddings_float16, type=embedding_dtype)
            embeddings_pa_array = self._converting_embeddings_list_to_pa_array(embeddings)
            new_table = table.add_column(len(table.schema), self.output_embeddings_column_name, embeddings_pa_array)
        else:
            embeddings = table.column(self.output_embeddings_column_name).to_pylist()
            assert len(embeddings) > 0, f"No embbeddings are loaded from input parquet"
            embeddings_pa_array = self._converting_embeddings_list_to_pa_array(embeddings)
            new_table = table.set_column(len(table.schema)-1, self.output_embeddings_column_name, embeddings_pa_array)
        
        if self.embeddings_in_parquet:
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
        if not self.embeddings_in_parquet:
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
            help=f"Name of the HF model to use for encoding the text. The default model is {default_model_name}",
        )
        parser.add_argument(
            f"--{model_max_seq_length_cli_param}",
            type=int,
            required=False,
            default=default_model_max_seq_length,
            help={f"Max number of tokens to use for the model"},
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
            f"--{embeddings_in_chunks_cli_param}",
            type=bool,
            required=False,
            default=default_embeddings_in_chunks,
            help="A flag to indicate whether or not embeddings should be created by chunking the text first",
        )
        parser.add_argument(
            f"--{embeddings_max_num_chunks_cli_param}",
            type=int,
            required=False,
            default=default_embeddings_max_num_chunks,
            help="max num of chunks to create chunk-embeddings for a document",
        )
        parser.add_argument(
            f"--{embeddings_in_parquet_cli_param}",
            type=bool,
            required=False,
            default=default_embeddings_in_parquet,
            help="A flag indicating if embeddings are to be stored in parquet, default=False",
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
