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

installed.txt: requirements.txt
	make venv
	source venv/bin/activate && \
		python -m pip list > $@ \
	deactivate

run-cli-sample: installed.txt 
	source venv/bin/activate && \
	$(PYTHON) -m dpk_ml_filter.runtime \
		--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}" \
	   	--ml_filter_lang_column_name "lang" \
		--ml_filter_column_prefix "e_" \
		--ml_filter_config "test-data/input/cleansing-config.yaml" && \
	deactivate

run-ray-cli-sample: installed.txt 
	source venv/bin/activate && \
	$(PYTHON) -m dpk_ml_filter.ray.runtime --run_locally True \
		--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'ray-output'}" \
	   	--ml_filter_lang_column_name "lang" \
		--ml_filter_column_prefix "e_" \
		--ml_filter_config "test-data/input/cleansing-config.yaml" && \
	deactivate

