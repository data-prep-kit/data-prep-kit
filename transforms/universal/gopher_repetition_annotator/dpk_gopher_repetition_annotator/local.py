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


import json
import logging
import os

from transform import (
    GopherRepetitionAnnotatorTransform,
)
from data_processing.data_access import DataAccessLocal


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/input"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}

agr_params = {}

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
    )
    data_access = DataAccessLocal(local_conf)
    agr_params["data_access"] = data_access
    # Create and configure the transform.
    transform = GopherRepetitionAnnotatorTransform(agr_params)
    # Use the local data access to read a parquet table.
    table, _ = data_access.get_table(os.path.join(input_folder, "test1.parquet"))
    logging.info(f"input table has {table.num_rows} rows")
    # Transform the table
    table_list, metadata = transform.transform(table)
    data_access.save_table(os.path.join(output_folder, "test1.parquet"), table_list[0])
    logging.info(f"{len(table_list)} output tables with {sum([tbl.num_rows for tbl in table_list])} rows")
    metadata_str = json.dumps(metadata, indent=2)
    logging.info(f"output metadata :\n{metadata_str}")
    with open(os.path.join(output_folder, "metadata.json"), "w") as mf:
        mf.write(metadata_str)
