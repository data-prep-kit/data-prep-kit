# Programming language Select

## Description

This is a transform which can be used while preprocessing code data. It allows the
user to specify the programming languages for which the data should be identifies as matching
a defined set of programming languages.
It adds a new annotation column which can specify boolean True/False based on whether the rows belong to the
specified programming languages. The rows which belongs to the programming languages which are
not matched are annotated as False.

It requires a text file specifying the allowed languages. It is specified by the
command line param `proglang_select_allowed_langs_file`. 
A sample file is included at `test-data/languages/allowed-code-languages.lst`.
The column specifying programming languages is to be specified by
commandline params `proglang_select_language_column`.


### Input

| input column name | data type | description |
|:---|:---|:---|
| programming_language | string| it specifies the programming language of content |

### Output Columns annotated by this transform

| output column name | data type | description |
|:---|:---|:---|
| allowed_language | bool | True if the programming langauge is in the allowed language file, False otherwise|


## Configuration

The set of dictionary keys holding programming language select configuration for values are as follows:

The transform can be configured with the following key/value pairs from the configuration dictionary.

```python

{
    proglang_select_allowed_langs_file: selected_languages_file,
    proglang_select_language_column: language_column_name,
    proglang_select_output_column: annotated_column_name,
    proglang_select_data_factory: DataAccessFactory(),  # Expect to create DataAccessLocal
}

```

**proglang_select_allowed_langs_file** - A file containing a list of allowed programming languages. Each language is a new line.

**proglang_select_language_column** - The column containing programming language.

**proglang_select_output_column** - The column to store the annotation, True or False. True if the programming language is present in the allowed list. 

**proglang_select_data_factory** - The DataFactory object which creates data access to read allowed language file  


## Usage

The following command line arguments are available.

```
  --proglang_select_allowed_langs_file PROGLANG_MATCH_ALLOWED_LANGS_FILE
                        Path to file containing the list of languages to be matched.
  --proglang_select_language_column PROGLANG_MATCH_LANGUAGE_COLUMN
                        The column name holding the name of the programming language assigned to the document
  --proglang_select_output_column PROGLANG_MATCH_OUTPUT_COLUMN
                        The column name to add and that contains the matching information
  --proglang_select_s3_cred PROGLANG_MATCH_S3_CRED
                        AST string of options for s3 credentials. Only required for S3 data access.
                        access_key: access key help text
                        secret_key: secret key help text
                        url: optional s3 url
                        region: optional s3 region```
```


### Running the samples

To run the samples, use the following `make` targets

* `run-cli-sample` - runs dpk_proglang_select/transform.py using command line args

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

[notebook](./proglang-select.ipynb)


## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:

- [Unit test](test/test_proglang_select_python.py)
- [Integration test](test/test_proglang_select.py)

## Consideration

## Proglang Select Ray Transform 

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.


### Configuration and command line Options

Programming Language Select configuration and command line options are the same as for the base python transform. 

### Running

#### Launched Command Line Options 

When running the transform with the Ray launcher (i.e., TransformLauncher),
In addition to those available to the transform as defined here,
the set of 
[launcher options](../../../data-processing-lib/doc/launcher-options.md) are available.

#### Running the samples

To run the samples, use the following `make` target

* `run-ray-cli-sample` - runs dpk_proglang_select/ray/transform.py using command line args

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

[notebook](./proglang-select-ray.ipynb)


#### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.
