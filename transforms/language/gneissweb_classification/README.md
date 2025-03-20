# Gneissweb Classification Transform
The Gneissweb Classification transform serves as a simple exemplar to demonstrate the development
of a simple 1:1 transform.  
Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions, transform configuration, testing and IDE set up.

## Contributors

- Ran Iwamoto (ran.iwamoto1@ibm.com)

## Summary 
This transform will classify each text with confidence score with fasttext classification model such as:
- [ibm-granite/GneissWeb.Quality_annotator](https://huggingface.co/ibm-granite/GneissWeb.Quality_annotator)
- [ibm-granite/GneissWeb.Sci_classifier](https://huggingface.co/ibm-granite/GneissWeb.Sci_classifier)
- [ibm-granite/GneissWeb.Tech_classifier](https://huggingface.co/ibm-granite/GneissWeb.Tech_classifier)
- [ibm-granite/GneissWeb.Edu_classifier](https://huggingface.co/ibm-granite/GneissWeb.Edu_classifier)
- [ibm-granite/GneissWeb.Med_classifier](https://huggingface.co/ibm-granite/GneissWeb.Med_classifier)

## Configuration and command line Options

The set of dictionary keys holding [ClassificationTransform](dpk_gneissweb_classification/transform.py) 
configuration for values are as follows:

| Configuration Parameters  | Default  | Description |
|------------|----------|--------------|
| gcls_model_credential | _unset_ | specifies the credential you use to get models. This will be huggingface token. [Guide to get huggingface token](https://huggingface.co/docs/hub/security-tokens) |
| gcls_model_file_name | _unset_ | specifies what filename of models you use to get models, like [`fasttext_gneissweb_quality_annotator.bin`,`fasttext_science.bin`,`fasttext_technology_computing.bin`,`fasttext_education.bin`,`fasttext_medical.bin`] |
| gcls_model_url | _unset_ |  specifies urls that models locate. For fasttext, this will be repo name of the models, like [`ibm-granite/GneissWeb.Quality_annotator`,`ibm-granite/GneissWeb.Sci_classifier`,`ibm-granite/GneissWeb.Tech_classifier`,`ibm-granite/GneissWeb.Edu_classifier`,`ibm-granite/GneissWeb.Med_classifier`] |
| gcls_n_processes | 1 | number of processes. Must be a positive integer |
| gcls_content_column_name | `contents` | specifies name of the column containing documents |
| gcls_output_lablel_column_name | [`label_quality`,`label_sci`,`label_tech`,`label_edu`,`label_med`] | specifies name of the output column to hold predicted classes|
| gcls_output_score_column_name | [`score_quality`,`score_sci`,`score_tech`,`score_edu`,`score_med`]  | specifies name of the output column to hold score of prediction |

## Running

### Launched Command Line Options 
The following command line arguments are available in addition to 
the options provided by 
the [launcher](../../../data-processing-lib/doc/launcher-options.md).
The prefix gcls is short name for Gneissweb CLaSsification.
```
  --gcls_model_credential GCLS_MODEL_CREDENTIAL   the credential you use to get models. This will be huggingface token.
  --gcls_model_file_name GCLS_MODEL_KIND   filename of models you use to get models. Currently,like [`fasttext_gneissweb_quality_annotator.bin`,`fasttext_science.bin`,`fasttext_technology_computing.bin`,`fasttext_education.bin`,`fasttext_medical.bin`]
  --gcls_model_url GCLS_MODEL_URL   urls that models locate. For fasttext, this will be repo name of the models, like [`ibm-granite/GneissWeb.Quality_annotator`,`ibm-granite/GneissWeb.Sci_classifier`,`ibm-granite/GneissWeb.Tech_classifier`,`ibm-granite/GneissWeb.Edu_classifier`,`ibm-granite/GneissWeb.Med_classifier`]
  --gcls_content_column_name GCLS_CONTENT_COLUMN_NAME   A name of the column containing documents
  --gcls_output_lable_column_name GCLS_OUTPUT_LABEL_COLUMN_NAME   Column names to store classification results, like [`label_quality`,`label_sci`,`label_tech`,`label_edu`,`label_med`]
  --gcls_output_score_column_name GCLS_OUTPUT_SCORE_COLUMN_NAME   Column names to store the score of prediction, like [`score_quality`,`score_sci`,`score_tech`,`score_edu`,`score_med`]
  --gcls_n_processes NUMBER_OF_PROCESSES   number of processes, an integer value. Larger value will give a better throughput in compensation for memory consumption
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
