# dpk_transform_chain

A lightweight pure Python orchestration framework for running transformation pipelines 

This package supports:
- ✅ Full in-memory processing
- ✅ Parallel processing: process multiple files or batches concurrently using multiple threads
- ✅ Simple Python API interface (no YAML, no Prefect, no Dask required)

---

## 📦 Package Components
| Module | Description |
|--------|-------------|
| `TransformsChain` | Full in-memory pipeline (small to medium files) |
| `ParallelTransformsChain` | Parallel batch processing in memory |

---

## 🔧 Install

```bash
cd transforms

# Optional: create virtual environment
python -m venv venv
source venv/bin/activate


uv pip install ".[all]"

cd ../data-process-lib
uv pip install . 
```

---

## 🔬 Usage Example

```python
from data_processing.data_access import DataAccessLocal
from dpk_docling2parquet import docling2parquet_contents_types, Docling2ParquetTransform
from dpk_doc_chunk import DocChunkTransform
from dpk_transform_chain import TransformsChain

# Instantiate your transforms (fully compatible with existing transform logic)
docling2parquet_params = {"contents_type": docling2parquet_contents_types.MARKDOWN}

doc_chunk_params = {"chunking_type": "li_markdown",
                    "chunk_size_tokens": 128,
                    "chunk_overlap_tokens": 30,
                    }
doc2parquet = Docling2ParquetTransform(docling2parquet_params)
doc_chunk = DocChunkTransform(doc_chunk_params)

# Instantiate your data access object
da_config = {
            "config": {
                "input_folder": "test-data/binary_input",
                "output_folder": "test-data/binary_output",
            },
            "files_to_use": [".pdf"]
        }

data_access = DataAccessLocal(**da_config)

# Create orchestrator instance (this example uses AutoMode)
orch = TransformsChain(
            data_access=data_access,
            transforms=[doc2parquet, doc_chunk]
        )

# Run full pipeline
orch.run()
```

---

## 🔧 API Summary

| Orchestrator | Class |
|--------------|-------|
| Full memory | `TransformsChain(data_access, transforms)` |

---

## 🔬 Running Tests

```bash
pytest tests/
```

Tests are fully mocked and do not require real data files.

---

