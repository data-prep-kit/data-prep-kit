# Text Enrichment

## Summary 
This transform filters the data using conditions specified in a yaml file.

The input table must contain at the values specified in the filtering conditions, as well as a language identifier (`lang`).
The language identifier column name can be set with --filter_lang_column_name.
The yaml file with the filtering conditions can be specified with --filter_config.
Optionally a prefix can be added to the labels specified in the filtering conditions. This prefix can be set with --filter_column_prefix.

To facilitate multi-language processing the output column names can renamed with a common prefix, specified with --enrichment_output_column_prefix.
Additionally, each column can be rename using an the option --enrichment_NAME_column_name, where NAME is one of the labels below.
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
