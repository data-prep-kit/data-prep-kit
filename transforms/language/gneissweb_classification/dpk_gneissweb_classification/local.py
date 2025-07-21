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
from dpk_gneissweb_classification.transform import (
    ClassificationTransform,
    content_column_name_cli_param,
    model_credential_cli_param,
    model_file_name_cli_param,
    model_url_cli_param,
    n_processes_cli_param,
    output_label_column_name_cli_param,
    output_score_column_name_cli_param
)


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))

classification_params = {
    model_credential_cli_param: os.environ.get('HF_READ_ACCESS_TOKEN', "PUT YOUR OWN HUGGINGFACE CREDENTIAL"),
    model_file_name_cli_param: ["['fasttext_medical.bin']"],
    model_url_cli_param:["['ibm-granite/GneissWeb.Med_classifier']"],
    output_label_column_name_cli_param:["['label_med']"],
    output_score_column_name_cli_param:["['score']"],
    content_column_name_cli_param: "text",
    n_processes_cli_param: 1,
}


if __name__ == "__main__":
    # Here we show how to run outside of the runtime
    # Create and configure the transform.
    transform = ClassificationTransform(classification_params)
    # Use the local data access to read a parquet table.
    data_access = DataAccessLocal()
    table, _ = data_access.get_table(os.path.join(input_folder, "test_01.parquet"))
    print(f"input table: {table}")
    # Transform the table
    try:
        table_list, metadata = transform.transform(table)
        print(f"\noutput table: {table_list}")
        print(f"output metadata : {metadata}")
    except Exception as e:
        print(f"Exception executing transform {e}")
