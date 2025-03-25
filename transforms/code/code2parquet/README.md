# code2parquet Transform

## Description

The code2parquet transform is designed to convert raw files, in particular ZIP files, containing programming files (.py, .c, .java, etc), 
into Parquet format. 
As a transform, it is built to handle concurrent processing of Ray-based
multiple files using multiprocessing for efficient execution.
Each file contained within the ZIP is transformed into a distinct row within the Parquet dataset, adhering to the below schema.

## Contributor

- Saptha Surendra (Saptha.Surendran@ibm.com)

## Output Columns annotated by this transform

| output column name | data type | description |
|:---|:---|:---|
| title | string| Path to the file within the ZIP archive.|
| document| string| Name of the ZIP file containing the current file.|
| repo_name | string| The name of the repository to which the code belongs. This should match the name of the zip file containing the repository.|
| contents| string| Content of the file, converted to a string.|
| document_id| string| Unique identifier computed as a uuid.|
| ext| string| File extension extracted from the file path.|
| hash| string| sha256 hash value computed from the file content string.|
| size| string| Size of the file content in bytes.|
| date_acquired| string| Timestamp indicating when the file was processed.|
| snapshot | string| Name indicating which dataset it belong to.|
| programming_language| string | Name indicating which dataset it belong to.|
| domain| string| Name indicating which domain it belong to, whether code, natural language etc. |

## Configuration

The set of dictionary keys holding [code2parquet](dpk_code2parquet/transform.py) 
configuration values are as follows:

The transform can be configured with the following key/value pairs
from the configuration dictionary.
* `supported_languages` - a dictionary mapping file extensions to language names.
* `supported_langs_file` - used if `supported_languages` key is not provided,
  and specifies the path to a JSON file containing the mapping of languages
  to extensions. The json file is expected to contain a dictionary of
  languages names as keys, with values being a list of strings specifying the
  associated extensions. As an example, see 
  [lang_extensions](test-data/languages/lang_extensions.json) .
* `data_access_factory` - used to create the DataAccess instance used to read
the file specified in `supported_langs_file`.
* `detect_programming_lang` - a flag that indicates if the language:extension mappings
  should be applied in a new column value named `programming_language`.
* `domain` - optional value assigned to the imported data in the 'domain' column.
* `snapshot` -  optional value assigned to the imported data in the 'snapshot' column.

## Usage

The following command line arguments are available:

* `--code2parquet_supported_langs_file` - set the `supported_langs_file` configuration key. 
* `--code2parquet_detect_programming_lang` - set the `detect_programming_lang` configuration key. 
* `--code2parquet_domain` - set the `domain` configuration key. 
* `--code2parquet_snapshot` -  set the `snapshot` configuration key.


### Running the samples

To run the samples, use the following `make` target

* `run-cli-sample` - runs dpk_code2parquet/transform.py using command line args

This target will activate the virtual environment and sets up any configuration needed.
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

[notebook](./code2parquet.ipynb)

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently, we have:

- [Unit test](test/test_code2parquet_python.py)
- [Integration test](test/test_code2parquet.py)


##  code2parquet Ray Transform 

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

### Configuration and command line Options

code2parquet configuration and command line options are the same as for the base python transform. 

### Running

#### Launched Command Line Options 

When running the transform with the Ray launcher (i.e., TransformLauncher), the following additional command line arguments are available:
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).

#### Running the samples

To run the samples, use the following `make` target

* `run-ray-cli-sample` - runs dpk_code2parquet/ray/transform.py using command line args

This target will activate the virtual environment and sets up any configuration needed.
Use the `-n` option of `make` to see the detail of what is done to run the sample.

For example, 

```shell
make run-ray-cli-sample
...
```
Then 
```shell
ls output
```
To see results of the transform.

### Code example (Ray)

[notebook](./code2parquet-ray.ipynb)


#### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.
