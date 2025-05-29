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



run-ray-cli-sample:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.runtime \
		--data_local_config "{ 'input_folder' : 'test-data/input2', 'output_folder' : 'output'}"  \
        --cq_contents_column_name contents \
        --cq_language_column_name language \
        --cq_tokenizer 'codeparrot/codeparrot' \
        --cq_calculate_complexity True \
        --cq_has_ast True \
        --cq_sqlglot True \
        --run_locally True


CRD:
	#git clone https://gitlab.cern.ch/paas-tools/CRDs-catalog.git dpk_code_quality/schemas/CRD/CRDS-catalog-main
	git clone https://github.com/datreeio/CRDs-catalog.git dpk_code_quality/schemas/CRD/CRDS-catalog-main