# Data Prep Kit Release notes

## Release 1.0.0 - 1/24/2025

## General

1. Refactored all language transforms and implemented simplified APIs for the refactored transforms
1. Added notebook examples for each of the transforms 
1. Streamlined documentation and added tutorial for developers who want to build new transforms 
1. Other minor enhancements and bug fixes were done for transforms, workflow pipelines, and CI/CD makefiles

### Transforms

1. Added new similarity transform (for detecting confidentiality, copyright, and/or plagiarism in documents)


## Release 0.2.3 - 12/15/2024

## General

New algorithm for Fuzzy dedup transform
Sample notebooks for some of the language transforms
Integrate Semantic profiler and report generation for code profiler transform

### data-prep-toolkit libraries (python, ray, spark) 

1. Increase ray agent limit to 10,000 (default was 100) 

### Transforms

1. Fuzzy dedup new algorithm for Python, Ray and Spark

## Release 0.2.2 - 11/25/2024

### General 
1. Update RAG example to use granite model 
1. Updated transforms with Docling 2
1. Added single package for dpk with extra for \[spark\] and \[ray\]
1. Added single package for transforms with extra for \[all\] or \[individual-transform-name\]


### data-prep-toolkit libraries (python, ray, spark) 

1. Fix metadata logging even when actors crash 
1. Add multilock for ray workers downloads/cleanup
1. Multiple updates to spark runtime
1. Added support for python 3.12
1. refactoring of data access code


### KFP Workloads 

1. Modify superpipeline params type Str/json
1. Set kuberay apiserver version 
1. Add Super pipeline for code transforms


### Transforms

1. Enhance pdf2parquet with docling2 support for extracting HTML, DOCS, etc.
1. Added web2parquet transform
1. Added HAP transform

### HTTP Connector 0.2.3

1. Enhanced parameter/configuration allows the user to customize crawler settings 
1. implement subdomain focus feature in data-prep-connector 


## Release 0.2.2- HTTP Connector Module - 10/23/2024

### General 
1. Bug fixes across the repo
1. Minor enhancements and experimentation with single packaging techniques using \[extra\]
1. Decoupled the release process for each of the component so we can be more responsive to the needs of our stakeholders
1. The minor digit for the release for all components is incremented and the patch digit is reset to 0 for all new releases of the data-prep-toolkit
1. The patch digit for the release of any one component can be increased independently from other component patch number


### data-prep-toolkit-Connector

1. Released first version of the data-prep-toolkit-connector for crawling web sites and downloading HTML and PDF files for ingestion by the pipeline



## Release 0.2.1 - 9/24/2024

### General 
1. Bug fixes across the repo
1. Added AI Alliance RAG demo, tutorials and notebooks and tips for running on google colab
1. Added new transforms and single package for transforms published to pypi
1. Improved CI/CD with targeted workflow triggered on specific changes to specific modules
1. New enhancements for cutting a release


### data-prep-toolkit libraries (python, ray, spark) 

1. Restructure the repository to distinguish/separate runtime libraries
1. Split data-processing-lib/ray into python and ray
1. Spark runtime
1. Updated pyarrow version
1. Define required transform() method as abstract to AbstractTableTransform
1. Enables configuration of makefile to use src or pypi for data-prep-kit library dependencies 


### KFP Workloads 

1. Add a configurable timeout before destroying the deployed Ray cluster.

### Transforms

1. Added 7 new transdforms including: language identification, profiler, repo level ordering, doc quality, pdf2parquet, HTML2Parquet and PII Transform
1. Added ededup python implementation and incremental ededup 
1. Added fuzzy floating point comparison


## Release 0.2.0 - 6/27/2024

### General 
1. Many bug fixes across the repo, plus the following specifics.
1. Enhanced CI/CD and makefile improvements  include definition of top-level targets (clean, set-verions, build, publish, test)
1. Automation of release process branch/tag management
1. Documentation improvements 

### data-prep-toolkit libraries (python, ray, spark) 

1. Split libraries into 3 runtime-specific implementations
1. Fix missing final count of processed and add percentages
1. Improved fault tolerance in python and ray runtimes 
1. Report global DataAccess retry metric  
1. Support for binary data transforms
1. Updated to Ray version to 2.24
1. Updated to PyArrow version 16.1.0

### KFP Workloads 

1. Add KFP V2 support 
1. Create a distinct (timestamped) execution.log file for each retry
1. Support for multiple inputs/outputs

### Transforms

1. Added language/lang_id - detects language in documents
1. Added universal/profiler - counts works/tokens in documents
1. Converted ingest2parquet tool to transform named code2parquet
1. Split transforms, as appropriate, into python, ray and/or spark.
1. Added spark implementations of filter, doc_id and noop transforms.
1. Switch from using requirements.txt to pyproject.toml file for each transform runtime
1. Repository restructured to move kfp workflow definitions to associated transform project directory

## Release 0.1.1 - 5/24/2024

## Release 0.1.0 - 5/15/2024

## Release 0.1.0 - 5/08/2024

