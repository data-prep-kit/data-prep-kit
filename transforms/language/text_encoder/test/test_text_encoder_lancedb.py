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
import sys
import shutil
import pyarrow.parquet as pq
import pytest
from dpk_text_encoder.lance_commit import main, parse_args
from data_processing.data_access import DataAccessLocal
from dpk_text_encoder.transform import (
   TextEncoderTransform
)

basedir = os.path.abspath(os.path.dirname(__file__))
input_dir = os.path.abspath(os.path.join(basedir, "../test-data/input"))
output_dir = os.path.abspath(os.path.join(basedir, "../output"))
expected_dir = os.path.abspath(os.path.join(basedir, "../test-data/expected_lancedb"))
fragment_dir = os.path.join(output_dir, "fragments_json")
lancedb_uri = os.path.join(output_dir, "test.db")
lancedb_data_uri = os.path.join(output_dir, "test.db/test.lance")
lancedb_table_name = "test"

dal = DataAccessLocal(
    config={
        "input_folder": input_dir,
        "output_folder": output_dir,
    }
)

text_encoder_params = {
    "data_access": dal,
    "model_name": "ibm-granite/granite-embedding-small-english-r2",
    "content_column_name": "contents",
    "output_embeddings_column_name": "embeddings",
    "embedding_batch_size": 5,
    "embeddings_in_lanceDB": True,
    "lanceDB_data_uri": lancedb_data_uri,
    "lanceDB_batch_size": 10,
    "lanceDB_fragments_json_folder": fragment_dir,
    "lanceDB_table_name": lancedb_table_name
}

test_file_name = os.path.join(input_dir, "test1.parquet")

@pytest.fixture(scope="session", autouse=True)
def setup_test_directory():
    """Removes and recreates the test directory once per test session."""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir) 
    os.makedirs(output_dir)
    yield
    # The 'yield' keyword is used for teardown (cleanup after all tests run)


def test_lancedb_lance_commit(monkeypatch, capsys):
    # test embeddings integration with lance db
    text_encoder = TextEncoderTransform(text_encoder_params)
    input_table = pq.read_table(test_file_name)
    print(f"{test_file_name=} {input_table.num_rows=}")
    result, metadata = text_encoder.transform(table=input_table, file_name=test_file_name)
    assert metadata['num_rows'] == 15
    assert metadata['nfiles'] == 1

    # test lance_commit
    mock_args = [
        "lance_commit.py",
        "--lanceDB_storage_type", "local",
        "--lanceDB_uri", lancedb_uri,
        "--lanceDB_data_uri", lancedb_data_uri,
        "--lanceDB_table_name", "test",
        "--lanceDB_fragments_json_folder", fragment_dir,
        "--lanceDB_table_schema_folder", output_dir
    ]
    monkeypatch.setattr(sys, 'argv', mock_args)
    parsed_args = parse_args(sys.argv[1:]) 
    main(parsed_args)
    captured = capsys.readouterr()
    output_text = captured.out
    lines = output_text.strip().splitlines()
    assert "lance completed the commit" in lines[-1], f"lance commit failed."
