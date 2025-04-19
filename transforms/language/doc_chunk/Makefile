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


LINUX_WITH_CPU_TORCH?=true
OS := $(shell uname -s)
ifeq ($(OS),Linux)
	ifeq ($(LINUX_WITH_CPU_TORCH),true)
	PIP_INSTALL_EXTRA_ARGS=--extra-index-url=https://download.pytorch.org/whl/cpu
	DOCKER_BUILD_EXTRA_ARGS=--build-arg PIP_INSTALL_EXTRA_ARGS=${PIP_INSTALL_EXTRA_ARGS}
	endif
endif

# Used to generate expected data for Unit Test
run-cli-sample-json:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected'}"  \
            --doc_chunk_chunking_type dl_json


run-cli-sample-md:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
             --data_local_config "{ 'input_folder' : 'test-data/input_md', 'output_folder' : 'test-data/expected_md'}"  \
            --doc_chunk_chunking_type li_markdown

run-cli-sample-text:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
            --data_local_config "{ 'input_folder' : 'test-data/input_toke_text', 'output_folder' : 'test-data/expected_token_text'}"  \
            --doc_chunk_chunking_type li_token_text \
			--doc_chunk_output_chunk_column_name chunk_text
