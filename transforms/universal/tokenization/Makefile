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
TRANSFORM_NAME?=$(shell basename `pwd`)

################################################################################

TRANSFORM_PYTHON_SRC="-m dpk_$(TRANSFORM_NAME).runtime"
TRANSFORM_RAY_SRC="-m dpk_$(TRANSFORM_NAME).ray.runtime"


run-cli-sample: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
            --data_local_config "{ 'input_folder' : 'test-data/ds01/input', 'output_folder' : 'output'}"

run-list-sample: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
			--tkn_doc_content_column  curr_file_contents \
			--tkn_doc_id_column pulls_and_issues_id \
            --data_local_config "{ 'input_folder' : 'test-data/list/input', 'output_folder' : 'output'}"


############

run-tkn2arrow-python:
	make venv
	source venv/bin/activate && \
	rm -rf output/ds02 && \
	$(PYTHON) -m dpk_tokenization2arrow.runtime \
            --data_local_config "{ 'input_folder' : 'test-data/ds02/input', 'output_folder' : 'output/ds02'}"

run-tkn2arrow-ray:
	make venv
	source venv/bin/activate && \
	rm -rf output/ds02 && \
	$(PYTHON) -m dpk_tokenization2arrow.ray.runtime \
            --data_local_config "{ 'input_folder' : 'test-data/ds01/input', 'output_folder' : 'output/ds01'}" \
			--run_locally True

run-tkn2arrow-list:
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_tokenization2arrow.runtime \
			--tkn_doc_content_column  curr_file_contents \
			--tkn_doc_id_column pulls_and_issues_id \
            --data_local_config "{ 'input_folder' : 'test-data/list/input', 'output_folder' : 'output'}"




## Deploying rayjob to ocp cluster assumes that 
### the user is logged in to the cluster (oc login ... )
### the context is set for the right project/namespace (oc project ...)
### the namespace includes s3-secret and hf-secret
### a .env file exists in the current folders with all the environment variables referenced in the job yaml file
## Include .env file if any to be exported for use by envsubst
-include .env

run-ray-job:
ifneq ($(strip $(wildcard .env)),)
	$(eval export $(shell sed -ne 's/ *#.*$$//; /./ s/=.*$$// p' .env))
endif
	envsubst < tokenization2arrow-rayjob.yaml | kubectl apply -f -
	
kill-ray-job:
	export
	envsubst < tokenization2arrow-rayjob.yaml | kubectl delete -f -
