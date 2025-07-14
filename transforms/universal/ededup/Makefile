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

run-cli-python:
	make venv
	source venv/bin/activate && \
	python -m dpk_$(TRANSFORM_NAME).transform_python \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/expected'}"  \
				--ededup_doc_column "contents" \
            	--ededup_doc_id "document_id"

	source venv/bin/activate && \
	python -m dpk_$(TRANSFORM_NAME).transform_python \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/incremental'}"  \
				--ededup_doc_column "contents" \
            	--ededup_doc_id "document_id" \
				--ededup_use_snapshot "True" \
				--ededup_snapshot_directory test-data/input/snapshot


run-cli-ray:
	make venv
	source venv/bin/activate && \
	python -m dpk_$(TRANSFORM_NAME).ray.transform \
				--run_locally True \
				--ededup_num_hashes 2 \
                --data_local_config "{ 'input_folder' : 'test-data-ray/input', 'output_folder' : 'test-data-ray/expected'}"  \
				--ededup_doc_column "contents" \
            	--ededup_doc_id "document_id"

	source venv/bin/activate && \
	python -m dpk_$(TRANSFORM_NAME).ray.transform \
				--run_locally True \
				--ededup_num_hashes 2 \
                --data_local_config "{ 'input_folder' : 'test-data-ray/input', 'output_folder' : 'test-data-ray/incremental'}"  \
				--ededup_doc_column "contents" \
            	--ededup_doc_id "document_id" \
				--ededup_use_snapshot "True" \
				--ededup_snapshot_directory test-data-ray/input/snapshot
