# Setup and Load Data into Elasticsearch

This script reads a CSV file containing documents, generates embeddings for a specified "contents" field using a Sentence Transformers model, and indexes the documents into an Elasticsearch index.

## Features

- **.env Configuration**: Optionally reads Elasticsearch host, credentials, index name, and CSV path from a `.env` file.
- **Index Management**: Can optionally create a new index using a default mapping file if `CREATE_INDEX` is set to `True`. If `CREATE_INDEX` is `False`, the script verifies that the index exists.
- **CSV Ingestion**: Reads documents from a CSV file and verifies the existence of a `contents` column. If the column is not found, the script exits.
- **Embeddings Generation**: Uses a `SentenceTransformer` model (`paraphrase-MiniLM-L6-v2`) to generate 384-dimensional embeddings for each document’s contents.


## Requirements

- Python 3.8+
- `requests`
- `python-dotenv`
- `sentence-transformers`
- A running instance of Elasticsearch (e.g., `Elasticsearch 7.x+` or `Elasticsearch 8.x+`), accessible at the specified `ELASTIC_HOST`.

## Setup

1. **Install Dependencies**  
   Install Python dependencies using:
   ```bash
   uv pip install -r requirements.txt
## Running the script
   ```bash
   python set_up_elasticsearch.py
