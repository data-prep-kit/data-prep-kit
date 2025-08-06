# Docling2Parquet Transform 

The Docling2Parquet transform iterates through PDF, Docx, Pptx, Images files or zip of files and generates parquet files
containing the converted document in Markdown or JSON format.

The conversion is using the [Docling package](https://github.com/DS4SD/docling).

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.


## Contributors

- Michele Dolfi (dol@zurich.ibm.com)


## Input files

This transform supports the following input formats:

- PDF documents
- DOCX documents
- PPTX presentations
- XLSX spreadsheets 
- Image files (png, jpeg, etc)
- HTML pages
- Markdown documents
- ASCII Docs documents
- XML in JATS format (e.g. scientific publications)
- XML of USPTO publications

The input documents can be provided in a folder structure, or as a zip archive.
Please see the configuration section for specifying the input files.


## Output format

The output table will contain following columns

| output column name | data type | description |
|-|-|-|
| source_filename | string | the basename of the source archive or file |
| filename | string | the basename of the document file |
| contents | string | the content of the document |
| document_id | string | the document id, a random uuid4  |
| document_hash | string | the document hash of the input content |
| ext | string | the detected file extension |
| hash | string | the hash of the `contents` column |
| size | string | the size of `contents` |
| date_acquired | date | the date when the transform was executing |
| num_pages | number | number of pages in the document |
| num_tables | number | number of tables in the document |
| num_doc_elements | number | number of document elements in the document |
| document_convert_time | float | time taken to convert the document in seconds |


## Configuration

The transform can be initialized with the following parameters.

| Parameter  | Default  | Description  |
|------------|----------|--------------||
| `data_files_to_use`          | - | The files extensions to be considered when running the transform. Example value `['.pdf','.docx','.pptx','.zip']`. For all the supported input formats, see the section above. |
| `batch_size`                 | -1 | Number of documents to be saved in the same result table. A value of -1 will generate one result file for each input file. |
| `artifacts_path`             | <unset> | Path where to Docling models artifacts are located, if unset they will be downloaded and fetched from the [HF_HUB_CACHE](https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache) folder. |
| `contents_type`         | `text/markdown`        | The output type for the `contents` column. Valid types are `text/markdown`, `text/plain` and `application/json`. |
| `do_table_structure`         | `True`        | If true, detected tables will be processed with the table structure model. |
| `do_ocr`                     | `True`        | If true, optical character recognition (OCR) will be used to read the content of bitmap parts of the document. |
| `ocr_engine`                 | `easyocr`     | The OCR engine to use. Valid values are `easyocr`, `tesseract`, `tesseract_cli`. |
| `bitmap_area_threshold`      | `0.05`        | Threshold for running OCR on bitmap figures embedded in document. The threshold is computed as the fraction of the area covered by the bitmap, compared to the whole page area. |
| `pdf_backend`                | `dlparse_v2`  | The PDF backend to use. Valid values are `dlparse_v2`, `dlparse_v1`, `pypdfium2`. |
| `double_precision`           | `8`           | If set, all floating points (e.g. bounding boxes) are rounded to this precision. For tests it is advised to use 0. |
| `do_formula_enrichment`      | `False`       | If true, formula enrichment will be enabled to extract LaTeX representations of mathematical formulas. |
| `accelerator_device`         | `auto`        | The accelerator device to use for GPU acceleration. Valid values are `auto`, `cpu`, `cuda`, `mps`. `auto` automatically selects the best available device. |
| `num_threads`                | `4`           | Number of threads to use for processing. |
| `cuda_use_flash_attention2`  | `False`       | Enable CUDA flash attention optimization (only applicable when using CUDA accelerator device). |
| `use_vlm_pipeline`           | `False`       | Enable Vision Language Model (VLM) pipeline for advanced document understanding and conversion. |
| `vlm_model_type`             | `smoldocling_transformers` | The VLM model type to use. Valid values are `smoldocling_mlx`, `smoldocling_transformers`, `granite_vision_transformers`, `granite_vision_ollama`, `pixtral_12b_transformers`, `pixtral_12b_mlx`, `phi4_transformers`, `qwen25_vl_3b_mlx`, `gemma3_12b_mlx`, `custom_inline`, `custom_api`. |
| `vlm_repo_id`                | `ds4sd/SmolDocling-256M-preview` | Repository ID for the VLM model (used with custom_inline model type). |
| `vlm_prompt`                 | `Convert this page to docling.` | Prompt text to use with the VLM model. |
| `vlm_api_url`                | `http://localhost:11434/v1/chat/completions` | API URL for external VLM services (used with custom_api model type). |
| `vlm_api_model`              | `granite3.2-vision:2b` | Model name for API-based VLM services. |
| `vlm_inference_framework`    | `transformers` | Inference framework to use. Valid values are `mlx`, `transformers`. |
| `vlm_response_format`        | `doctags`     | Response format for VLM output. Valid values are `doctags`, `markdown`, `html`. |
| `vlm_transformers_model_type`| `automodel-vision2seq` | Transformers model type. Valid values are `automodel`, `automodel-vision2seq`, `automodel-causallm`, `automodel-imagetexttotext`. |
| `vlm_scale`                  | `2.0`         | Scaling factor for VLM processing. |
| `vlm_temperature`            | `0.0`         | Temperature setting for VLM text generation (0.0 = deterministic). |
| `vlm_max_new_tokens`         | `4096`        | Maximum number of new tokens to generate with VLM. |
| `vlm_timeout`                | `120.0`       | Timeout in seconds for VLM API calls. |
| `vlm_trust_remote_code`      | `False`       | Whether to trust remote code when loading VLM models. |
| `vlm_load_in_8bit`           | `True`        | Enable 8-bit quantization for VLM models to reduce memory usage. |


### GPU Acceleration

The transform supports GPU acceleration for improved performance when processing documents. The GPU functionality is controlled by the following parameters:

- **`accelerator_device`**: Specifies which device to use for acceleration:
  - `auto` (default): Automatically selects the best available device (CUDA > MPS > CPU)
  - `cpu`: Forces CPU-only processing
  - `cuda`: Uses NVIDIA CUDA GPU acceleration (requires CUDA-compatible GPU)
  - `mps`: Uses Apple Metal Performance Shaders on macOS (requires Apple Silicon Mac)

- **`num_threads`**: Controls the number of processing threads (default: 4)
- **`cuda_use_flash_attention2`**: Enables CUDA flash attention optimization when using CUDA devices for better memory efficiency

### Vision Language Model (VLM) Pipeline

The transform now supports advanced Vision Language Model (VLM) capabilities for enhanced document understanding and conversion. This feature enables AI-powered document analysis using state-of-the-art vision-language models.

#### Key VLM Features:
- **Multi-modal document understanding**: Combines visual and textual analysis
- **Multiple model support**: Choose from various pre-trained models or use custom models
- **Flexible deployment**: Support for both local inference and API-based services
- **Optimized performance**: Hardware acceleration and memory optimization options

#### VLM Configuration:

- **`use_vlm_pipeline`**: Enable/disable VLM processing (default: `False`)
- **`vlm_model_type`**: Select from pre-configured models or custom options:
  - Pre-trained models: `smoldocling_transformers`, `granite_vision_transformers`, `pixtral_12b_transformers`, etc.
  - Custom options: `custom_inline` (local model), `custom_api` (external API)

#### Model-Specific Parameters:

**For Inline Models (`custom_inline`):**
- `vlm_repo_id`: HuggingFace model repository ID
- `vlm_inference_framework`: Choose between `transformers` or `mlx`
- `vlm_transformers_model_type`: Specify the model architecture type
- `vlm_load_in_8bit`: Enable quantization for memory efficiency
- `vlm_trust_remote_code`: Allow execution of custom model code

**For API Models (`custom_api`):**
- `vlm_api_url`: Endpoint URL for the VLM service
- `vlm_api_model`: Model name/identifier for the API
- `vlm_timeout`: Request timeout in seconds

**Generation Parameters:**
- `vlm_prompt`: Custom prompt for document conversion
- `vlm_response_format`: Output format (`doctags`, `markdown`, `html`)
- `vlm_temperature`: Controls randomness in generation (0.0 = deterministic)
- `vlm_max_new_tokens`: Maximum tokens to generate
- `vlm_scale`: Scaling factor for processing

#### Example VLM Configuration:

```python
{
    "use_vlm_pipeline": True,
    "vlm_model_type": "smoldocling_transformers",
    "vlm_response_format": "markdown",
    "vlm_temperature": 0.0,
    "accelerator_device": "cuda"
}
```

For API-based processing:
```python
{
    "use_vlm_pipeline": True,
    "vlm_model_type": "custom_api",
    "vlm_api_url": "http://localhost:11434/v1/chat/completions",
    "vlm_api_model": "granite3.2-vision:2b",
    "vlm_prompt": "Convert this document page to structured markdown"
}
```


#### Hardware Requirements

- **CUDA**: Requires NVIDIA GPU with CUDA support and PyTorch compiled with CUDA
- **MPS**: Requires Apple Silicon Mac (M1/M2/M3) with macOS and PyTorch compiled with MPS support
- **CPU**: Available on all systems as fallback

#### Performance Recommendations

- Use `auto` for automatic device selection based on available hardware
- For NVIDIA GPUs, use `cuda` with `cuda_use_flash_attention2=true` for optimal performance
- For Apple Silicon Macs, use `mps` for GPU acceleration
- Adjust `num_threads` based on your system's CPU cores for CPU processing

Example

```py
{
    "data_files_to_use": ast.literal_eval("['.pdf','.docx','.pptx','.zip']"),
    "contents_type": "application/json",
    "do_ocr": True,
    "do_formula_enrichment": True,
    "accelerator_device": "auto",
    "num_threads": 4,
    "cuda_use_flash_attention2": True
}
```


## Usage

### Launched Command Line Options 

When invoking the CLI, the parameters must be set as `--docling2parquet_<name>`, e.g., `--docling2parquet_do_ocr=true`.

For GPU acceleration parameters:
- `--docling2parquet_accelerator_device=auto`
- `--docling2parquet_num_threads=4`
- `--docling2parquet_cuda_use_flash_attention2=true`


### Running the samples
To run the samples, use the following `make` target

* `run-cli-sample` - runs dpk_docling2parquet/transform_python.py using command line args

These targets will activate the virtual environment and set up any configuration needed.
Use the `-n` option of `make` to see the detail of what is done to run the sample.

For example, 
```shell
make run-cli-sample
...
```
Then 
```shell
ls output
```
To see results of the transform.


### Code example

See the [sample notebook](docling2parquet-python.ipynb) for an example

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:
- [Unit test](test/test_docling2parquet_python.py)
- [Integration test](test/test_docling2parquet.py)
- [GPU Accelerator test](test/test_docling2parquet_gpu_accelerator.py)
- [Simple GPU test](test/test_gpu_accelerator_simple.py)

# Docling2Parquet Ray Transform 

This module implements the ray version of the [docling2parquet transform](dpk_docling2parquet/ray/).

## Configuration and command line Options

Ingest Docling to Parquet configuration and command line options are the same as for the base python transform. 


## Running

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e., TransformLauncher),
in addition to those available to the transform for the Python version in this file,
the set of 
[launcher options](../../../data-processing-lib/doc/launcher-options.md) are available.

### Code example (Ray)

See the [sample notebook](docling2parquet-ray.ipynb) for an example

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.


## Prometheus metrics

The transform will produce the following statsd metrics:

| metric name                      | Description                                                      |
|----------------------------------|------------------------------------------------------------------|
| worker_doc_count                 | Number of documents converted by the worker                      |
| worker_doc_pages_count           | Number of document pages converted by the worker                 |
| worker_doc_page_avg_convert_time | Average time for converting a single document page on each worker|
| worker_document_convert_time     | Time spent converting a single document                          |


# Credits

The Docling document conversion is developed by the AI for Knowledge group in IBM Research Zurich.
The main package is [Docling](https://github.com/DS4SD/docling).

