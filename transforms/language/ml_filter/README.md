# Multilingual Filter

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Contributors

- Cezar Pendus (cpendus@us.ibm.com)

## Summary 
This transform filters the data using conditions specified in a corresponding yaml file. Here is a sample [yaml file](./cleansing-config.yaml).

The input table must contain all the values specified in the filtering conditions, as well as a language identifier (`lang`).
The language identifier column name can be set with --filter_lang_column_name.
The yaml file with the filtering conditions can be specified with --filter_config.
Optionally a prefix can be added to the labels specified in the filtering conditions. This prefix can be set with --filter_column_prefix.

Additionally, each column can be renamed using an the option --enrichment_NAME_column_name, where NAME is one of the labels below.
If a column is renamed to the empty string, it will not be set in the output.

The config file has to contain a section for each language that it accepts. 
A set of condtions that apply to all languages can be set in the `default` section.

For example, the average word lengths below will apply to both French and English:
```
default:
    # thresholds based on stats and sampling for European langs without German, Basque
    avg_word_length_min: 3.2
    avg_word_length_max: 7.0
en:
    num_words_min: 110
    lid_score_min: 0.5
fr:
    num_words_min: 100
    lid_score_min: 0.6
```
## Required parameters for the transform
| Name  | Default Value | Description |
|------------|----------|--------------|
| **lm_filter_config** | **_text_** | File name with the conditions for the filter, in YAML format. |
| **lm_filter_lang_column_name** | **lang** | The column name with language identifier used in the filter conditions. |
| **lm_filter_column_prefix** | _not set_ | A prefix for the names referenced in the conditions file.|
| **lm_filter_ignore_missing_columns** | **False** | By default, the transform will fail if any for the values referenced in the conditions is missing. Set this parameter to ignore all the missing columns. |

## Running the samples
To run the samples, use the following `make` target

* `run-cli-sample` - runs dpk_ml_filter.runtime using command line args
or
* `run-ray-cli-sample` - runs dpk_ml_filter.ray.runtime using command line args

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

**Note:** The Ray scalable version of the transform is included, however, running on a single machine and not a cluster, the Ray version does not get a performance benefit because the transform operates one record at a time on an input file.

### Code example

[notebook](./ml_filter.ipynb)

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:
- [Unit test](test/test_ml_filter.py)

## Credits

The work on this transform is continuation of the original work by Juergen Bross (jbross@us.ibm.com).
