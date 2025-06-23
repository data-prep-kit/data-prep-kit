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

from data_processing.data_access import DataAccessLocal
from dpk_similarity.transform import SimilarityTransform


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/input"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}

similarity_params = {
    "es_endpoint": None,
    "es_index": "mydata",
    "annotation_column": "similarity_score",
    "doc_text_column": "contents"
}

if __name__ == "__main__":
    data_access = DataAccessLocal(local_conf)
    similarity_params["data_access"] = data_access
    
    # Use the local data access to read a parquet table.
    table, _ = data_access.get_table(os.path.join(input_folder, "test1.parquet"))
    print(f"input table: {table}")

    # Create and configure the transform.
    transform = SimilarityTransform(similarity_params)

    # Transform the table
    table_list, metadata = transform.transform(table)

    for tb in table_list:
        print(f"\noutput table: {tb}")
    print(f"output metadata : {metadata}")
