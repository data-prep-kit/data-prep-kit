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

# Regenerate test-data/expected by running the transform with output pointed at the
# expected directory. Mirrors the config used by test/test_html2parquet_python.py
# (markdown output, .html and .zip inputs).
generate-expected:
	$(MAKE) venv
	@source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).transform_python \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected'}" \
                --data_files_to_use "['.html','.zip']" \
                --html2parquet_output_format "markdown"

