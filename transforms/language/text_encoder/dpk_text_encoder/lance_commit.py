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
import os
import pyarrow.parquet as pq
import json
from data_processing.data_access import DataAccess, DataAccessS3, DataAccessLocal
from lance import FragmentMetadata
import argparse
import sys


def get_fragments_json(s3: DataAccess, json_folder: str) -> list:
    all_fragments_json = []
    # read in the fragment jsons
    total_rows = 0
    files, _ = s3._list_files_folder(json_folder)
    for j, file in enumerate(files):
        if file['name'].endswith(".json"):
            try:
                # Read the content as bytes
                json_bytes, _ = s3.get_file(file['name'])
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

def commit_fragments(s3: DataAccess, all_fragments_json: list, schema_folder: str, dataset_uri:str):

    all_fragments = [FragmentMetadata.from_json(f) for f in all_fragments_json]
    files, _ = s3._list_files_folder(schema_folder)
    for file in files:
        if file['name'].endswith(".parquet"):
            try:
                print(f"{file=}")
                parquet_bytes, _ = s3.get_file(file['name'])
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
        config = {}
        config['access_key'] = os.environ['S3_ACCESS_KEY'] 
        config['secret_key'] = os.environ['S3_SECRET_KEY']
        config['url'] = os.environ['S3_ENDPOINT']
        s3 = DataAccessS3(config)
    else:
        s3 = DataAccessLocal()
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
