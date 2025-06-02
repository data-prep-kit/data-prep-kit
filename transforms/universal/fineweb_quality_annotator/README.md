# FineWeb Quality Annotator

Please see the set of [transform project conventions](../../../README.md) for details on general project conventions transform configuration, testing and IDE set up.

## Contributors

 - Constantin Adam (cmadam@us.ibm.com)

## Description

This annotator applies heuristic rules described in page 7 of the [**FineWeb Datasets paper**](https://arxiv.org/pdf/2406.17557). It follows the [**Datatrove reference implementation**](https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/fineweb_quality_filter.py).

The annotator does not remove any data, it only stores for each document four values that can be subsequently used to filter out documents using specific threshold values, such as those specified in the FineWeb reference implementation of the FineWeb Quality filters: - Discard documents where the fraction of lines ending with punctuation is <= 0.12 - Discard documents where the fraction of characters in duplicated lines is >= 0.1 - Discard the documents where the fraction of lines shorter than 30 characters is >= 0.67 - Discard the documents where the ratio between new lines ('\n') and words is >= 0.3

## Input 

The input table contains a column, by default named `text` holding the document text.

## Output 

The output table is annotated to include few new columns for values as follows:

- frac_line_punct_cname - output table column storing the fraction of lines that end with punctuation. Default is frac_line_punct.
- dup_line_char_frac_cname - specifies the name of the output table column storing the duplicate line character fraction. Default is dup_line_char_frac.
- new_line_ratio_cname - specifies the name of the output table column storing the ratio between the number of new lines and the total number of words. Default is new_line_ratio.
- short_line_frac_cname - specifies the name of the output table column storing the fraction of short lines. Default is short_line_frac.
- short_line_length - specifies the maximum length of a short line. Default is 30

## Configuration and command line Options

The set of dictionary keys holding [BlockListTransform](ray/local.py) configuration for values are as follows:

* _blocklist_annotation_column_name_ - specifies the name of the table column into which the annotation is placed. 
This column is **added** to the output tables.  The default is 
* _blocklist_source_url_column_name_ - specifies the name of the table column holding the URL from which the document was retrieved.
* _blocklist_blocked_domain_list_path_ - specifies the directory holding files matching the regular expression `domains*`.
 
Additionally, a set of data access-specific arguments are provided that enable the specification of the location of domain list files, so that these files could be stored in the local file system or in S3 storage, for example. The arguments generally match the TransformLauncher's data access arguments but with the `blocklist_' prefix.

See the Command Line options below for specifics on these.

## Usage and Running

### Building

A [docker file](Dockerfile) that can be used for building docker image. You can use

```shell
make build 
```

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the [**running images quickstart**](https://github.com/data-prep-kit/data-prep-kit/blob/dev/doc/quick-start/run-transform-image.md), substituting the name of this transform image and runtime as appropriate.

You can run the [local.py](ray/local.py) to transform the `test1.parquet` file in [test input data](test-data/input). The simple example reports blocked domains found in the input parquet file. 

In addition, there are some useful `make` targets (see conventions above)
or use `make help` to see a list of available targets.


### Launched Command Line Options 

When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).
```
--blocklist_blocked_domain_list_path BL_BLOCKED_DOMAIN_LIST_PATH
                        COS URL or local folder (file or directory) that points to the list of block listed domains.  If not running in Ray, this must be a local folder.
--blocklist_annotation_column_name BL_ANNOTATION_COLUMN_NAME
                        Name of the table column that contains the block listed domains
--blocklist_source_url_column_name BL_SOURCE_URL_COLUMN_NAME
                        Name of the table column that has the document download URL
--blocklist_s3_cred BL_S3_CRED
                        AST string of options for cos credentials. Only required for COS or Lakehouse.
                        access_key: access key help text
                        secret_key: secret key help text
                        url: S3 url
                        Example: { 'access_key': 'AFDSASDFASDFDSF ', 'secret_key': 'XSDFYZZZ', 'url': 's3:/cos-optimal-llm-pile/test/' }
--blocklist_s3_config BL_S3_CONFIG
                        AST string containing input/output paths.
                        input_path: Path to input folder of files to be processed
                        output_path: Path to output folder of processed files
                        Example: { 'input_path': '/bucket_name/input', 'output_path': '/bucket_name/output' }
--blocklist_lh_config BL_LH_CONFIG
                        AST string containing input/output using lakehouse.
                        input_table: Path to input folder of files to be processed
                        input_dataset: Path to outpu folder of processed files
                        input_version: Version number to be associated with the input.
                        output_table: Name of table into which data is written
                        output_path: Path to output folder of processed files
                        token: The token to use for Lakehouse authentication
                        lh_environment: Operational environment. One of STAGING or PROD
                        Example: { 'input_table': '/cos-optimal-llm-pile/bluepile-processing/rel0_8/cc15_30_preproc_ededup', 'input_dataset': '/cos-optimal-llm-pile/bluepile-processing/rel0_8/cc15_30_preproc_ededup/processed', 'input_version': '1.0', 'output_table': 'ededup', 'output_path': '/cos-optimal-llm-pile/bluepile-processing/rel0_8/cc15_30_preproc_ededup/processed', 'token': 'AASDFZDF', 'lh_environment': 'STAGING' }
--blocklist_local_config BL_LOCAL_CONFIG
                        ast string containing input/output folders using local fs.
                        input_folder: Path to input folder of files to be processed
                        output_folder: Path to output folder of processed files
                        Example: { 'input_folder': './input', 'output_folder': '/tmp/output' }

```




