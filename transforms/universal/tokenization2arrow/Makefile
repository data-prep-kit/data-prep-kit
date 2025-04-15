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

TRANSFORM_PYTHON_SRC="-m dpk_$(TRANSFORM_NAME).runtime"
TRANSFORM_RAY_SRC="-m dpk_$(TRANSFORM_NAME).ray.runtime"


run-cli-sample-python:
	# TODO: set env variable HF_TOKEN to download tokenizer from HF
	make venv
	source venv/bin/activate && \
	rm -rf output/ds02 && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
            --data_local_config "{ 'input_folder' : 'test-data/ds02/input', 'output_folder' : 'output/ds02'}"

run-cli-sample-ray:
	# TODO: set env variable HF_TOKEN to download tokenizer from HF
	make venv
	source venv/bin/activate && \
	rm -rf output/ds02 && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.runtime \
            --data_local_config "{ 'input_folder' : 'test-data/ds01/input', 'output_folder' : 'output/ds01'}" \
			--run_locally True
