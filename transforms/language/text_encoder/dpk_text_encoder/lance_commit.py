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

import lancedb
import lance
from pyarrow import fs
import io
import pyarrow.parquet as pq
import json
from lance import FragmentMetadata
import argparse
import os
import sys


def setup_s3(access_key: str, secret_key: str, endpoint: str) -> fs.S3FileSystem:
    try:
        s3 = fs.S3FileSystem(
            access_key=access_key,
            secret_key=secret_key,
            request_timeout=10,
            connect_timeout=10,
            retry_strategy=fs.AwsStandardS3RetryStrategy(max_attempts=10),
            endpoint_override=endpoint,
        )
    except Exception as e:
        print(f"Error: Incorrect parameters for setting up fs.S3FileSystem(). {e}")
        print(f"{access_key=} {secret_key=} {endpoint=}")
        exit(1)
    return s3

def get_fragments_json(s3: fs.S3FileSystem, json_folder: str) -> list:
    all_fragments_json = []
    # read in the fragment jsons
    total_rows = 0
    files = [file for file in s3.get_file_info(fs.FileSelector(json_folder))]
    for j, file in enumerate(files):
        if file.type == fs.FileType.File and file.path.endswith(".json"):
            try:
                with s3.open_input_stream(file.path) as f:
                    # Read the content as bytes
                    json_bytes = f.readall()
                    # Decode the bytes to a UTF-8 string
                    json_string = json_bytes.decode('utf-8')
                    # Parse the JSON string
                    data = json.loads(json_string)
                    fragment = data['fragment']
                    for index, json_str in enumerate(fragment):
                        data_dict = json.loads(json_str)
                        if "physical_rows" in data_dict.keys():
                            total_rows += data_dict["physical_rows"]
                    all_fragments_json += fragment
            except Exception as e:
                print(f"cannot get json loaded: {e}")
                pass
    print(f"{all_fragments_json=}")
    print(f"{total_rows=}")
    return all_fragments_json

def commit_fragments(s3: fs.S3FileSystem, all_fragments_json: list, schema_folder: str, dataset_uri:str):

    all_fragments = [FragmentMetadata.from_json(f) for f in all_fragments_json]
    files = [file for file in s3.get_file_info(fs.FileSelector(schema_folder, recursive=True))]
    for file in files:
        if file.type == fs.FileType.File and file.path.endswith(".parquet"):
            try:
                print(f"{file.path=}")
                with s3.open_input_stream(file.path) as f: 
                    parquet_bytes = f.readall()
                    # Create a BytesIO object from the bytes, which is seekable
                    buffer = io.BytesIO(parquet_bytes)
                    table = pq.read_table(buffer)
                    schema = table.schema
                    print(f"find schema for the lance fragments")
                    break
            except Exception as e: 
                print(f"read schema failed: {e=}")  
    print(f"{schema=}")

    op = lance.LanceOperation.Overwrite(schema, all_fragments)
    read_version = 0 # Because it is empty at the time.
    lance.LanceDataset.commit(
        dataset_uri,
        op,
        read_version=read_version,
    )
    print(f"lance commit successful.")

def main(args):
    lanceDB_storage_type = args.lanceDB_storage_type
    if lanceDB_storage_type == 's3':
        s3_access_key=os.environ.get('S3_ACCESS_KEY')
        s3_secret_key=os.environ.get('S3_SECRET_KEY')
        s3_endpoint=os.environ.get('S3_ENDPOINT')
        if s3_access_key is None:
            print(f"Error: need to provide s3_access_key via env S3_ACCESS_KEY")
            exit(1)
        if s3_secret_key is None:
            print(f"Error: need to provide s3_secret_key via env S3_SECRET_KEY")
            exit(1)
        if s3_endpoint is None:
            print(f"Error: need to provide s3_endpoint via env S3_ENDPOINT")
            exit(1)
        s3 = setup_s3(s3_access_key, s3_secret_key, s3_endpoint)
    else:
        s3 = fs.LocalFileSystem()
    # read in fragments json files
    lanceDB_fragments_json_folder = args.lanceDB_fragments_json_folder
    all_fragments_json = get_fragments_json(s3, lanceDB_fragments_json_folder)
    lanceDB_table_schema_folder = args.lanceDB_table_schema_folder
    lanceDB_data_uri = args.lanceDB_data_uri
    commit_fragments(s3, all_fragments_json, lanceDB_table_schema_folder, lanceDB_data_uri)

    lanceDB_uri = args.lanceDB_uri
    db = lancedb.connect(lanceDB_uri)
    table_name = args.lanceDB_table_name
    table = db.open_table(table_name)
    print(f"{lanceDB_uri=}")
    print(f"{table.count_rows()=}")
    print(f"lance completed the commit.")
    # sys.exit(0)

def parse_args(args_list):
    parser = argparse.ArgumentParser(description="Commit lance fragments written by parallel jobs into lanceDB table.")
    parser.add_argument(
        f"--lanceDB_storage_type",
        type=str,
        required=False,
        default='local',
        help="lanceDB storage type: local or s3"
    )
    parser.add_argument(
        f"--lanceDB_uri",
        type=str,
        required=False,
        default="",
        help="lanceDB uri, path to the lanceDB uri, start with s3:// if it is a COS path"
    )
    parser.add_argument(
        f"--lanceDB_table_name",
        type=str,
        required=False,
        default="test",
        help="lanceDB table name"
    )
    parser.add_argument(
        f"--lanceDB_data_uri",
        type=str,
        required=False,
        default="",
        help="lance dataset uri path to /table_name.lance"
    )
    parser.add_argument(
        f"--lanceDB_fragments_json_folder",
        type=str,
        required=False,
        default="",
        help="folder path storing the fragments json files"
    )
    parser.add_argument(
        f"--lanceDB_table_schema_folder",
        type=str,
        required=False,
        default="",
        help="folder path storing empty output parquet with lanceDB table schema"
    )
    return parser.parse_args(args_list)

if __name__ == "__main__":
    import sys
    # When run from the command line, it uses sys.argv[1:]
    parsed_args = parse_args(sys.argv[1:]) 
    main(parsed_args)