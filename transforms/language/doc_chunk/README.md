# Chunk documents Transform 

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Contributors

- Michele Dolfi (dol@zurich.ibm.com)

## Description 

This transform is chunking documents. It supports multiple _chunker modules_ (see the `chunking_type` parameter).

When using documents converted to JSON, the transform leverages the [Docling Core](https://github.com/DS4SD/docling-core) `HierarchicalChunker`
to chunk according to the document layout segmentation, i.e. respecting the original document components as paragraphs, tables, enumerations, etc.
It relies on documents converted with the Docling library in the [pdf2parquet transform](../pdf2parquet/README.md) using the option `contents_type: "application/json"`,
which provides the required JSON structure.

When using documents converted to Markdown, the transform leverages the [Llama Index](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#markdownnodeparser) `MarkdownNodeParser`, which is relying on its internal Markdown splitting logic.


### Input 

| input column name | data type | description |
|-|-|-|
| the one specified in _content_column_name_ configuration | string | the content used in this transform |


### Output format

The output parquet file will contain all the original columns, but the content will be replaced with the individual chunks.


#### Tracing the origin of the chunks

The transform allows to trace the origin of the chunk with the `source_doc_id` which is set to the value of the `document_id` column (if present) in the input table.
The actual name of columns can be customized with the parameters described below.


## Configuration

The transform can be tuned with the following parameters.


| Parameter  | Default  | Description  |
|------------|----------|--------------|
| `chunking_type`        | `dl_json` | Chunking type to apply. Valid options are `li_markdown` for using the LlamaIndex [Markdown chunking](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#markdownnodeparser), `dl_json` for using the [Docling JSON chunking](https://github.com/DS4SD/docling), `li_token_text` for using the LlamaIndex [Token Text Splitter](https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/token_text_splitter/), which chunks the text into fixed-sized windows of tokens. |
| `content_column_name`        | `contents` | Name of the column containing the text to be chunked. |
| `doc_id_column_name`         | `document_id` | Name of the column containing the doc_id to be propagated in the output. |
| `chunk_size_tokens`          | `128` | Size of the chunk in tokens for the token text chunker. |
| `chunk_overlap_tokens`       | `30` | Number of tokens overlapping between chunks for the token text chunker. |
| `output_chunk_column_name`   | `contents` | Column name to store the chunks in the output table. |
| `output_source_doc_id_column_name`   | `source_document_id` | Column name to store the `doc_id` from the input table. |
| `output_jsonpath_column_name`| `doc_jsonpath` | Column name to store the document path of the chunk in the output table. |
| `output_pageno_column_name`  | `page_number` | Column name to store the page number of the chunk in the output table. |
| `output_bbox_column_name`    | `bbox` | Column name to store the bbox of the chunk in the output table. |



## Usage

### Launched Command Line Options 

When invoking the CLI, the parameters must be set as `--doc_chunk_<name>`, e.g. `--doc_chunk_column_name_key=myoutput`.

### Code example

See a sample [notebook](doc_chunk.ipynb)

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:
- [Unit test](test/test_doc_chunk_python.py)


## Further Resource

- For the [Docling Core](https://github.com/DS4SD/docling-core) `HierarchicalChunker`
  - <https://ds4sd.github.io/docling/>
- For the Markdown chunker in LlamaIndex
  - [Markdown chunking](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/#markdownnodeparser)
- For the Token Text Splitter in LlamaIndex
  - [Token Text Splitter](https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/token_text_splitter/)


# Chunk documents Ray Transform 

## Summary 
This project wraps the doc_chunck transform python implementation with a Ray runtime.

## Configuration and command line Options

chunk documents configuration and command line options are the same as for the base python transform. 

### Launched Command Line Options 
In addition to those available to the transform as defined above,
the set of 
[launcher options](../../../data-processing-lib/doc/launcher-options.md) are available.

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.
