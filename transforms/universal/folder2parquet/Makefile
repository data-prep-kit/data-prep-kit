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

generate-expected:
	$(MAKE) venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected'}" \
			 --data_files_to_use "['.txt','.zip']"

	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected2'}" \
			 --data_files_to_use "['.txt','.zip']" \
             --f2p_fewer_parquets "True"

test-cli:
	$(MAKE) venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/output'}" \
			 --data_files_to_use "['.txt','.zip', 'pdf']"
