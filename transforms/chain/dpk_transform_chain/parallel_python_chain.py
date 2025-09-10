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
import gc
import concurrent.futures
from pathlib import Path
from data_processing.utils import get_logger, TransformUtils


class ParallelTransformsChain:
    def __init__(self, data_access, transforms, max_workers=4):
        """
        data_access: instance of DataAccessLocal or DataAccessS3
        transforms: list of transform instances (each has .transform(table) interface)
        max_workers: number of worker processes to run concurrently
        """
        self.data_access = data_access
        self.transforms = transforms
        self.max_workers = max_workers
        self.logger = get_logger(__name__)

    def run(self):
        batches = list(self.data_access.get_batches_to_process())

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(self.process_batch, batches)

    def process_batch(self, batch_files):
        for file_path in batch_files:
            self.logger.info(batch_files)
            self.logger.info(f"Processing file: {file_path}")

            # depending on head transform (i.e. docling, web2parquet), original file path could be non parquet,
            # which would be a problem for other table transforms expecting input extension to be parquet
            # to counter, change ext. to parquet after the first transform to be safe.
            first = True

            # get raw bytes from file
            byte_array, _ = self.data_access.get_file(file_path)

            for transform in self.transforms:
                # use transform_binary to accommodate table and binary transform calls
                if first:
                    fp = file_path
                    first = False
                else:
                    fp = Path(file_path).with_suffix(".parquet")

                byte_list, metadata = transform.transform_binary(file_name=fp, byte_array=byte_array)

                if byte_list and len(byte_list) > 0:
                    byte_array = byte_list[0][0]

                else:
                    self.logger.info("Transform returned empty, skipping.")
                    continue

            output_path = os.path.join(self.data_access.get_output_folder(), os.path.basename(file_path))
            output_path = Path(output_path).with_suffix(".parquet")
            self.data_access.save_file(output_path, byte_array)
            self.logger.info(f"Finished processing and saved: {output_path}")
            del byte_array
            gc.collect()
