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




run-spark-cli-sample: 
	$(MAKE) venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).spark.transform \
		--spark_local_config_filepath ../config/spark_profile_local.yml \
		--data_local_config "{ 'input_folder' : '../test-data/input', 'output_folder' : '../output'}"  \
		--filter_criteria_list "[ 'docq_total_words > 100 AND docq_total_words < 200', 'ibmkenlm_docq_perplex_score < 230']"  \
		--filter_columns_to_drop "[ 'extra', 'cluster' ]"
