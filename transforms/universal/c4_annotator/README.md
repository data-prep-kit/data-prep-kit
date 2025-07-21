# C4 Annotator 
Please see the set of
[transform project conventions](../../README.md)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
This annotator applies heuristic rules from C4 https://jmlr.org/papers/volume21/20-074/20-074.pdf
It follows the reference implementations from [Tensorflow](https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/text/c4_utils.py#L197) and [Datatrove](https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/c4_filters.py) but, instead of filtering out data, it is annotated. Based on these annotations, data can be filtered later.

Apply C4 Quality filters
- Retain only lines that end in a terminal punctuation mark (! . " ?)
- Discard any page with fewer than 5 sentences and only retain lines that contain at least 3 words
- [NOT IMPLEMENTED] Remove any page that contained any word on the “List of Dirty, Naughty, Obscene or Otherwise Bad Words”
- Remove any line with the word Javascript.
- Remove any page where the phrase “lorem ipsum” appears
- Remove any pages that contain a curly bracket

Additional filters not mentioned on the list from the paper but on the code:
- Remove lines with one word over 1000 chars
- Remove lines with cookies and terms of use keywords

Apply paragraph filtering from C4
- Remove the documents that have too few or too short paragraphs.

Apply badwords filter from C4
- Remove the documents containing more than a specific fraction of bad words

## Configuration and command line Options

The set of dictionary keys holding [AnnotatorC4Transform](dpk_c4_annotator/transform.py ) 
configuration for values are as follows:

* _c4a_contents_column_name_ - specifies the name of the column holding the document text
* _c4a_clean_contents_column_name_ - specifies the name of the column where the cleaned document is saved in the output table. This column is **added** to the output tables.  The default is `text`.
* _c4a_drop_reason_column_name_ - specifies the name of the column where the reason to drop a document (an empty string for the documents that are kept) is saved in the output table. This column is **added** to the output tables.  The default is `drop_reason`.
* _c4a_doc_stats_column_name_ - specifies the name of the column where the document stats are saved in the output table. This column is **added** to the output tables. The default is `doc_stats`.
* _c4a_tokenizer_language_ - specifies the language for which a specific punkt tokenizer from nltk will be loaded. Currently, only English (`en`) language is supported.
* _c4a_split_paragraph_ - if True, split the document text on "\n".  Set to False to apply the filters to each sentence instead of to each line. The default is `True`.
* _c4a_remove_citations_cli_param_ - if True, remove wikipedia style citations from the text. The default is `True`.
* _c4a_filter_no_terminal_punct_ - if True, remove lines without terminal punctuation marks. The default is `True`.
* _c4a_min_num_sentences_ - specifies the minimum number of sentences (after line filtering) in a valid document. Set to -1 to disable. The default is `5`.
* _c4a_min_words_per_line_ - specifies the minimum number of words in a valid line. Set to -1 to disable.  The default is `3`.
* _c4a_max_word_length_ - specifies the maximum length of a valid word. Drop the lines with words longer than this limit. Set to -1 to disable. The default is `1000`.
* _c4a_filter_lorem_ipsum_ - if True, mark for deletion the documents that contain "lorem ipsum". The default is `True`.
* _c4a_filter_javascript_ - if True, drop lines mentioning "javascript". The default is `True`.
* _c4a_filter_curly_bracket_ - if True, drop documents containing '{' or '}'. The default is `True`.
* _c4a_filter_policy_ - if True, drop lines containing any of the phrases in POLICY_SUBSTRINGS. The default is `True`.
* _c4a_min_paragraphs_ - specifies the minimum number of valid paragraphs in a valid document. Set to -1 to disable. The default is `3`.
* _c4a_min_paragraph_len_ - specifies the minimum length of a valid paragraph in a document. Set to -1 to disable. The default is `200`.
* _c4a_paragraph_delimiter_ - specifies the character used to delimit paragraphs. The default is `\n`.
* _c4a_ldnoobw_url_ - specifies the URL from which the LDNOOBW list will be retrieved.
* _c4a_filter_badwords_ - if True, mark for deletion documents containing bad words. The default is `False`.
* _c4a_badwords_keep_fraction_ - specifies the percentage of pages containing bad words that should be kept.  The default is `0.0`.
* _c4a_badwords_seed_ - specifies the seed used for the uniform distribution generator for use with keep_fraction. The default is `None`.

Additionally, a set of data access-specific arguments are provided that enable
the specification of the location of domain list files, so that these
files could be stored in the local file system or in S3 storage, for example.
The arguments are as follows (and generally match the TransformLauncher's 
data access arguments but with the `c4a_' prefix).

* _c4a_local_config_ - specifies the input and outout folders, although these are not used by the transform.
* _c4a_s3_config_ - specifies the input and output paths in s3.
* _c4a_s3_credentials_ - provides credentials to access the s3 storage. 

See the Command Line options below for specifics on these.

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).
```
options:
  -h, --help            show this help message and exit
  --c4a_contents_column_name C4A_CONTENTS_COLUMN_NAME
                        Name of the column holding the document text
  --c4a_clean_contents_column_name C4A_CLEAN_CONTENTS_COLUMN_NAME
                        Name of the column where the cleaned document is saved in the output table
  --c4a_drop_reason_column_name C4A_DROP_REASON_COLUMN_NAME
                        Name of the column where the keep document decision (true/false) is saved
  --c4a_doc_stats_column_name C4A_DOC_STATS_COLUMN_NAME
                        Name of the column where the document stats are saved
  --c4a_tokenizer_language C4A_TOKENIZER_LANGUAGE
                        Language for which a specific punkt tokenizer from nltk will be loaded
  --c4a_split_paragraph C4A_SPLIT_PARAGRAPH
                        If True, split on '
                        ' Set to False to apply the filters to each sentence instead of to each line
  --c4a_remove_citations C4A_REMOVE_CITATIONS
                        If True, remove wikipedia style citations from the text
  --c4a_filter_no_terminal_punct C4A_FILTER_NO_TERMINAL_PUNCT
                        If True, remove lines without terminal punctuation marks
  --c4a_min_num_sentences C4A_MIN_NUM_SENTENCES
                        Minimum number of sentences (after line filtering) in a valid document. Set to -1 to disable
  --c4a_min_words_per_line C4A_MIN_WORDS_PER_LINE
                        Minimum number of words in a valid line. Set to -1 to disable
  --c4a_max_word_length C4A_MAX_WORD_LENGTH
                        Maximum length of a word; drop lines with longer words. Set to -1 to disable
  --c4a_filter_lorem_ipsum C4A_FILTER_LOREM_IPSUM
                        If True, mark for deletion the documents that contain 'lorem ipsum'
  --c4a_filter_javascript C4A_FILTER_JAVASCRIPT
                        If True, drop lines mentioning 'javascript'
  --c4a_filter_curly_bracket C4A_FILTER_CURLY_BRACKET
                        If True, drop documents containing '{' or '}'
  --c4a_filter_policy C4A_FILTER_POLICY
                        If True, drop lines containing any of the phrases in POLICY_SUBSTRINGS
  --c4a_min_paragraphs C4A_MIN_PARAGRAPHS
                        Minimum number of valid paragraphs in a valid document. Set to -1 to disable
  --c4a_min_paragraph_len C4A_MIN_PARAGRAPH_LEN
                        Minimum length of a valid paragraph. Set to -1 to disable
  --c4a_paragraph_delimiter C4A_PARAGRAPH_DELIMITER
                        The character used to delimit paragraphs
  --c4a_ldnoobw_url C4A_LDNOOBW_URL
                        The URL from which the LDNOOBW list will be retrieved
  --c4a_filter_badwords C4A_FILTER_BADWORDS
                        If True, mark for deletion documents containing bad words
  --c4a_badwords_keep_fraction C4A_BADWORDS_KEEP_FRACTION
                        Percentage of pages containing bad words that should be kept
  --c4a_badwords_seed C4A_BADWORDS_SEED
                        The seed used for the uniform distribution generator for use with keep_fraction
  --c4a_s3_cred C4A_S3_CRED
                        AST string of options for s3 credentials. Only required for S3 data access.
                        access_key: access key help text
                        secret_key: secret key help text
                        url: optional s3 url
                        region: optional s3 region
                        Example: { 'access_key': 'access', 'secret_key': 'secret', 
                        'url': 'https://s3.us-east.cloud-object-storage.appdomain.cloud', 
                        'region': 'us-east-1' }
  --data_s3_cred DATA_S3_CRED
                        AST string of options for s3 credentials. Only required for S3 data access.
                        access_key: access key help text
                        secret_key: secret key help text
                        url: optional s3 url
                        region: optional s3 region
                        Example: { 'access_key': 'access', 'secret_key': 'secret', 
                        'url': 'https://s3.us-east.cloud-object-storage.appdomain.cloud', 
                        'region': 'us-east-1' }
  --data_s3_config DATA_S3_CONFIG
                        AST string containing input/output paths.
                        input_folder: Path to input folder of files to be processed
                        output_folder: Path to output folder of processed files
                        Example: { 'input_folder': 's3-path/your-input-bucket', 
                        'output_folder': 's3-path/your-output-bucket' }
  --data_local_config DATA_LOCAL_CONFIG
                        ast string containing input/output folders using local fs.
                        input_folder: Path to input folder of files to be processed
                        output_folder: Path to output folder of processed files
                        Example: { 'input_folder': './input', 'output_folder': '/tmp/output' }
  --data_max_files DATA_MAX_FILES
                        Max amount of files to process
  --data_checkpointing DATA_CHECKPOINTING
                        checkpointing flag
  --data_files_to_checkpoint DATA_FILES_TO_CHECKPOINT
                        list of file extensions to choose for checkpointing.
  --data_data_sets DATA_DATA_SETS
                        List of sub-directories of input directory to use for input. For example, ['dir1', 'dir2']
  --data_files_to_use DATA_FILES_TO_USE
                        list of file extensions to choose for input.
  --data_num_samples DATA_NUM_SAMPLES
                        number of random input files to process
  --runtime_pipeline_id RUNTIME_PIPELINE_ID
                        pipeline id
  --runtime_job_id RUNTIME_JOB_ID
                        job id
