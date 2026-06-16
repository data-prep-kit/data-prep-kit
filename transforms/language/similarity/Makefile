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



run-cli-sample:
	$(MAKE) venv
	@source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
				--similarity_es_pwd $(SIMILARITY_ES_PWD) \
				--similarity_es_userid $(SIMILARITY_ES_USERID) \
				--similarity_es_endpoint $(SIMILARITY_ES_ENDPOINT) \
				--similarity_es_index "cnn_dailymail"

run-local-sample:
	$(MAKE) venv
	@source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).local


run-local-python-sample:
	$(MAKE) venv
	@source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).local_python
