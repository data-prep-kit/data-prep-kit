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

import tempfile, os
from data_processing.utils import get_logger, TransformUtils
from data_processing.data_access import DataAccessLocal
from data_processing.transform import AbstractTableTransform
from typing import Any

import pyarrow as pa
import json


logger = get_logger(__name__)

expected_schema = pa.schema([
    ('document_id', pa.int64()),
    ('contents', pa.string())
])
data = [
    {"document_id": 1, "contents": "This is the first line used for testing"},
    {"document_id": 2, "contents": "This is the first line used for testing"}
]

def test_read_ndjson():
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "output.ndjson")

        with open(file_path, 'w') as temp_file:
            for item in data:
                json_line = json.dumps(item)
                temp_file.write(json_line + '\n')

            # Get the name (path) of the temporary file
            logger.info(f"Running test with temporary file: {file_path}")

        with open(file_path, 'rb') as file:
            # Read the entire file content as a 'bytes' object
            bytes_data = file.read()
            # Test conversion function
            table = TransformUtils.convert_ndjson_to_arrow (bytes_data)
            assert table.schema==expected_schema, f"Mismatched schema- Received: {table.schema}"
#            logger.info(f"table.schema")


def test_read_zip():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create temporary ndjson file in temporary folder    
        file_path = os.path.join(tmpdir, "output.ndjson")
        with open(file_path, 'w') as temp_file:
            for item in data:
                json_line = json.dumps(item)
                temp_file.write(json_line + '\n')

        import shutil
        # Create a zip archive of a directory
        archive_path=shutil.make_archive('test_archive', 'zip', tmpdir)
        # Read the entire file content as a 'bytes' object
        bytes_data, _ = DataAccessLocal().get_file(path=archive_path)
        table = TransformUtils.convert_zip_to_arrow (bytes_data)
        assert table.schema==expected_schema, f"Mismatched schema- Received: {table.schema}"
#        logger.info(f"{table.schema}")
        os.remove(archive_path)



def test_transform():
    # Define skeleton transform for execising transform_binary
    class TestTransform(AbstractTableTransform):
        def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
            return [table],{}
    
    # setup temporary folder with json file
    with tempfile.TemporaryDirectory() as tmpdir:
        ########## Test using ndjson
        file_path = os.path.join(tmpdir, "output.ndjson")
        with open(file_path, 'w') as temp_file:
            for item in data:
                json_line = json.dumps(item)
                temp_file.write(json_line + '\n')

        # Read the json file content as a 'bytes' object and call transform_binary
        logger.info(f"Running test with json file: {file_path}")
        bytes_data, _ = DataAccessLocal().get_file(path=file_path)
        ret, _ =TestTransform(config={}).transform_binary(file_path, bytes_data)
        table=TransformUtils.convert_binary_to_arrow(data=ret[0][0])
        assert table.schema==expected_schema, f"Mismatched schema- Received: {table.schema}"
        #logger.info(f"{table.schema}")


        ########## Test using jsonl
        file_path = os.path.join(tmpdir, "output.jsonl")
        with open(file_path, 'w') as temp_file:
            for item in data:
                json_line = json.dumps(item)
                temp_file.write(json_line + '\n')

        # Read the json file content as a 'bytes' object and call transform_binary
        logger.info(f"Running test with json file: {file_path}")
        bytes_data, _ = DataAccessLocal().get_file(path=file_path)
        ret, _ =TestTransform(config={}).transform_binary(file_path, bytes_data)
        table=TransformUtils.convert_binary_to_arrow(data=ret[0][0])
        assert table.schema==expected_schema, f"Mismatched schema- Received: {table.schema}"

        ########## Test using zip files
        import shutil
        archive_path=shutil.make_archive('test_archive2', 'zip', tmpdir)
        logger.info(f"Running test with archive file: {archive_path}")

        # Read the entire file content as a 'bytes' object and call transform_binary
        bytes_data, _ = DataAccessLocal().get_file(path=archive_path)
        ret, _ =TestTransform(config={}).transform_binary(archive_path, bytes_data)
        table=TransformUtils.convert_binary_to_arrow(data=ret[0][0])
        assert table.schema==expected_schema, f"Mismatched schema- Received: {table.schema}"
        os.remove(archive_path)




