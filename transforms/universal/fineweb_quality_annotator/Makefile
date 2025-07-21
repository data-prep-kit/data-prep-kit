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


run-python-cli-sample:
	make venv
	source venv/bin/activate && \
	rm -rf output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
		--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"

run-ray-cli-with-all-params:
	make venv
	source venv/bin/activate && \
	rm -rf output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.runtime \
	--run_locally=True \
	--data_checkpointing=False --data_files_to_use="['.parquet']" --data_max_files=2 --data_num_samples=-1 \
	--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}" \
	--fineweb_quality_contents_column_name "text" \
	--fineweb_quality_frac_line_punct_cname "FWQA_frac_line_punct" \
	--fineweb_quality_dup_line_char_frac_cname "FWQA_dup_line_char_frac" \
	--fineweb_quality_new_line_ratio_cname "FWQA_new_line_ratio" \
	--fineweb_quality_short_line_frac_cname "FWQA_short_line_frac" \
	--fineweb_quality_short_line_length 35
