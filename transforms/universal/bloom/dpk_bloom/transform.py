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

from rbloom import Bloom
from hashlib import sha256
from pickle import dumps
from huggingface_hub import hf_hub_download
import os
import warnings
import pandas as pd
import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import TransformUtils, get_logger


class BLOOMTransform(AbstractTableTransform):
    """
    Implements BLOOM transform
    """
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.model_name_or_path = config.get("model_name_or_path", "../bf.bloom")
        self.annotation_column = config.get("annotation_column", "is_in_GneissWeb")
        self.doc_text_column = config.get("doc_text_column", "contents")
        self.batch_size = config.get("batch_size", 1000)
        self.model = Bloom.load(self.model_name_or_path, self._hash_func)
        warnings.warn(
                "We are using the default hash function below. Please verify if it is correct for your Bloom filter configuration.",
                UserWarning
            )
        
    @staticmethod
    def _hash_func(obj):
        h = sha256(dumps(obj)).digest()
        # use sys.byteorder instead of "big" for a small speedup when
        # reproducibility across machines isn't a concern
        return int.from_bytes(h[:16], "big", signed=True)

    def _apply_model(self, data: list, batch_size: int) -> list[float]:
        num_batches = len(data) // batch_size
        data_bloom_label = []
        for i in range(num_batches + 1):
            print(f"Processing batch: {i}/{num_batches}")
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(data))
            if start_idx >= end_idx:
                continue
            data_bloom_label.extend([1 if id in self.model else 0 for id in data[start_idx:end_idx]])
        return data_bloom_label

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Process a table of document text to generate binary label for each document indicating if a document exists in GneissWeb
        :param table: Pyarrow table
        :return: a table with an additional is_in_GneissWeb column
        """
        # make sure that the table contains "contents" column. 
        # TransformUtils.validate_columns(table=table, required=[self.doc_text_column]) #To prevent errors, comment out this line if your Parquet file does not contain the "contents" column. 
        self.df = table.to_pandas()
        df_id_list = []
        for i in range(len(self.df)):
            id_ = self.df.iloc[i]['id'] # Please make sure the UUID column in the Parquet file is named "id."
            df_id_list.append(id_)

        data_bloom_label = self._apply_model(df_id_list, self.batch_size)
        self.df[self.annotation_column] = data_bloom_label
        print(self.df)

        out_table = pa.Table.from_pandas(self.df)
        metadata = {}
        return [out_table], metadata


logger = get_logger(__name__)


class BLOOMTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(name="bloom", transform_class=BLOOMTransform)
        self.params = {}
        self.daf = None

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the BLOOMTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            "--model_name_or_path",
            type=str,
            required=False,
            default="../bf.bloom",
            help="bloom filer model path",
        )

        parser.add_argument(
            "--annotation_column",
            type=str,
            required=False,
            default="is_in_GneissWeb",
            help="label indicating whether the document belongs to GneissWeb",
        )

        parser.add_argument(
            "--doc_text_column",
            type=str,
            required=False,
            default="contents",
            help="The column name that contains the document text",
        )

        parser.add_argument(
            "--inference_engine",
            type=str,
            required=False,
            default="CPU",
            help="inference engine used",
        )

        parser.add_argument(
            "--batch_size",
            type=int,
            required=False,
            default=1000,
            help="batch size",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        self.params["model_name_or_path"] = args.model_name_or_path
        self.params["annotation_column"] = args.annotation_column
        self.params["doc_text_column"] = args.doc_text_column
        self.params["inference_engine"] = args.inference_engine
        self.params["batch_size"] = args.batch_size
        logger.info(f"bloom params are {self.params} ")
        return True
