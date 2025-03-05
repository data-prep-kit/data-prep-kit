# Gneissweb Classification Transform
The Gneissweb Classification transform serves as a simple exemplar to demonstrate the development
of a simple 1:1 transform.  
Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions, transform configuration, testing and IDE set up.

## Summary 
This transform will classify each text with confidence score with fasttext classification model such as [ref](https://huggingface.co/facebook/fasttext-language-identification).

## Configuration and command line Options

The set of dictionary keys holding [ClassificationTransform](dpk_gneissweb_classification/transform.py) 
configuration for values are as follows:

| Configuration Parameters  | Default  | Description |
|------------|----------|--------------|
| gcls_model_credential | _unset_ | specifies the credential you use to get model. This will be huggingface token. [Guide to get huggingface token](https://huggingface.co/docs/hub/security-tokens) |
| gcls_model_file_name | _unset_ | specifies what filename of model you use to get model, like `model.bin` |
| gcls_model_url | _unset_ |  specifies url that model locates. For fasttext, this will be repo name of the model, like `facebook/fasttext-language-identification` |
| gcls_content_column_name | `contents` | specifies name of the column containing documents |
| gcls_output_lablel_column_name | `label` | specifies name of the output column to hold predicted classes|
| gcls_output_score_column_name | `score` | specifies name of the output column to hold score of prediction |

## Running

### Launched Command Line Options 
The following command line arguments are available in addition to 
the options provided by 
the [launcher](../../../data-processing-lib/doc/launcher-options.md).
The prefix gcls is short name for Gneissweb CLaSsification.
```
  --gcls_model_credential GCLS_MODEL_CREDENTIAL   the credential you use to get model. This will be huggingface token.
  --gcls_model_file_name GCLS_MODEL_KIND   filename of model you use to get model. Currently,like `model.bin`
  --gcls_model_url GCLS_MODEL_URL   url that model locates. For fasttext, this will be repo name of the model, like `facebook/fasttext-language-identification`
  --gcls_content_column_name GCLS_CONTENT_COLUMN_NAME   A name of the column containing documents
  --gcls_output_lable_column_name GCLS_OUTPUT_LABEL_COLUMN_NAME   Column name to store classification results
  --gcls_output_score_column_name GCLS_OUTPUT_SCORE_COLUMN_NAME   Column name to store the score of prediction
```
These correspond to the configuration keys described above.

### Code example
Here is a sample [notebook](gneissweb_classification.ipynb)

## Troubleshooting guide

For M1 Mac user, if you see following error during make command, `error: command '/usr/bin/clang' failed with exit code 1`, you should follow [this step](https://freeman.vc/notes/installing-fasttext-on-an-m1-mac)


### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.

# Gneissweb Classification Ray Transform 
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
This project wraps the gneissweb classification transform with a Ray runtime.

## Configuration and command line Options

Gneissweb Classification configuration and command line options are the same as for the base python transform. 

### Launched Command Line Options 
In addition to those available to the transform as defined here,
the set of 
[launcher options](../../../data-processing-lib/doc/launcher-options.md) are available.

### Code example (Ray version)
Here is a sample [notebook](gneissweb_classification-ray.ipynb)

### Transforming data using the transform image

To use the transform image to transform your data, please refer to the 
[running images quickstart](../../../doc/quick-start/run-transform-image.md),
substituting the name of this transform image and runtime as appropriate.
