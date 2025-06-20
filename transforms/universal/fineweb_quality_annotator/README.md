# FineWeb Quality Annotator

Please see the set of [transform project conventions](../../README.md) for details on general project conventions transform configuration, testing and IDE set up.

## Contributors

 - Constantin Adam (cmadam@us.ibm.com)

## Description

This annotator applies heuristic rules described in page 7 of the [**FineWeb Datasets paper**](https://arxiv.org/pdf/2406.17557). It follows the [**Datatrove reference implementation**](https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/fineweb_quality_filter.py).

This Transform does not remove any data, it only stores for each document four values that can be subsequently used to filter out documents using specific threshold values, such as those specified in the FineWeb reference implementation of the FineWeb Quality filters as:

    Discard documents where the fraction of lines ending with punctuation is <= 0.12 
    Discard documents where the fraction of characters in duplicated lines is >= 0.1
    Discard the documents where the fraction of lines shorter than 30 characters is >= 0.67
    Discard the documents where the ratio between new lines ('\n') and words is >= 0.3

Please note that the filter steps needs to be run separately on output produced by this annotation transform.


## Input 

The input table contains a column, by default named `text` holding the document text.

## Output 

The output table is annotated to include few new columns for values as follows:

- frac_line_punct - this column stors the fraction of lines that end with punctuation. Default is frac_line_punct.
- dup_line_char_frac - this column stors the duplicate line character fraction
- new_line_ratio - this column stors the ratio between the number of new lines and the total number of words.
- short_line_frac - this column stores the fraction of short lines.

## Configuration and command line Options

* _fineweb_quality_contents_column_name_ ( default value: `text` ) - Name of the column holding the document text used as as input
* _fineweb_quality_frac_line_punct_cname_ ( default value: `frac_line_punct` ) - Name of the output table column storing the fraction of lines that end with punctuation.
* _fineweb_quality_dup_line_char_frac_cname_ ( default value: `dup_line_char_frac`) - Name of the output table column storing the duplicate line character fraction.
* _fineweb_quality_new_line_ratio_cname_ ( default value: `new_line_ratio` ) - Name of the output table column storing the ratio between the number of new lines and the total number of words.
* _fineweb_quality_short_line_frac_cname_ ( default value: `short_line_frac` ) - Name of the output table column storing the fraction of short lines.
* _fineweb_quality_short_line_length_ ( default value: `30` ) - Maximum length of a short line.


Additionally, a set of data access-specific arguments are provided that enable the specification of the location of domain list files, so that these files could be stored in the local file system or in S3 storage, for example. The arguments generally match the TransformLauncher's data access arguments but with the `fineweb_quality_` prefix.
