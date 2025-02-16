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

from data_processing.data_access import DataAccessLocal
from dpk_merge.transform import MergeTransform


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
merge_params = {"merge_input_dirs": "test-data/input1,test-data/input2"}

if __name__ == "__main__":
    # Here we show how to run outside the runtime
    # Create and configure the transform.
    data_access = DataAccessLocal()
    data_access.input_folder = input_folder
    merge_params["data_access"] = data_access
    transform = MergeTransform(merge_params)

    file_name = os.path.join(input_folder, "test1.parquet")
    table, _ = data_access.get_table(file_name)
    print(f"file name {file_name} input table: {table}")
    # Transform the table
    table_list, metadata = transform.transform(table, file_name)
    print(f"\noutput table: {table_list}")
    print(f"output metadata : {metadata}")
