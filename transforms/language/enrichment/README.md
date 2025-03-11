# Text Enrichment

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
