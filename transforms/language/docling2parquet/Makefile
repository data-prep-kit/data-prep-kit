REPOROOT=../../..
# Use make help, to see the available rules
include $(REPOROOT)/transforms/.make.cicd.targets

#
# This is intended to be included across the Makefiles provided within
# a given transform's directory tree,  so must use compatible syntax.
#
################################################################################
# This defines the name of the transform and is used to match against
# expected files and is used to define the transform's image name. 
TRANSFORM_NAME=$(shell basename `pwd`)

################################################################################


#### user defined Target

LINUX_WITH_CPU_TORCH?=true
OS := $(shell uname -s)
ifeq ($(OS),Linux)
	ifeq ($(LINUX_WITH_CPU_TORCH),true)
	PIP_INSTALL_EXTRA_ARGS=--extra-index-url=https://download.pytorch.org/whl/cpu
	DOCKER_BUILD_EXTRA_ARGS=--build-arg PIP_INSTALL_EXTRA_ARGS=${PIP_INSTALL_EXTRA_ARGS}
	endif
endif

run-cli-sample:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'expected_json'}"  \
				--data_files_to_use "['.pdf','.zip','.xml']"

run-cli-granite:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
             --data_local_config "{ 'input_folder' : 'test-data/granite_docling_input', 'output_folder' : 'expected_json'}"  \
				--data_files_to_use "['.pdf']" \
				--docling2parquet_contents_type "application/json" \
                --docling2parquet_pipeline "vlm"


generate-expected:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
			 --data_files_to_use "['.pdf','.docx','.pptx','.xml','.zip']" \
			 --docling2parquet_double_precision 0 \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected'}"
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
			 --data_files_to_use "['.pdf','.docx','.pptx','.xml','.zip']" \
			 --docling2parquet_double_precision 0 \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected_batch'}"  \
             --docling2parquet_batch_size 10
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
			 --data_files_to_use "['.pdf','.docx','.pptx','.xml','.zip']" \
			 --docling2parquet_double_precision 0 \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected_md_no_table_no_ocr'}"  \
             --docling2parquet_contents_type "text/markdown" \
			 --docling2parquet_do_ocr False \
			 --docling2parquet_do_table_structure False
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
			 --data_files_to_use "['.pdf','.docx','.pptx','.xml','.zip']" \
			 --docling2parquet_double_precision 0 \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected_json'}"  \
             --docling2parquet_contents_type "application/json"
