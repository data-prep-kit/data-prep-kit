# Exact Deduplication Transform 

Exact deduplication transform identifies and removes identical documents in a dataset by comparing them hash-for-hash
to ensure exact matching. Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on
general project conventions, transform configuration, testing and IDE set up.

## Contributors
- Boris Lublinsky (blublinsk@ibm.com)

## Description
This Python implementation of the exact deduplication transform uses "streaming" deduplication based on a central hash.
As shown below, it relies on a distributed hash cache and data processors that read documents, generate hashes,
coordinate with the cache to remove duplicates, and store unique documents in the data plane.

![](images/exactdedup.png)

Mapping this model to the transform model is complicated by the need for a hash cache, which the transform model does
not recognize. The solution is to have the transform runtime create the hash cache and pass it as a parameter to the
transforms. The transform runtime handles hash cache creation and enhances statistics with details about cache size and
utilization.

### Incremental Execution and Snapshotting

The current implementation includes snapshotting, where the hash cache is saved to storage (local disk or S3) at the
end of execution. This enables incremental deduplication: you can run deduplication on existing files, save the hash
cache, and later load the snapshot to deduplicate only new files, avoiding reprocessing the entire dataset.

## Input Columns Used by This Transform

| Input Column Name                                                   | Data Type | Description                      |
|---------------------------------------------------------------------|-----------|----------------------------------|
| Column specified by the _contents_column_ configuration argument    | str       | Column that stores document text |
| Column specified by the _document_id_column_ configuration argument | int64     | Column that stores document ID   |

## Output Columns Annotated by This Transform
This transform does not perform any annotations; it only filters out the documents that are marked as duplicates.

## Configuration

The set of dictionary keys holding [EdedupTransform](dpk_ededup/transform_base.py)
configuration for values (common for Python and Ray) are as follows:

* _doc_column_ - specifies name of the column containing documents
* _doc_id_column_ - specifies the name of the column containing a document id
* _use_snapshot_ - specifies that ededup execution starts with a set of pre-existing hashes, enabling incremental
execution
* _snapshot_directory_ - specifies the directory for reading snapshots. If not provided, the default is
`output_folder/snapshot`

## Usage

The following command line arguments (corresponding to the configuration keys described above) are available in addition
to the options provided by the [launcher](../../../data-processing-lib/doc/launcher-options.md).
```text
  --ededup_doc_column EDEDUP_DOC_COLUMN
                        name of the column containing document
  --ededup_doc_id_column EDEDUP_DOC_ID_COLUMN
                        name of the column containing document id
  --ededup_use_snapshot EDEDUP_USE_SNAPSHOT
                        flag to continue from snapshot
  --ededup_snapshot_directory EDEDUP_SNAPSHOT_DIRECTORY
                        location of snapshot files  
```

### Code example

[notebook](ededup-python.ipynb)

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:
- [Unit test](test/test_ededup_python.py)
- [Integration test](test/test_ededup.py)

# Exact Dedup Ray Annotator

Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions,
transform configuration, testing and IDE set up.

## Additional parameters

In addition to common ededup parameters, Ray implementation provides two additional ones

* _hash_cpu_ - specifies amount of CPU per hash actor
* _num_hashes_ - specifies number of hash actors

## Additional support

We also provide an [estimate](dpk_ededup/ray/cluster_estimator.py) to roughly determine cluster size for running transformer.

### Running the samples
To run the samples, use the following `make` target

* `run-cli-sample` - runs dpk_ededup/ray/transform.py using command line args

This target will activate the virtual environment and set up any configuration needed.
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

[notebook](ededup-ray.ipynb)

### Launched Command Line Options
When running the transform with the Ray launcher (i.e., RayTransformLauncher), these additional command line arguments are available 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).

```
  --ededup_hash_cpu EDEDUP_HASH_CPU
                        number of CPUs per hash
  --ededup_num_hashes EDEDUP_NUM_HASHES
                        number of hash actors to use
  --ededup_doc_column EDEDUP_DOC_COLUMN
                        name of the column containing document
  --ededup_doc_id_column EDEDUP_DOC_ID_COLUMN
                        name of the column containing document id
  --ededup_use_snapshot EDEDUP_USE_SNAPSHOT
                        flag to continue from snapshot
  --ededup_snapshot_directory EDEDUP_SNAPSHOT_DIRECTORY
                        location of snapshot files                      
 ```

These correspond to the configuration keys described above.
