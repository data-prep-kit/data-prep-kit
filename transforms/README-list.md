# DPK Python Transforms

## installation

The [transforms](https://github.com/data-prep-kit/data-prep-kit/blob/dev/transforms/README.md) are delivered as a standard pyton library available on pypi and can be installed using pip install:

`python -m pip install data-prep-toolkit-transforms[all]`
or
`python -m pip install data-prep-toolkit-transforms[ray, all]`
or
`python -m pip install data-prep-toolkit-transforms[language]`


installing the python transforms will also install  `data-prep-toolkit`

installing the ray transforms will also install  `data-prep-toolkit[ray]`

## Release notes:

### 1.1.1

	Include all code transforms as extra [code]
	Refactored code transforms (code_uality, code2parquet, header_cleanser, license select, proglang_select)
	Added ml-filter and enrichment
	renamed PDF2Parquet to Docling2Paruqet 

### 1.0.1
	Added Gneissweb transforms
	fdedup fix for windows
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



 
