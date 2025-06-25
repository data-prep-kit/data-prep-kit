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
	--gra_contents_column_name="contents" --gra_dup_10_grams_cname="top_10_grams" --gra_dup_5_grams_cname="top_5_grams" \
	--gra_dup_6_grams_cname="top_6_grams" --gra_dup_7_grams_cname="top_7_grams" --gra_dup_8_grams_cname="top_8_grams" --gra_dup_9_grams_cname="top_9_grams" \
	--gra_dup_line_char_frac_cname="dup_line_char_frac" --gra_dup_line_frac_cname="dup_line_frac" --gra_dup_para_char_frac_cname="dup_para_char_frac" \
	--gra_dup_para_frac_cname="dup_para_frac" --gra_top_2_grams_cname="top_2_grams" --gra_top_3_grams_cname="top_3_grams" \
	--gra_top_4_grams_cname="top_4_grams"