# Data Prep Kit Release notes

## Release 1.1.7 - 2/10/2025

### Transforms

1. Folder-to-Parquet Transform: Added a new transform that converts a folder of files into a unified Parquet dataset.
1. Text Encoder: Updated to use LanceDB for improved vector storage and retrieval performance.
1. Spark Support: Added Spark compatibility for both doc_quality and docling2parquet transforms.
1. Ededup: Fixed a type mismatch between str and int when using int_doc_id.

### General

1. Python 3.13 Support: Expanded compatibility to include Python 3.13.
1. Faster Installation with uv: Migrated repository to use uv for significantly faster environment setup and dependency installation.
1. Rich Logging: Introduced a Rich-based log handler for more readable, structured, and colorized console output.
1. Image Modeler Improvements: Updated model downloader to fetch YOLOv models used by the image transforms.

## Release 1.1.6 - 11/13/2025

### Transforms

1. OpenSearch Transform: Enables keyword and vector-based search capabilities using OpenSearch
   - If the table includes an embeddings column, the transform sets up a k-NN vector index for similarity searches.
1. Image Transform Modality: Introduced three new transforms for processing image data:
   - Faces: Detects people and faces using a pre-trained face detection model.
   - NSFW: Scores content for Not Safe For Work using Hugging Face image-classification pipeline.
   - People: Counts faces and supports face blurring for privacy.   
1. Docling2Parquet: Updated options to extract binary image data (images/pages) into a dedicated column (`image_bins`) in Parquet output.

### General

1. Tekton deployment yamls: Introduced Kubernetes deployment YAMLs for Tekton, simplifying pipeline composition without relying on Kubeflow Pipelines (KFP) infrastructure.
1. Input Handling: Expanded runtime input support to include ZIP, NDJSON, and JSON formats in addition to Parquet.
1. Logging System: Implemented a new JSON-based logging system that consolidates all DPK logs into a single logger.


## Release 1.1.5 - 10/2/2025

### Transforms

1. Granite Docling Integration: Enabled document parsing via docling2parquet, with options for VLM pipeline compatibility.

1. PII Redactor: Added support for cryptographic redaction.
1. GneissWeb: Enhanced multithreading and optimized model loading for better performance.
1. Filter Transform: Added safeguard to check if filter_criteria is None, preventing crashes when criteria are unset or empty.

### General

1. Python Multiprocessing: Introduced multiprocessing job support and resolved boto pickling errors for transform runtimes.


## Release 1.1.4 - 9/15/2025

### General

1. Improved logging to remove access and secret keys from config when present for legacy runs.
1. Resolved issues related to handling additional secrets when more than one secret added to config for kfp.


### Transforms

1. Added support for binary transforms and binary data in chained operations (new examples and test coverage provided).
1. Updated filter transform to return an empty table while preserving the original schema when filtering results in empty table
1. Updated tokenization2arrow to correctly process lists of texts.

### Dependency updates

1. Avoided using polars version 1.33 due to breaking changes.
1. Removed lower bound constraint on boto3 dependency.

## Release 1.1.3 - 8/18/2025

## General

1. Fixed the bug with MD file as input for docling2parquet 
1. Adjust tagged dependencies to ensure notebooks work in google collab environment
1. Prepare post1 release with patches 
1. Parse metadata.json at end of the run and flag for exceptions, removing errors where logs would show failure, but KFP would show success
1. Updated model_loader to utilize data_access_s3, enabling s3 I/O from different COS locations
1. Removing non-required torch dependency
1. Updated validation for data_access_local, allowing empty input_folder and/or output_folder (defaults to current directory)
1. Fixed bug with dividing by 0 in fine web quality annotator

## Release 1.1.2.post1 - 7/3/2025

## General

1. Patch filter failing when transform is used with default/empty configuration
1. Patch PII requirements for pydantic to allow testing with Prefect

## Release 1.1.2 - 7/3/2025

## General

1. Restructured data-access package to allow adding user specific connectors as external packages (e.g. lakehouse connector) 
1. Removed credentials being utilized as transform/data access arguments and now passed set as environment variable
1. Added runtime code location  environment variables to docker files to display real build information
1. Added in-memory data access for caching reads/writes in DataAccessLocal, and in new DataAccessMemory class. 
1. Added file batch processing for data access

### Transforms

1. Added transform chain module for running one more transforms in sequence, with support for parallel micro-batch execution
1. Added fineweb_quality_annotator and gopher_repetition_annotator transforms
1. Added model loader util for transforms utilizing models, enabling loading from COS, HuggingFace, and locally
1. Updated KPF workflows to remove setting runtime code location, and set credentials via environment variables


## Release 1.1.1 - 4/9/2025

## General

1. Move to the [Linux Foundation AI&DATA Organization](https://lfaidata.foundation/projects/data-prep-kit/) and re-assign roles for maintainers and contributors
1. Added logo, updated documentation and enforce signed contributions
1. Added support for Hugging Face credentials when running verification workflows
1. Added new transforms and bug fixes

### Transforms

1. Added Multi-lingual ML Filter and Enrichment(Quality annotation) transforms
1. Added Blockist and Collapse(Column concatenation) transforms
1. Added support for comments based semantic categories 
1. Ededup added parameter for optional removed field
1. Refactored all code transforms and published via wheel in pypi

### Recipes

1. Refactored, re-organized and continued improving notebooks and recipes


## Release 1.1.0 - 3/10/2025

## General

1. Updated tutorials and documentations
1. Added GneissWeb Transforms, GneissWeb recipe and support for XML ingest in Docling 
1. Bug fixes for Windows Support, KFP workflow pipelines, and CI/CD workflow

### Recipes
1. Updated RAG Notebooks for PDF and HTML
1. New GneissWeb Notebook showcasing advanced data prep operations for improved model performance
1. New Agentic Notebook showcasing integration with Langchain and Llama-index

### Transforms
1. GneissWeb transforms: [extreme tokenized](transforms/language/extreme_tokenized/README.md), [readability](transforms/language/readability/README.md), [gneissweb classification](transforms/language/gneissweb_classification/README.md), [Rep Removal](transforms/universal/rep_removal/README.md), [Tokenization2Arrow](transforms/universal/tokenization2arrow/README.md), [Bloom](transforms/universal/bloom/README.md)
1. Code Profiler: Added Support for CSharp
1. Header Cleanser: Enhanced with multi-processing support
1. Fuzzy Dedup: Support for Windows Folder names
1. PDF to Parquet: Update docling to 2.25 for ingesting XML/JATS
1. HAP: Assign 0 score for empty content

### data-prep-toolkit libraries (python, ray, spark) 

1. Disabled fcntl on Windows

### KFP Pipelines

1. Updated super pipeline KFPv2


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

1. Enhance docling2parquet with docling2 support for extracting HTML, DOCS, etc.
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

1. Added 7 new transdforms including: language identification, profiler, repo level ordering, doc quality, docling2parquet, HTML2Parquet and PII Transform
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

