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



run-cli-sample:
	make venv
	source venv/bin/activate && \
	DPK_DPK_DOC_CLEANER_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
            --data_local_config "{ 'input_folder' : 'enwiki', 'output_folder' : 'output'}"  \
            --cdc_contents_column_name original_content \
            --cdc_clean_text_column_name content_resi


run-zip-test:
	make venv
	source venv/bin/activate && \
	DPK_DPK_DOC_CLEANER_TRANSFORM_LOG_LEVEL=DEBUG $(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
            --data_local_config "{ 'input_folder' : 'input-zip', 'output_folder' : 'output'}"  \
			--data_files_to_use "['.zip']"

run-ray-image:
	#docker run -it --env-file .env -e DPK_LOG_LEVEL=DEBUG dom2parquet-ray:latest python -m dpk_$(TRANSFORM_NAME).ray.runtime \
	docker run -d --env-file .env dom2parquet-ray:latest python -m dpk_$(TRANSFORM_NAME).ray.runtime \
            --data_s3_config="{ 'input_folder' : '${DOM_INPUT_FOLDER}', 'output_folder' : '${DOM_OUTPUT_FOLDER}' }"  \
            --run_locally=True --runtime_num_workers="10"  \
	     --data_max_files=-1 \
	    --data_files_to_use="['.zip']"
            #--run_locally=True --runtime_num_workers="10" --runtime_worker_options="{'num_cpus': 1.0}" \

