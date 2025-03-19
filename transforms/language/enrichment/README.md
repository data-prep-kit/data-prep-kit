# Text Enrichment

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Contributors

- Cezar Pendus (cpendus@us.ibm.com)

## Summary 
This transform computes a number of features that can be later used to estimate the data quality. 
The input table must contain at least two columns: the text content (`text` by default), and the language identifier (`lang`).
Both these columns can be specified with --enrichment_content_column_name and --enrichment_lang_column_name.
To facilitate multi-faceted processing the output column names can renamed with a common prefix, specified with --enrichment_output_column_prefix.
Additionally, each column can be renamed using an the option --enrichment_NAME_column_name, where NAME is one of the labels below.
If a column is renamed to the empty string, it will not be set in the output.

The added columns are: 
```
    "num_newlines"
    "num_paragraphs"
    "num_words"
    "num_chars"
    "total_non_newline_chars"

    "avg_word_length"
    "avg_paragraph_length_chars"
    "avg_paragraph_length_words"

    "alphanumeric_char_ratio"
    "control_char_ratio"
    "punctuation_char_ratio"
    "other_symbol_char_ratio"

    "tabs_word_ratio"
    "hashes_word_ratio"
    "ellipsis_ratio"
    "bulletpoint_ratio"

    'dup_paragraphs_ratio'
    'dup_paragraphs_char_ratio'

    'top_2_gram_char_ratio'
    'top_3_gram_char_ratio'
    'top_4_gram_char_ratio'

    'dup_5_gram_char_ratio'
    'dup_6_gram_char_ratio'
    'dup_7_gram_char_ratio'
    'dup_8_gram_char_ratio'
    'dup_9_gram_char_ratio'
    'dup_10_gram_char_ratio'
```
## Required parameters for the transform
| Name  | Default Value | Description |
|------------|----------|--------------|
| **enrichment_content_column_name** | **text** | The column with the content to process. |
| **enrichment_lang_column_name** | **lang** | The column name with language identifier for the content. Some of the feature computations require tokenized text as input, the value in this field is used to select the appropriate tokenizer. |
| **enrichment_output_column_prefix** | _not set_ | A prefix for the names of all the output columns. Please see the above NAME labels. Additionally, each column can be explicitly renamed, or if set to an empty string omitted from the output altogether. |

## Running the samples
To run the samples, use the following `make` target

* `run-cli-sample` - runs dpk_enrichment.runtime using command line args
or
* `run-ray-cli-sample` - runs dpk_enrichment.ray.runtime using command line args

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

[notebook](./enrichment.ipynb)

## Testing

Following [the testing strategy of data-processing-lib](../../../data-processing-lib/doc/transform-testing.md)

Currently we have:
- [Unit test](test/test_enrichment.py)