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



run-cli-python-sample: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
            	--doc_id_hash hash_column \
				--doc_id_int int_id_column



run-cli-python-s3: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
                --data_s3_config "{ 'input_folder' : 'cloud-object-storage-cos-standard-k1l/doc-id-test-data/input', 'output_folder' : 'cloud-object-storage-cos-standard-k1l/doc-id-output'}"  \
                --doc_id_int int_id

run-cli-spark-sample: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).spark.runtime \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
                --doc_id_int int_id

run-cli-ray-sample: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.runtime \
                --run_locally True --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
                --doc_id_int int_id

run-cli-ray-depricated: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.transform \
                --run_locally True --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
                --doc_id_int int_id

## Used for local testing of the image on MacOS
run-docker-python-sample:
	make DOCKER_PLATFORM=linux/arm64 image-python
	mkdir -p ./output
	$(DOCKER) run -v ./test-data:/test-data -v ./output:/output -it localhost/doc_id-python \
                python -m dpk_$(TRANSFORM_NAME).runtime \
                --data_local_config "{ 'input_folder' : '/test-data/input', 'output_folder' : '/output'}"  \
                --doc_id_int int_id

run-cli-python-jsonl: 
	make venv
	source venv/bin/activate && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
                --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'output'}"  \
                --doc_id_hash_column uuid \
				--doc_id_doc_column messages \
				--data_files_to_use "['.jsonl']"

test-notebooks:
	make venv
	source venv/bin/activate && pip install jupyterlab nbconvert python-dotenv
	@for x in $(TRANSFORM_NAME).ipynb $(TRANSFORM_NAME)-ray.ipynb; do \
		source venv/bin/activate && jupyter nbconvert --execute $$x --to notebook --output=output_notebook.ipynb; \
		rm -f output_notebook.ipynb; \
	done




