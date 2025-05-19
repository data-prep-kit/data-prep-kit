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

# Developers should adapt this according to their implementation if they do not follow the proposed template
# We continue to refine this. The current settings are based on current template
TRANSFORM_PYTHON_SRC="-m dpk_$(TRANSFORM_NAME).runtime"
TRANSFORM_RAY_SRC="-m dpk_$(TRANSFORM_NAME).ray.runtime"
TRANSFORM_SPARK_SRC="-m dpk_$(TRANSFORM_NAME).spark.runtime"


run-cli:
	make venv
	source venv/bin/activate && \
	python -m dpk_collapse.runtime --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
	--collapse_input_columns "['title','contents']" --collapse_output_column "text2"

run-cli-ray:
	make venv
	source venv/bin/activate && \
	python -m dpk_collapse.ray.runtime --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
	--collapse_input_columns "['title','contents']" --collapse_output_column "text2" \
	--run_locally True



