# Resize

The resize transforms allows to change the sizes of input files (both split larger ones and combine smaller).
Per the set of [transform project conventions](../../README.md#transform-project-conventions)
the following runtimes are available:

* python - provides the base python-based transformation
  implementation.
* ray - enables the running of the base python transformation
  in a Ray runtime
* [kfp](kfp_ray/README.md) - enables running the ray docker image
  in a kubernetes cluster using a generated `yaml` file.

Also, please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary

This is a simple transformer that is resizing the input tables to a specified size. 
* resizing based on in-memory size of the tables.
* resizing based on the number of rows in the tables. 

Tables can be either split into smaller sizes or aggregated into larger sizes.

If the files being processed by this transform are distributed accross multiple folders, there are considerations to be taken into account. As a simple example, let's assume the input files are in folders A and B. In an older implementation, the transform would continue the resizing of files from folder B, after folder A, as if they were in folder A. In the current implementation, the resizing of files from each folder is independent of the resizing from the files from the other folders. Let's assume we have a 200-row file 1 in folder A and a 200-row file 2 in folder B and the resizing specifies output files of maximum size 150 rows, so we will end up with 2 output files of 1_1 (size: 150 rows) and 1_2 (size: 50 rows) from folder A and output files of 2_1 (size: 150 rows) and 2_2 (size: 50 rows) from folder B. 

This gets more complicated when the ray implementation of this transform distributues processing files across mutiple ray working nodes. For the files in each folder, the ray workers will parallel-process the files in that folder across mutiple nodes, however, the independence of processing files across folders is preserved. 

## Building

A [docker file](Dockerfile.python) that can be used for building docker image. You can use

```shell
make build 
```

## Configuration and command line Options

The set of dictionary keys holding [Resize Transform](dpk_resize/transform.py)
configuration for values are as follows:

* _max_rows_per_table_ - specifies max documents per table
* _max_mbytes_per_table - specifies max size of table, according to the _size_type_ value.
* _size_type_ - indicates how table size is measured. Can be one of
    * memory - table size is measure by the in-process memory used by the table
    * disk - table size is estimated as the on-disk size of the parquet files.  This is an estimate only
        as files are generally compressed on disk and so may not be exact due varying compression ratios.
        This is the default.

Only one of the _max_rows_per_table_ and _max_mbytes_per_table_ may be used.

## Running

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e., TransformLauncher),
the following command line arguments are additionally available 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md) and map to the configuration keys above.

```
  --resize_max_rows_per_table RESIZE_MAX_ROWS_PER_TABLE
                        Max number of rows per table
  --resize_max_mbytes_per_table RESIZE_MAX_MBYTES_PER_TABLE
                        Max table size (MB). Size is measured according to the --resize_size_type parameter
  --resize_size_type {disk,memory}
                        Determines how memory is measured when using the --resize_max_mbytes_per_table option.
                        'memory' measures the in-process memory footprint and 
                        'disk' makes an estimate of the resulting parquet file size.
```

### Command Line-Launched example


#### Creating the Virtual Environment
First we need a python environment containing the transform.
We create the virtual environment in the transform folder (transforms/universal/resize):
```shell
make venv
source venv/bin/activate
```
Run the transform from the command line using
```shell
python -m dpk_noop.runtime --resize_max_rows_per_table= 125 \
    --data_local '{ "input_folder": "test-data/input", "output_folder": "output" }'
```
Exit the virtual environment and list parquet files produced by the transform
```shell
deactivate
ls output
```
### Code examples

[notebook (python runtime)](resize.ipynb)

[notebook(ray runtime)](resize-ray.ipynb)


### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate. 

We also provide several demos of the transform usage for different data storage options, including
[local file system](dpk_resize/ray/local.py) and [s3](dpk_resize/ray/s3.py).

