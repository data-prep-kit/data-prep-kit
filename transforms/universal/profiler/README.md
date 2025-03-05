# Profiler Transform 


## Summary

Profiler implement a word count. Typical implementation of the word count is done using map reduce.
* It’s O(N2) complexity
* shuffling with lots of data movement

Implementation here is using “streaming” aggregation, based on central cache:

* At the heart of the implementation is a cache of partial word counts, implemented as a set of Ray actors and containing 
word counts processed so far.
* Individual data processors are responsible for:
  * Reading data from data plane
  * tokenizing documents (we use pluggable tokenizer)
  * Coordinating with distributed cache to collect overall word counts

The complication of mapping this model to transform model is the fact that implementation requires an aggregators cache, 
that transform mode knows nothing about. The solution here is to use transform runtime to create cache
and pass it as a parameter to transforms.

## Transform runtime

[Transform runtime](dpk_profiler/runtime.py) is responsible for creating cache actors and sending their 
handles to the transforms themselves.
Additionally, it writes created word counts to the data storage (as .csv files) and enhances statistics information with the information about cache size and utilization

## Configuration and command line Options

The set of dictionary keys holding [ProfilerTransform](dpk_profiler/transform_base.py)
configuration for values are as follows:

* _doc_column_ - specifies name of the column containing documents

## Running

### Launched Command Line Options
When running the transform with the Python launcher (i.e., TransformLauncher),
the following command line arguments are available in addition to
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).

```shell
  --profiler_doc_column PROFILER_DOC_COLUMN
                        key for accessing data
 ```

These correspond to the configuration keys described above.

### Running the samples
To run the samples, run the following command from the transform folder transform/universal/profiler

For example, 
```shell
make venv && source venv/bin/activate
python -m dpk_profiler.local
```
### Code example

[notebook](profiler-python.ipynb)

## Transform ray runtime

[Transform ray runtime](dpk_profiler/ray/runtime.py) is responsible for creating cache actors and sending their 
handles to the transforms themselves.

## Configuration and command line Options

In addition to the configuration parameters defined above, 
Ray version adds the following parameters:

* _aggregator_cpu_ - specifies an amount of CPUs per aggregator actor
* _num_aggregators_ - specifies number of aggregator actors

### Launched Command Line Options
When running the transform with the Ray launcher (i.e., TransformLauncher),
the following command line arguments are available in addition to
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md):

```shell
  --profiler_aggregator_cpu PROFILER_AGGREGATOR_CPU
                        number of CPUs per aggrigator
  --profiler_num_aggregators PROFILER_NUM_AGGREGATORS
                        number of agregator actors to use
  --profiler_doc_column PROFILER_DOC_COLUMN
                        key for accessing data
 ```

These correspond to the configuration keys described above.

### Running the samples
To run the samples, run the following command from the transform folder transform/universal/profiler

For example, 
```shell
make venv && source venv/bin/activate
python -m dpk_profiler.ray.local
```
### Code example (Ray runtime)

[notebook](profiler-ray.ipynb)

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

