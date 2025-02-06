# Extreme Tokenized Documents Annotator 
Please see the set of
[transform project conventions](../../README.md)
for details on general project conventions, transform configuration, testing and IDE set up.

## Contributors
- Hajar Emami Gohari (Hajar.Emami@ibm.com)
- Constantin Adam (cmadam@us.ibm.com)

## Summary
This annotator retrieves the tokens generated for a set of documents. Then, it calculates, for each document, the size and the total number of characters. The number of tokens is divided by the size and by the number of characters, and the resulting values are stored in two columns (
`tokens_per_doc_size` and `tokens_per_doc_num_chars`).

The annotator transform annotates the input table with 5 columns:
  - doc_num_tokens - number of tokens for each document
  - doc_size_kbs - document size in kb
  - doc_num_chars - number of characters in the document
  - tokens_per_doc_size - ratio between number of tokens and document size
  - tokens_per_doc_num_chars - ratio between number of tokens and number of characters in document

Documents with extremely high or low number of tokens per character (or tokens per byte) are identified as extreme-tokenized documents and can be excluded in the filtering step.

## Configuration and command line Options

The set of dictionary keys holding [ExtremeTokenizedTransform](dpk_extreme_tokenized/runtime.py) configuration for values are as follows:

* _et_contents_column_name_ - specifies the name of the column holding the document text. The default is `text`.
* _et_arrow_path_ - location of the folder containing the arrow (tokenization) files.

Additionally, a set of data access-specific arguments are provided that enable
the specification of the location of domain list files, so that these
files could be stored in the local file system or in S3 storage, for example.
The arguments are as follows (and generally match the TransformLauncher's 
data access arguments but with the `extreme_tokenized_' prefix).

* _et_local_config_ - specifies the input and output folders.
* _et_s3_config_ - specifies the input and output paths in s3.
* _et_s3_credentials_ - provides credentials to access the s3 storage. 

See the Command Line options below for specifics on these.

## Running
You can run the [extreme_tokenized module](dpk_extreme_tokenized/runtime.py) to
transform the `test1.parquet` file in [test input data](test-data/input) 
to an `output` directory.  The output directory will contain both the new
annotated `test1.parquet` file and the `metadata.json` file.
<pre>
(venv) cma:extreme_tokenized$ make venv PYTHON=python3.11
(venv) cma:extreme_tokenized$ source venv/bin/activate
(venv) cma:extreme_tokenized$ python -m dpk_extreme_tokenized.runtime --et_arrow_path test-data/input/arrow --data_local_config "{ 'input_folder': 'test-data/input', 'output_folder': 'output' }"
09:41:22 INFO - Launching Extreme Tokenized Annotator transform
09:41:22 INFO - data factory et_ is using local configuration without input/output path
09:41:22 INFO - data factory et_ max_files -1, n_sample -1
09:41:22 INFO - data factory et_ Not using data sets, checkpointing False, max files -1, random samples -1, files to use ['.parquet'], files to checkpoint ['.parquet']
09:41:22 INFO - pipeline id pipeline_id
09:41:22 INFO - code location None
09:41:22 INFO - data factory data_ is using local data access: input_folder - test-data/input output_folder - output
09:41:22 INFO - data factory data_ max_files -1, n_sample -1
09:41:22 INFO - data factory data_ Not using data sets, checkpointing False, max files -1, random samples -1, files to use ['.parquet'], files to checkpoint ['.parquet']
09:41:22 INFO - orchestrator et started at 2025-01-27 09:41:22
09:41:22 INFO - Number of files is 1, source profile {'max_file_size': 0.029085159301757812, 'min_file_size': 0.029085159301757812, 'total_file_size': 0.029085159301757812}
09:41:22 INFO - Transforming table with 10 rows from file /home/cma/de/data-prep-kit/transforms/language/extreme_tokenized/test-data/input/test1.parquet
09:41:22 INFO - Completed 1 files (100.0%) in 0.001 min
09:41:22 INFO - Done processing 1 files, waiting for flush() completion.
(venv) cma:extreme_tokenized$ deactivate
</pre>

### Building the Docker Images
```shell
(venv) cma:extreme_tokenized$ make image 
...
(venv) cma:extreme_tokenized$ podman images
REPOSITORY                                                  TAG       IMAGE ID       CREATED              SIZE
extreme_tokenized-ray                                       latest    b933331aab92   41 seconds ago       2.77GB
quay.io/dataprep1/data-prep-kit/extreme_tokenized-ray       latest    b933331aab92   41 seconds ago       2.77GB
extreme_tokenized-python                                    latest    a5df95eba200   About a minute ago   696MB
quay.io/dataprep1/data-prep-kit/extreme_tokenized-python    latest    a5df95eba200   About a minute ago   696MB
````
In addition, there are some useful `make` targets (see conventions above)
or use `make help` to see a list of available targets.

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).
```
options:
  -h, --help            show this help message and exit
  --et_contents_column_name ET_CONTENTS_COLUMN_NAME
                        Name of the column holding the document text
  --et_arrow_path ET_ARROW_PATH
                         Arrow folder location.
  --et_s3_cred ET_S3_CRED
                        AST string of options for s3 credentials. Only required for S3 data access.
                        access_key: access key help text
                        secret_key: secret key help text
                        url: optional s3 url
                        region: optional s3 region
                        Example: { 'access_key': 'access', 'secret_key': 'secret', 
                        'url': 'https://s3.us-east.cloud-object-storage.appdomain.cloud', 
                        'region': 'us-east-1' }
  --data_s3_cred DATA_S3_CRED
                        AST string of options for s3 credentials. Only required for S3 data access.
                        access_key: access key help text
                        secret_key: secret key help text
                        url: optional s3 url
                        region: optional s3 region
                        Example: { 'access_key': 'access', 'secret_key': 'secret', 
                        'url': 'https://s3.us-east.cloud-object-storage.appdomain.cloud', 
                        'region': 'us-east-1' }
  --data_s3_config DATA_S3_CONFIG
                        AST string containing input/output paths.
                        input_folder: Path to input folder of files to be processed
                        output_folder: Path to output folder of processed files
                        Example: { 'input_folder': 's3-path/your-input-bucket', 
                        'output_folder': 's3-path/your-output-bucket' }
  --data_local_config DATA_LOCAL_CONFIG
                        ast string containing input/output folders using local fs.
                        input_folder: Path to input folder of files to be processed
                        output_folder: Path to output folder of processed files
                        Example: { 'input_folder': './input', 'output_folder': '/tmp/output' }
  --data_max_files DATA_MAX_FILES
                        Max amount of files to process
  --data_checkpointing DATA_CHECKPOINTING
                        checkpointing flag
  --data_files_to_checkpoint DATA_FILES_TO_CHECKPOINT
                        list of file extensions to choose for checkpointing.
  --data_data_sets DATA_DATA_SETS
                        List of sub-directories of input directory to use for input. For example, ['dir1', 'dir2']
  --data_files_to_use DATA_FILES_TO_USE
                        list of file extensions to choose for input.
  --data_num_samples DATA_NUM_SAMPLES
                        number of random input files to process
  --runtime_num_processors RUNTIME_NUM_PROCESSORS
                        size of multiprocessing pool
  --runtime_pipeline_id RUNTIME_PIPELINE_ID
                        pipeline id
  --runtime_job_id RUNTIME_JOB_ID
                        job id
  --runtime_code_location RUNTIME_CODE_LOCATION
                        AST string containing code location
                        github: Github repository URL.
                        commit_hash: github commit hash
                        path: Path within the repository
                        Example: { 'github': 'https://github.com/somerepo', 'commit_hash': '1324', 
                        'path': 'transforms/universal/code' }
```
