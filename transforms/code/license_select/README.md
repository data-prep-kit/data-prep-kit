# License Select Transform

## Description

The License Select transform checks if the license of input data is in approved/denied list. This transform add a new column `license_status` based on the annotation depending on the approved list. 


### Input

| input column name | data type | description |
|:---|:---|:---|
| license | string| license of input data|


### Output Columns annotated by this transform

| output column name | data type | description |
|:---|:---|:---|
| license_status | bool | it describes whether the license is approved or rejected as per the approved/rejected licenses list|

## Configuration

The set of dictionary keys holding license_select configuration for values are as follows:

The transform can be configured with the following key/value pairs from the configuration dictionary.

```python
# Sample params dictionary passed to the transform

{ 
"license_select_params" : {
        "license_column_name": "license",
        "deny_licenses": False,
        "licenses": [ 'MIT', 'Apache'],
        "allow_no_license": False,
    }
}
```

**license_column_name** - The name of the column with licenses.

**deny_licenses** - A boolean value, True for denied licesnes, False for approved licenses.

**licenses** - A list of licenses used as approve/deny list.

**allow_no_license** - A boolean value, used to retain the values with no license in the column `license_column_name` 

## Usage

The following command line arguments are available.

  `--lc_license_column_name` - set the name of the column holds license to process

  `--lc_allow_no_license` - allow entries with no associated license (default: false)

  `--lc_licenses_file` - S3 or local path to allowed/denied licenses JSON file

  `--lc_deny_licenses` - allow all licences except those in licenses_file (default: false)

- The optional `lc_license_column_name` parameter is used to specify the column name in the input dataset that contains the license information. The default column name is license.

- The optional `lc_allow_no_license` option allows any records without a license to be accepted by the filter. If this option is not set, records without a license are rejected.

- The required `lc_licenses_file` options allows a list of licenses to be specified. An S3 or local file path should be supplied (including bucket name, for example: bucket-name/path/to/licenses.json) with the file contents being a JSON list of strings. For example:

  >[
    'Apache-2.0',
    'MIT'
   ]

- The optional `lc_deny_licenses` flag is used when `lc_licenses_file` specifies the licenses that will be rejected, with all other licenses being accepted. These parameters do not affect handling of records with no license information, which is dictated by the allow_no_license option.

  
### Running the samples

To run the samples, use the following `make` target

* `run-cli-sample` - runs dpk_license-select/transform.py using command line args

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

[notebook](./license_select.ipynb)


## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:

- [Unit test](test/test_license_select_python.py)
- [Integration test](test/test_license_select.py)

## Consideration

## License Select Ray Transform 
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.


### Configuration and command line Options

License Select configuration and command line options are the same as for the base python transform. 

### Running

#### Launched Command Line Options 

When running the transform with the Ray launcher (i.e., TransformLauncher),
In addition to those available to the transform as defined here,
the set of 
[launcher options](../../../data-processing-lib/doc/launcher-options.md) are available.

#### Running the samples

To run the samples, use the following `make` target

* `run-ray-cli-sample` - runs dpk_license_select/ray/transform.py using command line args

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

[notebook](./license_select-ray.ipynb)


#### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.
