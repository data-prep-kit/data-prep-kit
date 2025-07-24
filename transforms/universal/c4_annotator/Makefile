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


run-python-cli-sample:
	make venv
	source venv/bin/activate && \
	rm -rf output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
	--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}" \

run-ray-cli-with-all-params:
	make venv
	source venv/bin/activate && \
	rm -rf output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
	--data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}" \
	--c4a_contents_column_name "text" \
	--c4a_clean_contents_column_name "c4_cleaned_content" \
	--c4a_drop_reason_column_name "c4_drop_reason" \
	--c4a_doc_stats_column_name "c4_doc_stats" \
	--c4a_tokenizer_language "en" \
	--c4a_split_paragraph True \
	--c4a_remove_citations True \
	--c4a_filter_no_terminal_punct True \
	--c4a_min_num_sentences 5 \
	--c4a_min_words_per_line 3 \
	--c4a_max_word_length 1000 \
	--c4a_filter_lorem_ipsum True \
	--c4a_filter_javascript True \
	--c4a_filter_curly_bracket True \
	--c4a_filter_policy True \
	--c4a_min_paragraphs 3 \
	--c4a_min_paragraph_len 200 \
	--c4a_paragraph_delimiter "\n" \
	--c4a_ldnoobw_url "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/25e679f03d96baa721cde20db9944649e8d0a844/en" \
	--c4a_filter_badwords True \
	--c4a_badwords_keep_fraction 0.1 \
	--c4a_badwords_seed 43
