# Repetition Removal Transform

This tranforms performs text repetition removal to remove sequences that frequently occur at documents within a single parquet file level.

The work is adopted from https://github.com/google-research/deduplicate-text-datasets to identify and remove all substrings of a given length that are repeated more than some threshold number of times.

Several enhancements have been made to run at scale at single-parquet file level:

    - Run in the same python space

    - Avoid resource conflict having two processes handling two different parquet files (in making suffix_array and other steps)

    - Cleanup (to prevent data fill up in container environment)

    - Avoid I/O processes (file read/write operations)

    - Eliminate encoding and decoding procedures when working with related files

    - Optimize data loading (loading the data once)

    - Optimize data encoding/decoding for saving the generated output
    
    - Save the tokenizer in a local path and load it from local path to speed up the process
    
    - Copy the empty parquet file to target folder without processing
    
These enhancements speed up the task, minimize the disk storage utilization, and improve parallelism on each node.

The original code from https://github.com/google-research/deduplicate-text-datasets removes all copies of the duplicates. 
Another modification has been made to retain the first copy of each duplicate cluster. 

This repetition removal task can be fine-tuned by adjusting the length_threshold(repeated text sequence length) and frequency_threshold. 

## Contributors
- Shalisha Witherspoon (shalisha.witherspoon@ibm.com)
- Hajar Emami Gohari (Hajar.Emami@ibm.com)

## Requirements
To run the repetition removal transform, **Rust** is required to be installed on the machine. 
You can install rust following instructions [here](https://www.rust-lang.org/tools/install).

**gcc** is also required to be present on the machine. Run `gcc -v` to see if already installed. Otherwise, 
you can find information for installing [here](https://gcc.gnu.org/install/).

## Running on M1 Mac
To run the Transform on an M1 mac, there are a few prerequisites you must run to get started. 

A) Install a compatible **psutils** library in the environment (uninstall if already present):
```shell
pip uninstall psutil
pip install --no-binary :all: psutil

```

B) Compile the dedup_dataset binary from the **dpk_rep_removal** package dir:
- Install from git clone repo:
```shell
cargo install --path dpk_rep_removal/rust
```
- Install from pip install (Note: Activate venv before running next commands):
```shell
PACKAGE_LOCATION=$(pip show data_prep_toolkit_transforms | grep Location | awk '{print $2}')
cargo install --path $PACKAGE_LOCATION/dpk_rep_removal/rust
```
## Input Parameters

The transform can be initialized with the following parameters:

| Parameter                          | Default    | Description                                       |
|------------------------------------|------------|---------------------------------------------------|
| `rep_removal_contents_column_name` | `contents` | Name of the column holding the document contents  |
| `rep_removal_dedup_level_name`     | `parquet`  | Name of the type of file to process               |
| `rep_remova_length_thresh`         | `50`       | Length threshold for processing                   |
| `rep_removal_frequency_threshold`  | `1`        | Frequency threshold for processing                |
| `rep_removal_retain_first_copy`    | `True`     | Boolean value for whether to retain first copy    |
| `rep_removal_tokenize`             | `True`     | Boolean value for whether to tokenize             |
| `rep_removal_num_threads`          | `4`        | Value for number of threads to use for processing |


## Output Format

The output format will be a new parquet file with the repeated sequence(s) removed,
for example:
```
orig parquet:
0 A staffer sells cars via livestream at a deale... ...           0.012263
1 The May 1st submission deadline may feel like ... ...           0.000067
2 Yes! Cinnamon Oil is a great way to deter mice... ...           0.021643
3 Rosemary Oil can be used to deter cockroaches.... ...           0.005885
4 A cat might have discovered an insect crawling... ...           0.881134
5 A staffer sells cars via livestream at a deale... ...           0.012263
6 The May 1st submission deadline may feel like ... ...           0.000067
7 Yes! Cinnamon Oil is a great way to deter mice... ...           0.021643
8 Rosemary Oil can be used to deter cockroaches.... ...           0.005885
9 A cat might have discovered an insect crawling... ...           0.881134
```

```
dedup output:
0 A staffer sells cars via livestream at a deale... ...           0.012263
1 The May 1st submission deadline may feel like ... ...           0.000067
2 Yes! Cinnamon Oil is a great way to deter mice... ...           0.021643
3 Rosemary Oil can be used to deter cockroaches.... ...           0.005885
4 A cat might have discovered an insect crawling... ...           0.881134
5                                                   ...           0.012263
6                                                   ...           0.000067
7                                                   ...           0.021643
8                                                   ...           0.005885
9                                                   ...           0.881134

```

## Basic Usage 
### Run via Command Line
You can invoke the transform via command line, as shown in sample make command `make run-cli-sample`:
```commandline
python -m dpk_rep_removal.runtime \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}" \
                --rep_removal_contents_column_name 'text' \
                --rep_removal_num_threads '1'

```

### Run in a notebook
A sample notebook [here](rep_removal.ipynb) shows how to run the code with python.

### Run in a container
There are docker files available for building an image to run the code with pure [python](Dockerfile.python), or with [ray](Dockerfile.ray).

For details on building and running the image, please refer to the [running images quickstart](../../../doc/quick-start/run-transform-image.md), substituting the name of this transform image and runtime as appropriate.