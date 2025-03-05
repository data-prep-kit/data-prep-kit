# DPK Python Transforms

## installation

The [transforms](https://github.com/IBM/data-prep-kit/blob/dev/transforms/README.md) are delivered as a standard pyton library available on pypi and can be installed using pip install:

`python -m pip install data-prep-toolkit-transforms[all]`
or
`python -m pip install data-prep-toolkit-transforms[ray, all]`
or
`python -m pip install data-prep-toolkit-transforms[language]`


installing the python transforms will also install  `data-prep-toolkit`

installing the ray transforms will also install  `data-prep-toolkit[ray]`

## List of Transforms in current package

Note: This list includes the transforms that were part of the release starting with data-prep-toolkit-transforms:0.2.1. This list may not always reflect up to date information. Users are encourage to raise an issue in git when they discover missing components or packages that are listed below but not in the current release they get from pypi.

* code
    * [code2parquet](https://github.com/IBM/data-prep-kit/blob/dev/transforms/code/code2parquet/python/README.md)
    * [header_cleanser (Not available on MacOS)](https://github.com/IBM/data-prep-kit/blob/dev/transforms/code/header_cleanser/python/README.md)
    * [code_quality](https://github.com/IBM/data-prep-kit/blob/dev/transforms/code/code_quality/python/README.md)
    * [proglang_select](https://github.com/IBM/data-prep-kit/blob/dev/transforms/code/proglang_select/python/README.md)
    * [code_profiler](https://github.com/IBM/data-prep-kit/blob/dev/transforms/code/code_profiler/README.md)
* language
    * [doc_chunk](https://github.com/IBM/data-prep-kit/blob/dev/transforms/language/doc_chunk/README.md)
	* [doc_quality](https://github.com/IBM/data-prep-kit/blob/dev/transforms/language/doc_quality/README.md)
	* [lang_id](https://github.com/IBM/data-prep-kit/blob/dev/transforms/language/lang_id/README.md)
	* [pdf2parquet](https://github.com/IBM/data-prep-kit/blob/dev/transforms/language/pdf2parquet/README.md)
	* [text_encoder](https://github.com/IBM/data-prep-kit/blob/dev/transforms/language/text_encoder/README.md)
	* [pii_redactor](https://github.com/IBM/data-prep-kit/blob/dev/transforms/language/pii_redactor/python/README.md)
* universal
    * [ededup](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/ededup/README.md)
    * [fdedup](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/fdedup/README.md)
	* [filter](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/filter/python/README.md)
	* [resize](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/resize/python/README.md)
	* [tokenization](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/tokenization/README.md)
	* [doc_id](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/doc_id/README.md)
	* [web2parquet](https://github.com/IBM/data-prep-kit/blob/dev/transforms/universal/web2parquet/README.md)
   
## Release notes:

### 1.0.1.dev1
	Added Gneissweb transforms
	fdedup fix for windows
### 1.0.1.dev0
	PR #979 (code_profiler)
### 1.0.0.a6
	Added Profiler
	Added Resize
### 1.0.0.a5
	Added Pii Redactor
	Relax fasttext requirement >= 0.9.2
### 1.0.0.a4
	Added missing ray implementation for lang_id, doc_quality, tokenization and filter
	Added ray notebooks for lang id, Doc Quality, tokenization, and Filter
### 1.0.0.a3
	Added code_profiler
### 1.0.0.a2
   Relax dependencies on pandas (use latest or whatever is installed by application)
   Relax dependencies on requests (use latest or whatever is installed by application)



 
