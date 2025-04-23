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



# Used primarily to regenerate expected files used by make Unit Test
run-sample-cli:
	make venv \
	&& source venv/bin/activate \
	&& python -m dpk_header_cleanser.runtime --data_local_config '{"input_folder": "test-data/input", "output_folder": "output/python/license-and-copyright-local"}' \
			--header_cleanser_contents_column_name contents \
			--header_cleanser_license True \
			--header_cleanser_copyright True
#
	source venv/bin/activate \
	&& python -m dpk_header_cleanser.runtime --data_local_config '{"input_folder": "test-data/input", "output_folder": "output/python/license-local"}' \
			--header_cleanser_contents_column_name contents \
			--header_cleanser_license True \
			--header_cleanser_copyright False
#
	source venv/bin/activate \
	&& python -m dpk_header_cleanser.runtime --data_local_config '{"input_folder": "test-data/input", "output_folder": "output/python/copyright-local"}' \
			--header_cleanser_contents_column_name contents \
			--header_cleanser_license False \
			--header_cleanser_copyright True

	source venv/bin/activate \
	&& python -m dpk_header_cleanser.ray.runtime --data_local_config '{"input_folder": "test-data/input", "output_folder": "output/ray/license-and-copyright-local"}' \
			--header_cleanser_contents_column_name contents \
			--header_cleanser_license True \
			--header_cleanser_copyright True \
			--run_locally True
#
	source venv/bin/activate \
	&& python -m dpk_header_cleanser.ray.runtime --data_local_config '{"input_folder": "test-data/input", "output_folder": "output/ray/license-local"}' \
			--header_cleanser_contents_column_name contents \
			--header_cleanser_license True \
			--header_cleanser_copyright False \
			--run_locally True
#
	source venv/bin/activate \
	&& python -m dpk_header_cleanser.ray.runtime --data_local_config '{"input_folder": "test-data/input", "output_folder": "output/ray/copyright-local"}' \
			--header_cleanser_contents_column_name contents \
			--header_cleanser_license False \
			--header_cleanser_copyright True \
			--run_locally True
