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

logger = get_logger(__name__)
from data_processing.data_access_lh import DataAccessLakeHouse, DPKConfigLH

# Configure lakehouse unit test tables
lakehouse_config = {
    "lh_environment": "STAGING",
    "input_table": 'ibmdatapile.academic.ieee', 
    "input_dataset": "",
    "input_version": "main",
    "output_table": 'processed.ibmdatapile.academic.ieee.lh_unittest', 
    "output_path": 'lh-test/tables/processed/ibmdatapile/academic/ieee/lh_unittest', 
    # Running these tests requires the credentials to be provided in the env vars.
    "token": DPKConfigLH.LAKEHOUSE_TOKEN,
}



@pytest.mark.skipif(
    DPKConfigLH.LAKEHOUSE_TOKEN is None, reason="LAKEHOUSE_TOKEN needs to be set, generally via env vars"
)
def test_credentials():
    logger.info("Checking Credentials set... ")
    assert DPKConfigLH.S3_ACCESS_KEY, "Missing S3 Access Key: Must be set via env variables"
    assert DPKConfigLH.S3_SECRET, "Missing S3 Secret: Must be set via env variables"
    assert DPKConfigLH.S3_ENDPOINT, "Missing Endpoint URL: Must be set via env variables"
    logger.info("Credentials set... ")


@pytest.mark.skipif(
    DPKConfigLH.LAKEHOUSE_TOKEN is None, reason="LAKEHOUSE_TOKEN needs to be set, generally via env vars"
)
def test_get_output_folder():

    logger.info("Created Data Access Object ")
    # create data access
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=None, checkpoint=False, m_files=-1
    )
    logger.info("Data Access Object Created ")

    output_folder=d_a.get_output_folder()
    logger.info(f"Data Access Object Created- Output Folder is: {output_folder}")

    logger.info(f"Data Access Object Created- Input Folder is: {d_a.lh.get_input_data_path()}")


@pytest.mark.skipif(
    DPKConfigLH.LAKEHOUSE_TOKEN is None, reason="LAKEHOUSE_TOKEN needs to be set, generally via env vars"
)
def test_get_folder():
    """
    Testing get folder
    :return: None
    """
    # create data access
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=None, checkpoint=False, m_files=-1
    )
    # get the folder
    files = d_a.get_files_to_process()
    logger.info(f"got {len(files[0])} files to process with checkpoint False")
    logger.info(f"List of files to process: {files[0]}")
    assert 1 == len(files[0])


@pytest.mark.skipif(
    DPKConfigLH.LAKEHOUSE_TOKEN is None, reason="LAKEHOUSE_TOKEN needs to be set, generally via env vars"
)
def test_table_read_write():
    """
    Testing table read/write
    :return: None
    """
    logger.info("Created Data Access Object ")
    # create data access
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=None, checkpoint=False, m_files=-1
    )
    logger.info("Data Access Object Created ")

    input_location = (
        "lh-test/tables/academic/ieee/data/version=0.0.1/"
        "language=en/00000-1-345d10e3-ed3c-46b3-8f0d-cb81af19898b-00001.parquet"
    )
    # read the table
    logger.info(f"Reading table with path: {input_location}")
    r_table, retries = d_a.get_table(path=input_location)
    r_columns = r_table.column_names
    logger.info(f"number of columns in the read table {len(r_columns)}, number of rows {r_table.num_rows}")
    assert 6220 == r_table.num_rows
    assert 14 == len(r_columns)
    # get table output location
    output_location = d_a.get_output_location(input_location)
    logger.info(f"Output location {output_location}")
    assert (
        "lh-test/tables/processed/ibmdatapile/academic/ieee/lh_unittest/data/version=0.0.1/"
        "language=en/00000-1-345d10e3-ed3c-46b3-8f0d-cb81af19898b-00001.parquet" == output_location
    )
    # save the table
    l, result = d_a.save_table(path=output_location, table=r_table)
    logger.info(f"length of saved table {l}, result {result}")
    assert 148378677 == l
    w_table, _ = d_a.get_table(path=output_location)
    s_columns = w_table.column_names
    assert len(r_columns) == len(s_columns)
    assert r_columns == s_columns


@pytest.mark.skipif(
    DPKConfigLH.LAKEHOUSE_TOKEN is None, reason="LAKEHOUSE_TOKEN needs to be set, generally via env vars"
)
def test_get_todo_list():
    """
    Testing get todo list by setting checkpoint to True
    : return: None
    """
    # create data access
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=None, checkpoint=True, m_files=-1
    )

    print(f"got {len(d_a.get_files_to_process()[0])} files to process with checkpoint True")
    assert 1 == len(d_a.get_files_to_process()[0])


@pytest.mark.skipif(
    DPKConfigLH.LAKEHOUSE_TOKEN is None, reason="LAKEHOUSE_TOKEN needs to be set, generally via env vars"
)
def test_files_to_process():
    """
    Testing get files to process
    :return: None
    """
    # get files to process with checkpoint set to False
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=None, checkpoint=False, m_files=-1
    )
    files, profile, _ = d_a.get_files_to_process()
    logger.info(f"files with checkpointing set to False {len(files)}, profile {profile}")
    assert 1 == len(files)
    assert 206.60683917999268 == profile["max_file_size"]
    assert 0.00907135009765625 == profile["min_file_size"]
    assert 1240.2788639068604 == profile["total_file_size"]

    # use checkpoint
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=None, checkpoint=True, m_files=-1
    )
    files, profile, _ = d_a.get_files_to_process()
    logger.info(f"files with checkpointing set to True {len(files)}, profile {profile}")
    assert 1 == len(files)
    assert 206.60683917999268 == profile["max_file_size"]
    assert 0.00907135009765625 == profile["min_file_size"]
    assert 1114.7140340805054 == profile["total_file_size"]

    # using data sets

    lakehouse_config["input_table"] = "ibmdatapile.academic.doabooks"
    lakehouse_config["input_dataset"] = "dataset:doabooks"

    logger.info(f"Repeating run using dataset {lakehouse_config['input_dataset']}")
    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=["doabooks"], checkpoint=False, m_files=-1
    )
    files, profile, _ = d_a.get_files_to_process()
    logger.info(f"using data sets files {len(files)}, profile {profile}")
    assert 1 == len(files)
    assert 150 == profile["max_file_size_MB"]
    assert 150 == profile["min_file_size_MB"]
    assert 6600 == profile["total_file_size_MB"]

    # using data sets with checkpointing
    logger.info(f"Repeating run with checkpointing True using dataset {lakehouse_config['input_dataset']}")

    d_a = DataAccessLakeHouse(
        config=lakehouse_config, d_sets=["doabooks"], checkpoint=True, m_files=-1
    )
    files, profile, _ = d_a.get_files_to_process()
    logger.info(f"using data sets files {len(files)}, profile {profile}")
    assert 1 == len(files)
    assert 150 == profile["max_file_size_MB"]
    assert 150 == profile["min_file_size_MB"]
    assert 6600 == profile["total_file_size_MB"]


if __name__ == "__main__":
    test_credentials()
    test_get_output_folder()
    test_table_read_write()
    test_get_folder()
    test_get_todo_list()
    test_files_to_process()
