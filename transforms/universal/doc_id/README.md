# Document ID Python Annotator

Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions,
transform configuration, testing and IDE set up.

## Contributors
- Boris Lublinsky (blublinsk@ibm.com)

## Description

This transform assigns unique identifiers to the documents in a dataset and supports the following annotations to the
original data:
* **Adding a Document Hash** to each document. The unique hash-based ID is generated using
`hashlib.sha256(doc.encode("utf-8")).hexdigest()`. To store this hash in the data specify the desired column name using
the `hash_column` parameter.
* **Adding an Integer Document ID**: to each document. The integer ID is unique across all rows and tables processed by
the `transform()` method. To store this ID in the data, specify the desired column name using the `int_id_column`
parameter.

Document IDs are essential for tracking annotations linked to specific documents. They are also required for processes
like [fuzzy deduplication](../fdedup/README.md), which depend on the presence of integer IDs. If your dataset lacks document ID
columns, this transform can be used to generate them.

## Input Columns Used by This Transform

| Input Column Name                                                | Data Type | Description                      |
|------------------------------------------------------------------|-----------|----------------------------------|
| Column specified by the _contents_column_ configuration argument | str       | Column that stores document text |

## Output Columns Annotated by This Transform
| Output Column Name | Data Type | Description                                 |
|--------------------|-----------|---------------------------------------------|
| hash_column        | str       | Unique hash assigned to each document       |
| int_id_column      | uint64    | Unique integer ID assigned to each document |

## Configuration and Command Line Options

The set of dictionary keys defined in [DocIDTransform](dpk_doc_id/transform.py)
configuration for values are as follows:

* _doc_column_ - specifies name of the column containing the document (required for ID generation)
* _hash_column_ - specifies name of the column created to hold the string document id, if None, id is not generated
* _int_id_column_ - specifies name of the column created to hold the integer document id, if None, id is not generated
* _start_id_ - an id from which ID generator starts () 

At least one of _hash_column_ or _int_id_column_ must be specified.

## Usage

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).
```
  --doc_id_doc_column DOC_ID_DOC_COLUMN
                        doc column name
  --doc_id_hash_column DOC_ID_HASH_COLUMN
                        Compute document hash and place in the given named column
  --doc_id_int_column DOC_ID_INT_COLUMN
                        Compute unique integer id and place in the given named column
  --doc_id_start_id DOC_ID_START_ID
                        starting integer id
```
These correspond to the configuration keys described above.

### Code example

[notebook](doc_id.ipynb)

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:
- [Unit test](test/test_doc_id_python.py)
- [Integration test](test/test_doc_id.py)


# Document ID Ray Annotator

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Ray Summary
This project wraps the Document ID transform with a Ray runtime.

## Configuration and command line Options

Document ID configuration and command line options are the same as for the
base python transform.

## Building

A [docker file](Dockerfile.ray) that can be used for building docker the ray image. You can use

```shell
make build 
```

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e., RayTransformLauncher), in addition to Python 
command line options, 
[there are options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).

To use the transform image to transform your data, please refer to the
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

### Code example

[notebook](doc_id-ray.ipynb)

# Document ID Spark Annotator

## Summary 

This transform assigns a unique integer ID to each row in a Spark DataFrame. It relies on the
[monotonically_increasing_id](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.monotonically_increasing_id.html)
pyspark function to generate the unique integer IDs. As described in the documentation of this function:
> The generated ID is guaranteed to be monotonically increasing and unique, but not consecutive. 

## Configuration and command line Options

Document ID configuration and command line options are the same as for the
base python transform.

## Running
You can run the [doc_id_local.py](dpk_doc_id/local.py) (spark-based implementation) to transform the
`test1.parquet` file in [test input data](test-data/input) to an `output` directory.  The directory will contain both
the new annotated `test1.parquet` file and the `metadata.json` file.

### Launched Command Line Options 
When running the transform with the Spark launcher (i.e., SparkTransformLauncher), the following command line arguments
are available in addition to the options provided by the
[launcher](../../../data-processing-lib/doc/launcher-options.md).

```
  --doc_id_column_name DOC_ID_COLUMN_NAME
                        name of the column that holds the generated document ids
```

### Running as spark-based application
```
(venv) cma:src$ python doc_id_local.py
18:32:13 INFO - data factory data_ is using local data access: input_folder - /home/cma/de/data-prep-kit/transforms/universal/doc_id/spark/test-data/input output_folder - /home/cma/de/data-prep-kit/transforms/universal/doc_id/spark/output at "/home/cma/de/data-prep-kit/data-processing-lib/ray/src/data_processing/data_access/data_access_factory.py:185"
18:32:13 INFO - data factory data_ max_files -1, n_sample -1 at "/home/cma/de/data-prep-kit/data-processing-lib/ray/src/data_processing/data_access/data_access_factory.py:201"
18:32:13 INFO - data factory data_ Not using data sets, checkpointing False, max files -1, random samples -1, files to use ['.parquet'] at "/home/cma/de/data-prep-kit/data-processing-lib/ray/src/data_processing/data_access/data_access_factory.py:214"
18:32:13 INFO - pipeline id pipeline_id at "/home/cma/de/data-prep-kit/data-processing-lib/ray/src/data_processing/runtime/execution_configuration.py:80"
18:32:13 INFO - code location {'github': 'github', 'commit_hash': '12345', 'path': 'path'} at "/home/cma/de/data-prep-kit/data-processing-lib/ray/src/data_processing/runtime/execution_configuration.py:83"
18:32:13 INFO - spark execution config : {'spark_local_config_filepath': '/home/cma/de/data-prep-kit/transforms/universal/doc_id/spark/config/spark_profile_local.yml', 'spark_kube_config_filepath': 'config/spark_profile_kube.yml'} at "/home/cma/de/data-prep-kit/data-processing-lib/spark/src/data_processing_spark/runtime/spark/spark_execution_config.py:42"
24/05/26 18:32:14 WARN Utils: Your hostname, li-7aed0a4c-2d51-11b2-a85c-dfad31db696b.ibm.com resolves to a loopback address: 127.0.0.1; using 192.168.1.223 instead (on interface wlp0s20f3)
24/05/26 18:32:14 WARN Utils: Set SPARK_LOCAL_IP if you need to bind to another address
Setting default log level to "WARN".
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
24/05/26 18:32:15 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
18:32:17 INFO - files = ['/home/cma/de/data-prep-kit/transforms/universal/doc_id/spark/test-data/input/test_doc_id_1.parquet', '/home/cma/de/data-prep-kit/transforms/universal/doc_id/spark/test-data/input/test_doc_id_2.parquet'] at "/home/cma/de/data-prep-kit/data-processing-lib/spark/src/data_processing_spark/runtime/spark/spark_launcher.py:184"
24/05/26 18:32:23 WARN SparkStringUtils: Truncated the string representation of a plan since it was too large. This behavior can be adjusted by setting 'spark.sql.debug.maxToStringFields'.
```

### Doc ID Statistics
The metadata generated by the Spark `doc_id` transform contains the following statistics:
  * `total_docs_count`, `total_columns_count`: total number of documents (rows), and columns in the input table, before the `doc_id` transform ran    
  * `docs_after_doc_id`, `columns_after_doc_id`: total number of documents (rows), and columns in the output table, after the `doc_id` transform ran  

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.
