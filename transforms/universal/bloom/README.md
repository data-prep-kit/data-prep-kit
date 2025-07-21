# Bloom Annotation

## Summary
Recently, IBM has introduced GneissWeb; a large dataset yielding around 10 trillion tokens that
caters to the data quality and quantity requirements of training LLMs. The models trained using GneissWeb dataset outperform
those trained on FineWeb by 2.14 percentage points in terms of average score computed
on a set of 11 commonly used benchmarks.

The Bloom Annotator transform assigns a label of 1 if the document is present in the GneissWeb Bloom filter; otherwise, it assigns 0. This approach provides a clear understanding of which documents in FineWeb are also present in GneissWeb and which are not. The GneissWeb Bloom filter is just one use case; the Bloom Annotator transform can work with any Bloom filter. 

Bloom annotator transform maps a non-empty input table to an output table with an added is_in_GneissWeb column. Each row in the table corresponds to a UUID and its associated document. The Bloom annotator transform verifies whether the document's UUID exists in the GneissWeb Bloom filter.

In order to be able to reproduce GneissWeb, we provide [here](https://huggingface.co/ibm-granite/GneissWeb.bloom) a Bloom filter representing all the document ids of FineWeb 1.1.0 whose documents are part of GneissWeb. It is of size 28GB and is of the rbloom family of Bloom filters. It is to be probed with the id column of FineWeb 1.1.0 or of Common Crawl. Due to the large size of the model, a machine with larger than 16GB of memory is needed to run the transform on the local machine. 

## Contributor
- Yang Zhao (yangzhao@ibm.com)

## General Information
Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions, transform configuration, testing and IDE set up.

## Prerequisite 
Please refer to `requirements.txt` to install the necessary packages.


### input format
The input is in .parquet format and contains the following columns:

| id  | contents | 
|:------:|:------:|
| &lt;urn:uuid:39147604-bfbe-4ed5-b19c-54105f8ae8a7&gt;  |   Viewing Single Post From: Spoilers for the We...   |
| &lt;urn:uuid:ba819eb7-e6e6-415a-87f4-0347b6a4f017&gt;  |    *sigh* Fundamentalist community, let me pass o...  |


### output format
The output is in .parquet format and includes an additional column, in addition to those in the input:

| id  | contents | is_in_GneissWeb  |
|:------:|:------:|:------:|
| &lt;urn:uuid:39147604-bfbe-4ed5-b19c-54105f8ae8a7&gt;  |    Viewing Single Post From: Spoilers for the We...   | 0     |
| &lt;urn:uuid:ba819eb7-e6e6-415a-87f4-0347b6a4f017&gt;  |    *sigh* Fundamentalist community, let me pass o...  | 1     |

## Configuration 
The set of dictionary keys holding [BLOOMTransformConfiguration](dpk_bloom/transform.py) 
configuration for values are as follows:


* --model_name_or_path - specify the GneissWeb Bloom filter model, which should be sourced from HuggingFace. 
* --batch_size - modify it based on the infrastructure capacity. Defaults to `1000`.
* --doc_text_column - the column name containing the document text in the input .parquet file. Defaults to `contents`.
* --annotation_column - the column name containing binary score in the output .parquet file. Defaults to `is_in_GneissWeb`.
  


## Usage
Place your input Parquet file in the `test-data/input/` directory. A sample file, `test1.parquet`, is available in this directory. Once done, run the script.

```python
python local_python.py
```

You will obtain the output file `test1.parquet` in the output directory.

### Code example
[notebook](bloom_python.ipynb)


## Testing

Currently we have:
- [bloom test](test/test_bloom.py)
