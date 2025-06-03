# 🌀 Prefect Workflow Executor

A flexible Python script that uses [Prefect](https://docs.prefect.io/) to build and execute customizable data workflows defined in **YAML** or **JSON** format.

---

## 📌 Features

- ✅ Define workflows declaratively using YAML or JSON  
- ✅ Dynamically build Prefect Flows based on structured input  
- ✅ Supports local and S3-based input/output configuration

---

## 📖 Configuration Structure

The configuration file defines the **workflow**, **data access**, and a **sequence of operations**. It is broken into the following components:

### `flow`
Top-level container for the entire workflow definition.

#### `name`
Name of the Prefect flow.

#### `global_config`
Defines settings that apply to the entire flow:
- `data_storage_type`: Currently supports `"local"` and `"s3"` (can be extended).
- `data_access`: Contains configuration for data IO and processing.
  - `s3_config`: Input/output folder paths on S3.
  - `s3_credentials`: Credentials for accessing the S3 bucket.
  - `batch_size`: Number of files/records per operation batch.
  - `files_to_use`: List of file extensions to process (e.g., `.parquet`, `.csv`).

#### `sequence`
A list of sequential or dependent transforms in the DAG-style workflow.

Each node includes:
- `name`: Unique name of the node (used as reference).
- `transform`: The transformation function to apply (e.g., `lang_id`, `doc_quality`).
- `params`: Dictionary of parameters required by the transform.
- `input_edges`: List of dependency references (which nodes must run before this one).
- `output_edges`: List of downstream nodes this step feeds into.

---

## 📂 Example YAML Configuration

```yaml
flow:
  name: sample flow
  global_config:
    data_storage_type: s3
    data_access:
      s3_config:
        input_folder: ""
        output_folder: ""
      s3_credentials:
        access_key: ""
        secret_key: ""
        url: ""
        region: ""
      batch_size: 10
      files_to_use:
        - ".parquet"
  sequence:
    - name: ingest
      transform: lang_id
      params:
        content_column_name: contents
        model_kind: fasttext
        model_url: facebook/fasttext-language-identification
        output_lang_column_name: fasttext_label
        output_score_column_name: fasttext_prob
      input_edges: []
      output_edges:
        - node_name_ref: doc_quality

    - name: doc_quality
      transform: doc_quality
      params:
        doc_content_column: contents
        bad_word_filepath: ""
        text_lang: en
      input_edges:
        - node_name_ref: ingest
      output_edges: []
```

---
## 📂 Example JSON Configuration

```json
{
  "flow": {
    "name": "sample flow",
    "global_config": {
        "data_storage_type": "local",
        "data_access": {
            "local_config": {
                "input_folder": "/User/test/input",
                "output_folder": "/Usr/test/output"
            },
            "batch_size": 10,
            "files_to_use": [".parquet"]
        }
    },
    "sequence": [
      {
        "name": "ingest",
        "transform": "lang_id",
        "params": {
            "content_column_name": "contents",
            "model_kind": "fasttext",
            "model_url": "facebook/fasttext-language-identification",
            "output_lang_column_name": "fasttext_dclm_oh_eli5_label",
            "output_score_column_name": "fasttext_dclm_oh_eli5_prob"
        },
        "input_edges": [],
        "output_edges": [
          {
            "node_name_ref": "doc_quality"
          }
        ]
      },
      {
        "name": "doc_quality",
        "transform": "doc_quality",
        "params": {
            "doc_content_column": "contents",
            "bad_word_filepath": "/User/test/Documents/bad_words/en",
            "text_lang": "en"

        },
        "input_edges": [
          {
            "node_name_ref": "ingest"
          }
        ],
        "output_edges": []
      }
    ]
  }
}

```

---

## 🚀 Getting Started

### 1. Create and Activate a Virtual Environment (Recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

---

### 2. Install DPK Dependencies

Make sure you’re in the root of the repository.

#### 📦 2.1 Install the Core Library (from `data-processing-lib/`)

```bash
cd data-processing-lib
pip install .
```

#### 📦 2.2 Install Transform Modules (from `transforms/` with extras)

```bash
cd ../transforms
pip install ".[all]"
```

> 💡 If you get a `SyntaxError: invalid decimal literal`, it may be due to a conflict with the `uuid` package (which is built into Python and **should not be installed** as a separate package). To resolve:
>
> ```bash
> pip uninstall uuid
> ```


### 3. Install Prefect Dependencies

```bash
pip install -r requirements.txt
```

> Dependencies include `prefect`, `pyyaml`, and any libraries used in custom transforms.

### 2. Define Your Workflow

Create a `.yaml` or `.json` file that describes your flow. Use the example above as a reference.

### 3. Run the Script

```bash
python orchestrator/abstract_orchestrator.py /path/to/your/flow.yaml
```

Supports `.yaml`, `.yml`, or `.json`.

---

## 📦 Output

Results (e.g., transformed data, logs) will be stored in the specified `output_folder` defined under `global_config`.

