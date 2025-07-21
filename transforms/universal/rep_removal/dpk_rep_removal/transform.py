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
import subprocess
import tempfile
import pyarrow as pa
import pandas as pd
from dpk_rep_removal.dedup_pq_level import load_pq_docs_once_avoidIO, extract_dup_per_doc_avoidIO_further, save_deduped_pq_once
from dpk_rep_removal.dedup_Rust_scripts import find_repeated_substrings, collect_duplicates_avoidIO
from typing import Any
from psutil import cpu_count
from dpk_rep_removal.make_suffix_array import make_suffix_array
from data_processing.transform import AbstractTableTransform
from data_processing.utils import get_logger
logging = get_logger(__name__, level="INFO")


class RepRemovalTransform(AbstractTableTransform):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        self.contents_column_name = config.get("rep_removal_contents_column_name", "contents")
        self.dedup_level = config.get("rep_removal_dedup_level_name", "parquet")
        self.length_thresh = str(config.get("rep_removal_length_thresh", 5))
        self.frequency_threshold = str(config.get("rep_removal_frequency_threshold", 1))
        self.retain_first_copy = str(config.get("rep_removal_retain_first_copy", True))
        self.tokenize = str(config.get("rep_removal_tokenize", True))
        self.num_threads = str(config.get("rep_removal_num_threads", cpu_count(logical=False)))
        self.num_cpus = str(config.get("rep_removal_num_cpus", cpu_count(logical=False)))

        if self.retain_first_copy.lower() == 'false':
            self.retain_first_copy = False

        else:
            self.retain_first_copy = True

        pwd = os.path.dirname(__file__)
        manifest_path = f"{pwd}/rust/"
        cmd = f"cargo install --path {manifest_path}"
        subprocess.run(cmd, shell=True, capture_output=True, text=True)

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """ """
        pq_df = table.to_pandas()
        try:
            with tempfile.TemporaryDirectory() as td:
                save_dir = os.path.join(td, 'save_dir')
                logging.info("encoding parquet")
                encoded_pq = os.path.join(save_dir, self.dedup_level)
                load_pq_docs_once_avoidIO(pq_df, self.contents_column_name, save_dir, self.dedup_level,
                                          self.tokenize, int(self.num_threads))

                cache_dir = os.path.join(td, 'cache')
                temp_dir = os.path.join(td, 'tmp')
                os.makedirs(cache_dir)
                os.makedirs(temp_dir)

                logging.info("making suffix array")
                make_suffix_array(encoded_pq, temp_dir, self.dedup_level, int(self.num_threads), int(self.num_cpus))
                logging.info("finding repeated substrings")
                find_repeated_substrings(encoded_pq, self.length_thresh, cache_dir, self.num_threads,
                                         self.frequency_threshold, self.retain_first_copy)
                logging.info("collecting duplicates")
                repeated_pairs = collect_duplicates_avoidIO(encoded_pq, self.length_thresh, cache_dir)

                # no duplicates found
                if 'out' not in repeated_pairs:
                    return [], {"duplicates_found": 0}

                extract_dup_per_doc_avoidIO_further(repeated_pairs)
                output_pq = os.path.join(td, 'output.parquet')
                pre_content_col_size, deduped_content_col_size = save_deduped_pq_once(pq_df, output_pq,
                                                                                      self.contents_column_name,
                                                                                      self.num_threads,
                                                                                      self.tokenize)

                duplicates_found = len(repeated_pairs[repeated_pairs.index('out') + 1:-1])
                logging.info(f"Num Duplicate Rows: {duplicates_found}")
                metadata = {
                    "pre_content col size": pre_content_col_size,
                    "rep_removed_content col size": deduped_content_col_size,
                    "duplicates_found": duplicates_found,
                }

            # add deduped to res table
                deduped_table = pd.read_parquet(output_pq)
                res_table = pa.Table.from_pandas(deduped_table)

                return [res_table], metadata

        except Exception as e:
            logging.error(e)
            return [], {}
