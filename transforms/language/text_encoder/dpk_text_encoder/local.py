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
import shutil

from data_processing.data_access import DataAccessLocal
from dpk_text_encoder.transform import (
    TextEncoderTransform,
    embeddings_in_parquet_key,
    model_name_key,
    content_column_name_key,
    output_embeddings_column_name_key,

)

# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}

embeddings_params = {
    embeddings_in_parquet_key: True,
    model_name_key: "ibm-granite/granite-embedding-small-english-r2",
    content_column_name_key: "contents",
    output_embeddings_column_name_key: "embeddings",
}

input_file_name = os.path.join(input_folder, "test1.parquet")

if __name__ == "__main__":

    # import pyarrow as pa
    # from data_processing.utils import TransformUtils
    # table = pa.Table.from_pylist([
    #     {"contents": "This is a transform which is encoding text."},
    #     {"contents": "There is no one who loves pain itself, who seeks after it and wants to have it, simply because it is pain."},
    # ])
    # with open("text1.parquet", "wb") as fp:
    #     fp.write(TransformUtils.convert_arrow_to_binary(table))

    # Here we show how to run outside of the runtime
    # Create and configure the transform.
        # Use the local data access to read a parquet table.
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder) 
    os.makedirs(output_folder)
    data_access = DataAccessLocal(local_conf)
    embeddings_params["data_access"] = data_access
    transform = TextEncoderTransform(embeddings_params)
    table, _ = data_access.get_table(os.path.join(input_folder, "test1.parquet"))
    print(f"{table.num_rows=}")
    # Transform the table
    table_list, metadata = transform.transform(table=table, file_name=input_file_name)
    print(f"\noutput table: {table_list[0].num_rows=}")
    print(f"output metadata : {metadata}")
