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

import pytest
from data_processing.utils import get_logger
from data_processing.data_access import DataAccessFactory

logger = get_logger(__name__)

da_module='data_processing.data_access_lh'
da_class='DataAccessLakeHouse'

# Configure lakehouse unit test tables
lakehouse_config = {
    "lh_environment": "STAGING",
    "input_table": 'ibmdatapile.academic.ieee', 
    "input_dataset": "",
    "input_version": "main",
    "output_table": 'processed.ibmdatapile.academic.ieee.lh_unittest', 
    "output_path": 'lh-test/tables/processed/ibmdatapile/academic/ieee/lh_unittest', 
    # Running these tests requires the credentials to be provided in the env vars.
}


def test_DF():
    logger.info("Create Data Access Object using Factory")
    daf=DataAccessFactory()
    args={
            "data_lh_config":lakehouse_config,
            "data_da_class": da_class,
            "data_da_module": da_module,
            }
    daf.apply_input_params(args=args)
    d_a=daf.create_data_access()

    assert d_a 
    logger.info("Created Data Access Object using Factory")

    output_folder=d_a.get_output_folder()
    logger.info(f"Data Access Object Created- Output Folder is: {output_folder}")
    logger.info(f"Data Access Object Created- Input Folder is: {d_a.lh.get_input_data_path()}")

    files = d_a.get_files_to_process()
    logger.info(f"got {len(files[0])} files to process with checkpoint False")
    logger.info(f"List of files to process: {files[0]}")
    assert 12 == len(files[0])

if __name__ == "__main__":
    test_DF()
