# Readability Scores Annotator 
Please see the set of
[transform project conventions](../../README.md)
for details on general project conventions, transform configuration, testing and IDE set up.

## Contributors
- Hajar Emami Gohari (Hajar.Emami@ibm.com)
- Constantin Adam (cmadam@us.ibm.com)

## Summary
This transform annotates documents of a parquet file with various Readability Scores (originally defined
in the [textstat github page](https://textstat.org)]) that can later be used in Quality Filtering.
The transform annotates the following readability scores:
 
- `flesch_ease_textstat` - while the maximum score is 121.22, there is no limit on how low the score can be. A negative score is valid.
the values for this score are explained in the table below:

   | Score | School level (US)   | Notes |
   |-----|---------------------|-----|
   | 100.00–90.00 | 	5th grade	         |           Very easy to read. Easily understood by an average 11-year-old student.
   | 90.0–80.0	| 6th grade	          | Easy to read. Conversational English for consumers.
   | 80.0–70.0	| 7th grade	          | Fairly easy to read.
   |70.0–60.0	|   8th & 9th grade	 | Plain English. Easily understood by 13- to 15-year-old students.
   | 60.0–50.0	| 10th to 12th grade	 | Fairly difficult to read.                                      
   | 50.0–30.0	| College	          | Difficult to read.                                            
   | 30.0–10.0	| College graduate	 | Very difficult to read. Best understood by university graduates.
   | 10.0–0.0	| Professional	       | Extremely difficult to read. Best understood by university graduates.

- `flesch_kincaid_textstat` - this is a grade formula in that a score of 9.3 means that a ninth grader
   would be able to read the document.
- `gunning_fog_textstat` - this is a grade formula in that a score of 9.3 means that a ninth grader
   would be able to read the document.
- `smog_index_textstat` -  the SMOG index of the given text. This is a grade formula in that a score
   of 9.3 means that a ninth grader would be able to read the document. Texts of fewer than 30 
   sentences are statistically invalid, because the SMOG formula was normed on 30-sentence samples. 
   Textstat requires at least 3 sentences for a result. 
- `coleman_liau_index_textstat` - the grade level of the text using the Coleman-Liau Formula. This is 
   a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document. 
- `automated_readability_index_textstat` - the ARI (Automated Readability Index) which outputs a
   number that approximates the grade level needed to comprehend the text. For example if the ARI is
   6.5, then the grade level to comprehend the text is 6th to 7th grade.
- `dale_chall_readability_score_textstat` - different from other tests, since it uses a lookup table
   of the most commonly used 3000 English words. Thus it returns the grade level using the New
   Dale-Chall Formula. Further reading on https://en.wikipedia.org/wiki/Dale–Chall_readability_formula
   The table below further explains the values assigned by this score:

  | Score	    |        Understood by |
  |--------|-------------|
  | 4.9 or lower	|    average 4th-grade student or lower
  | 5.0–5.9	     |   average 5th or 6th-grade student
  | 6.0–6.9	     |  average 7th or 8th-grade student
  | 7.0–7.9	      |  average 9th or 10th-grade student
  | 8.0–8.9	       | average 11th or 12th-grade student
  | 9.0–9.9	        | average 13th to 15th-grade (college) student

- `linsear_write_formula_textstat` - the grade level using the Linsear Write Formula. This is a grade
formula in that a score of 9.3 means that a ninth grader would be able to read the document. Further
reading on Wikipedia https://en.wikipedia.org/wiki/Linsear_Write
- `text_standard_textstat` - based upon all the above tests, returns the estimated school grade level
required to understand the text. Optional float_output allows the score to be returned as a float.
Defaults to False.
- `spache_readability_textstat` - the grade level of english text. Intended for text written for
children up to grade four.
- `mcalpine_eflaw_textstat` - a score for the readability of an english text for a foreign learner
or English, focusing on the number of miniwords and length of sentences. 
- `reading_time_textstat` - the reading time of the given text. Assumes 14.69ms per character. 
- `avg_grade_level` - average of grade-level scores `flesch_kincaid`, `gunning_fog`, and 
`automated_readability_index`

## Configuration and command line Options

The set of dictionary keys holding [ReadabilityTransform](dpk_readability/runtime.py) configuration for values are as follows:

* _readability_contents_column_name_ - specifies the name of the column holding the document text. The default is `text`.
* _readability_score_list_ - list of readability scores to be computed by the transform;
  valid values: `coleman_liau_index_textstat`, `flesch_kincaid_textstat`,
  `difficult_words_textstat`, `spache_readability_textstat`, `smog_index_textstat`,
  `reading_time_textstat`, `dale_chall_readability_score_textstat`, `text_standard_textstat`,
  `automated_readability_index_textstat`, `gunning_fog_textstat`, `flesch_ease_textstat`,
  `mcalpine_eflaw_textstat`, `linsear_write_formula_textstat`.


Additionally, a set of data access-specific arguments are provided that enable
the specification of the location of domain list files, so that these
files could be stored in the local file system or in S3 storage, for example.
The arguments are as follows (and generally match the TransformLauncher's 
data access arguments but with the `readability_' prefix).

* _readability_local_config_ - specifies the input and output folders.
* _readability_s3_config_ - specifies the input and output paths in s3.
* _readability_s3_credentials_ - provides credentials to access the s3 storage.

See the Command Line options below for specifics on these.

## Running
You can run the [readability module](dpk_readability/runtime.py) to
transform the `readability-test.parquet` file in [test input data](test-data/input) 
to an `output` directory.  The output directory will contain both the new
annotated `readability-test.parquet` file and the `metadata.json` file.
<pre>
cma:readability$ make venv PYTHON=python3.11
cma:readability$ source venv/bin/activate
(venv) cma:readability$ python -m dpk_readability.runtime --data_local_config "{ 'input_folder': 'test-data/input', 'output_folder': 'output' }" --readability_score_list "['reading_time_textstat','spache_readability_textstat','text_standard_textstat']"
13:07:23 INFO - Launching Readability transform
13:07:23 INFO - Readability parameters are : {'readability_contents_column_name': 'contents', 'readability_score_list': ['reading_time_textstat', 'spache_readability_textstat', 'text_standard_textstat']}
13:07:23 INFO - pipeline id pipeline_id
13:07:23 INFO - code location None
13:07:23 INFO - data factory data_ is using local data access: input_folder - test-data/input output_folder - output
13:07:23 INFO - data factory data_ max_files -1, n_sample -1
13:07:23 INFO - data factory data_ Not using data sets, checkpointing False, max files -1, random samples -1, files to use ['.parquet'], files to checkpoint ['.parquet']
13:07:23 INFO - orchestrator readability started at 2025-02-07 13:07:23
13:07:23 INFO - Number of files is 1, source profile {'max_file_size': 0.014194488525390625, 'min_file_size': 0.014194488525390625, 'total_file_size': 0.014194488525390625}
13:07:24 INFO - Completed 1 files (100.0%) in 0.002 min
13:07:24 INFO - Done processing 1 files, waiting for flush() completion.
13:07:24 INFO - done flushing in 0.0 sec
13:07:24 INFO - Completed execution in 0.002 min, execution result 0
(venv) cma:readability$ deactivate
</pre>

### Building the Docker Images
```shell
(venv) cma:readability$ make image 
...
(venv) cma:readability$ podman images
REPOSITORY                                                  TAG       IMAGE ID       CREATED              SIZE
readability-ray                                             latest    eb753e168d29   49 seconds ago       2.66GB
quay.io/dataprep1/data-prep-kit/readability-ray             latest    eb753e168d29   49 seconds ago       2.66GB
readability-python                                          latest    7f15c1d5d63d   About a minute ago   651MB
quay.io/dataprep1/data-prep-kit/readability-python          latest    7f15c1d5d63d   About a minute ago   651MB
````
In addition, there are some useful `make` targets (see conventions above)
or use `make help` to see a list of available targets.

### Launched Command Line Options 
When running the transform with the Ray launcher (i.e. TransformLauncher),
the following command line arguments are available in addition to 
[the options provided by the launcher](../../../data-processing-lib/doc/launcher-options.md).
```
options:
  -h, --help            show this help message and exit
  --readability_contents_column_name READABILITY_CONTENTS_COLUMN_NAME
                        contents column name for input parquet table to transform
  --readability_score_list READABILITY_SCORE_LIST
                        list of readability scores to be computed by the transform; valid values: {'flesch_ease_textstat', 'reading_time_textstat', 'flesch_kincaid_textstat', 'automated_readability_index_textstat', 'linsear_write_formula_textstat', 'text_standard_textstat', 'smog_index_textstat', 'difficult_words_textstat', 'spache_readability_textstat', 'dale_chall_readability_score_textstat', 'mcalpine_eflaw_textstat', 'gunning_fog_textstat', 'coleman_liau_index_textstat'}
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
  --runtime_num_processors RUNTIME_NUM_PROCESSORS
                        size of multiprocessing pool
  --runtime_pipeline_id RUNTIME_PIPELINE_ID
                        pipeline id
  --runtime_job_id RUNTIME_JOB_ID
                        job id
  --runtime_code_location RUNTIME_CODE_LOCATION
                        AST string containing code location
                        github: Github repository URL.
                        commit_hash: github commit hash
                        path: Path within the repository
                        Example: { 'github': 'https://github.com/somerepo', 'commit_hash': '1324', 
                        'path': 'transforms/universal/code' }

