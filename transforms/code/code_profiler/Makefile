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
export RUNTIME_HOST_ARCH=x86_64

run-cli-sample:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
			 --programming_language "programming_language" \
			 --contents "contents"

run-ray-cli-sample:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.transform \
		--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
        --run_locally True \
		--programming_language "programming_language" \
		--contents "contents"