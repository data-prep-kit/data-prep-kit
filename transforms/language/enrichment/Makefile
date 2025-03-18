REPOROOT=../../..
# Use make help, to see the available rules
include $(REPOROOT)/transforms/.make.cicd.targets

# Until we make runtime.py the standard supported by Makefile infra
TRANSFORM_PYTHON_SRC="-m dpk_$(TRANSFORM_NAME).runtime"
TRANSFORM_RAY_SRC="-m dpk_$(TRANSFORM_NAME).ray.runtime"
TRANSFORM_SPARK_SRC="-m dpk_$(TRANSFORM_NAME).spark.runtime"

#
# This is intended to be included across the Makefiles provided within
# a given transform's directory tree,  so must use compatible syntax.
#
################################################################################
# This defines the name of the transform and is used to match against
# expected files and is used to define the transform's image name. 
TRANSFORM_NAME=$(shell basename `pwd`)

################################################################################

TEST_PARAMS?=--enrichment_content_column_name text \
            --enrichment_lang_column_name lang \
            --enrichment_output_column_prefix e_

installed.txt: requirements.txt
	make venv
	source venv/bin/activate && \
		python -m pip install jupyterlab notebook pandas && \
		python -m pip list > $@ && \
	deactivate

run-cli-sample: installed.txt 
	source venv/bin/activate && \
	$(PYTHON) -m dpk_enrichment.runtime \
		--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}" \
		$(TEST_PARAMS) && \
	deactivate

run-ray-cli-sample: installed.txt 
	source venv/bin/activate && \
	$(PYTHON) -m dpk_enrichment.ray.runtime --run_locally True \
		--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'ray-output'}" \
		$(TEST_PARAMS) && \
	deactivate

