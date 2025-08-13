# Code Document Cleaner Transform for Ray

This module is used to extract and clean code document data from raw HTML.
This module is built by extending the OSS HTML parser, [Resiliparse](https://resiliparse.chatnoir.eu/en/stable/).
Specifically, the following functionalities are featured to better handle documents related to code,
but not limited to:

- **Indent preservation**: preserves code indentation, which is important for
indentation-matter programming languages (e.g., Python) or markups (e.g., YAML).
- **Boilerplate removal**: removes boilerplates appear in HTML,
such as menu bars, side bars, headers, footers, table of contents, etc.
- **Math handling**: preserves Math symbols and equations used in HTML.
- **List handling**: preserves list structures.
- **Table handling**: preserves table structures.

Please see the set of
[transform project conventions](../../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Running

This module assumes to process a table containing multile records.

Each table record corresponds to a single document and expects to have a column
that holds a raw HTML string of the document.

The output table processed by this module will have the extracted text in the column
specified by `--cdc_clean_text_column_name` (default: "contents") and
the raw HTML string in the "html_contents" column.

### Command Line Options

The following command line arguments are available in addition to
the options provided by
the [python launcher](../../../../data-processing-lib/doc/launcher-options.md).

```text
--cdc_disable_table_structure CDC_DISABLE_TABLE_STRUCTURE
    Disable to keep table structure if True. Default: False
--cdc_contents_column_name CDC_CONTENTS_COLUMN_NAME
    The column name to get HTML strings. Default: contents
--cdc_clean_text_column_name CDC_CLEAN_TEXT_COLUMN_NAME
    The column name to write cleaned texts. Default: contents
```

### Running the samples

Following samples are available to run this module and to see how it works.

- [code_doc_cleaner_local_ray.py](src/code_doc_cleaner_local_ray.py) cleans text in `test-data/input/test.parquet` and saves the results in `output_local_ray/test.parquet`. Run it without any command-line option: `cd src; python code_doc_cleaner_local_ray.py`.
- [code_doc_cleaner_s3_ray.py](src/code_doc_cleaner_s3_ray.py) cleans text in `s3://cos-optimal-llm-pile/test/mmuraoka/code_doc_clean/input/` and saves the results in `s3://cos-optimal-llm-pile/test/mmuraoka/code_doc_clean/output_s3_ray/`. Set environment variables `DPL_S3_ACCESS_KEY` and `DPL_S3_SECRET_KEY` with a read-write credential to `cos-optimal-llm-pile` of COS. Run it without any command-line option: `cd src; DPL_S3_ACCESS_KEY=abcdef... DPL_S3_SECRET_KEY=ABCDEF... python code_doc_clean_s3_ray.py`.

## Build

Use [Dockerfile](Dockerfile) to build a container image.

```shell
make image
```

## Test

```shell
cd src
pytest -s ../test
```
