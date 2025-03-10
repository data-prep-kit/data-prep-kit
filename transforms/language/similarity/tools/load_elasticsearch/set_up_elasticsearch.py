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

import csv
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import sys
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Optional values for these may come from the .env file
elastic_host = os.getenv('ELASTIC_HOST', '')
elastic_user = os.getenv('ELASTIC_USER', 'elastic')
elastic_password = os.getenv('ELASTIC_PASSWORD', 'elastic')
index_name = os.getenv('INDEX_NAME', 'mydata')
csv_path = os.getenv('CSV_PATH', os.path.join(os.path.dirname(os.path.realpath(__file__)), "mydata.csv"))
CONTENTS_COLUMN = os.getenv('contents', 'contents')

CREATE_INDEX = False  # If True, attempt to create index if not exists
BATCH_SIZE = 1000

if not elastic_host or not index_name or not csv_path:
    print("Error: Missing required configuration. Ensure elastic_host, index_name, and csv_path are set.")
    sys.exit(1)

bulk_url = f'{elastic_host}/_bulk'
headers = { 'Content-Type': 'application/x-ndjson' }
elastic_auth = HTTPBasicAuth(elastic_user, elastic_password)

mapping_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "mapping.json")
with open(mapping_file_path, "r") as f:
    mappings = json.load(f)

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
csv.field_size_limit(sys.maxsize)


def index_exists(index):
    """Check if the Elasticsearch index exists."""
    r = requests.head(f"{elastic_host}/{index}", auth=elastic_auth, verify=False)
    return r.status_code == 200


def create_index(index, mapping):
    """Create the Elasticsearch index with given mapping."""
    r = requests.put(f"{elastic_host}/{index}", auth=elastic_auth, headers={'Content-Type': 'application/json'}, json=mapping, verify=False)
    if r.status_code not in [200, 201]:
        print(f"Error creating index {index}: {r.status_code} {r.text}")
        sys.exit(1)
    else:
        print(f"Index {index} created successfully.")


def verify_and_setup_index(index):
    """Verify and optionally create the index based on CREATE_INDEX."""
    if CREATE_INDEX:
        if index_exists(index):
            print(f"Index {index} already exists. Exiting.")
            sys.exit(1)
        else:
            create_index(index, mappings)
    else:
        if not index_exists(index):
            print(f"Index {index} does not exist. Exiting.")
            sys.exit(1)


def read_csv(csv_file_path):
    """Read CSV and yield rows. Verify CONTENTS_COLUMN column."""
    with open(csv_file_path, "r", encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if CONTENTS_COLUMN not in reader.fieldnames:
            print(f"Error: '{CONTENTS_COLUMN}' column not found in CSV. Exiting.")
            sys.exit(1)
        for row in reader:
            yield row


def generate_embeddings_and_push(index, rows, batch_size):
    """Generate embeddings for each row and push to Elasticsearch in batches."""
    buffer = []
    total_docs = 0
    for i, row in enumerate(rows, start=1):
        contents = row[CONTENTS_COLUMN]
        embedding = model.encode(contents)
        sentence_transformers_384 = [float(val) for val in embedding]

        action = {"index": {"_index": index}}
        doc = {
            "contents": contents,
            "sentence_transformers_384": sentence_transformers_384
        }

        buffer.append(json.dumps(action))
        buffer.append(json.dumps(doc))

        if len(buffer) >= batch_size * 2:
            push_batch(buffer)
            total_docs += batch_size
            buffer = []

    # Push remaining documents if any
    if buffer:
        push_batch(buffer)
        total_docs += len(buffer) // 2

    return total_docs


def push_batch(batch):
    """Push a batch of documents to Elasticsearch."""
    data = "\n".join(batch) + "\n"
    r = requests.post(bulk_url, auth=elastic_auth, headers=headers, data=data, verify=False)
    if r.status_code != 200:
        print(f"Error pushing batch: {r.status_code}\n{r.text}")
        sys.exit(1)
    response_json = r.json()
    if response_json.get('errors', False):
        print("Bulk indexing encountered errors:")
        for item in response_json.get('items', []):
            if item.get('index', {}).get('error'):
                print(item.get('index', {}).get('error'))
        sys.exit(1)


if __name__ == "__main__":
    # Set up index
    verify_and_setup_index(index_name)

    # Read CSV rows
    rows = read_csv(csv_path)

    # Process and push documents
    total_docs_indexed = generate_embeddings_and_push(index_name, rows, BATCH_SIZE)

    # Print summary
    action_desc = "created" if CREATE_INDEX else "verified"
    print(f"Index '{index_name}' {action_desc}.")
    print(f"Indexed {total_docs_indexed} documents into '{index_name}'.")
    print("Operation complete.")