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
TRANSFORM_SPARK_SRC="-m dpk_$(TRANSFORM_NAME).spark.runtime"


generate-expected:
	$(MAKE) venv
	source venv/bin/activate && \
	DPK_DPK_RESIZE_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected-mbytes-1'}" \
			 --resize_max_mbytes_per_table 1
	source venv/bin/activate && \
	DPK_DPK_RESIZE_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected-mbytes-0.05'}" \
			 --resize_max_mbytes_per_table "0.05"
	source venv/bin/activate && \
	DPK_DPK_RESIZE_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected-mbytes-0.02'}" \
			 --resize_max_mbytes_per_table "0.02"
	source venv/bin/activate && \
	DPK_DPK_RESIZE_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected-rows-125'}" \
			 --resize_max_rows_per_table 125
	source venv/bin/activate && \
	DPK_DPK_RESIZE_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
             --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected-rows-300'}" \
			 --resize_max_rows_per_table 300

