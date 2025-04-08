# Comment cleanser

Please see the set of
[transform project conventions](../../../README.md)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary
This module is designed to detect and remove commented-out code from code files. It leverages the [comment_parser](https://pypi.org/project/comment-parser/) library to accurately extract comments from various programming languages.

To differentiate between regular comments (textual descriptions) and commented-out code, the module employs a Multinomial Naïve Bayes classifier. The classifier predicts:

0 → The comment is regular text.\
1 → The comment is code that should be removed.\
Additionally, the module logs the line numbers where commented-out code was detected. To log line number comment_parser's line_number method is used.

Functionality 
- Extract Comments: Uses comment_parser to fetch all comment lines.
- Predict Comment Type: Applies the Naïve Bayes model to classify whether a comment is text or code.
- Remove Commented Code: Deletes lines predicted as code.

## Configuration and command line Options

This project wraps the [comment cleanser transform](../python) with a Ray runtime.

## Running

### Launched Command Line Options 
In addition to those available to the transform as defined in [here](../python/README.md), 
the set of [launcher options](../../../../data-processing-lib/doc/launcher-options.md) are available.

### Running the samples
To run the samples, use the following `make` targets

* `run-cli-ray-sample` - runs src/comment_cleanser_transform.py using command line args
* `run-local-ray-sample` - runs src/comment_cleanser_local_ray.py
* `run-s3-ray-sample` - runs src/comment_cleanser_s3_ray.py
    * Requires prior invocation of `make minio-start` to load data into local minio for S3 access.

These targets will activate the virtual environment and set up any configuration needed.
Use the `-n` option of `make` to see the detail of what is done to run the sample.

For example, 
```shell
make run-cli-ray-sample
...
```
Then 
```shell
ls output
```
To see results of the transform.

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.