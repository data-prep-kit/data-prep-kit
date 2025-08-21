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
from pathlib import Path
from data_processing.utils import get_logger, TransformUtils
from data_processing.transform import AbstractTableTransform

class TransformsChain:
    def __init__(self, data_access, transforms):
        self.data_access = data_access
        self.transforms = transforms
        self.logger = get_logger(__name__)

    def run(self):
        for batch_files in self.data_access.get_batches_to_process():
            # changes need to be made for different file types for binary transforms.
            # try to get as table, then get binary file
            for file_path in batch_files:
                self.logger.info(batch_files)
                self.logger.info(f"Processing file: {file_path}")

                # check if parquet file to get table:
                _, ext = os.path.splitext(file_path)
                if ext.lower() == '.parquet':
                    table, _ = self.data_access.get_table(file_path)
                    byte_array = None

                # if not parquet file, get the binary
                else:
                    byte_array, _ = self.data_access.get_file(file_path)
                    table = None

                for transform in self.transforms:
                    # use transform method if transform is abstract table transform
                    if AbstractTableTransform in transform.__class__.__bases__:
                        table_list, metadata = transform.transform(table)
                        if table_list and len(table_list) > 0:
                            table = table_list[0]
                        else:
                            self.logger.info("Transform returned empty, skipping.")
                            continue

                    #assume AbstractBinaryTransform
                    else:
                        # byte_array should be None unless it's the initial input
                        if byte_array is None:
                            byte_array = TransformUtils.convert_arrow_to_binary(table)
                        byte_list, metadata = transform.transform_binary(file_name=file_path, byte_array=byte_array)
                        if byte_list and len(byte_list) > 0:
                            bytes = byte_list[0][0]
                            table = TransformUtils.convert_binary_to_arrow(bytes)
                            byte_array = None
                        else:
                            self.logger.info("Transform returned empty, skipping.")
                            byte_array = None
                            continue


                output_path = os.path.join(self.data_access.get_output_folder(), os.path.basename(file_path))
                output_path = Path(output_path).with_suffix(".parquet")
                self.data_access.save_table(output_path, table)
                self.logger.info(f"Finished processing and saved: {output_path}")
                del table
                gc.collect()
