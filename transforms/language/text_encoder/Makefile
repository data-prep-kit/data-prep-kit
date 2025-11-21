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





LINUX_WITH_CPU_TORCH?=true
OS := $(shell uname -s)
ifeq ($(OS),Linux)
	ifeq ($(LINUX_WITH_CPU_TORCH),true)
	PIP_INSTALL_EXTRA_ARGS=--extra-index-url=https://download.pytorch.org/whl/cpu
	DOCKER_BUILD_EXTRA_ARGS=--build-arg PIP_INSTALL_EXTRA_ARGS=${PIP_INSTALL_EXTRA_ARGS}
	endif
endif

run-python-cli-sample-parquet:
	make venv
	source venv/bin/activate && \
	rm -fr output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
			--data_local_config "{ 'input_folder' : 'test-data/input/', 'output_folder' : 'output/'}" \
			--text_encoder_embeddings_in_parquet True \
			--text_encoder_embedding_batch_size 5 \


run-python-cli-sample-lancedb:
	make venv
	source venv/bin/activate && \
	rm -rf output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).runtime \
			--data_local_config "{ 'input_folder' : 'test-data/input/', 'output_folder' : 'output/'}" \
			--text_encoder_lanceDB_data_uri "output/test.db/test.lance/"  \
			--text_encoder_lanceDB_batch_size 10 \
			--text_encoder_embedding_batch_size 5 \
			--text_encoder_lanceDB_fragments_json_folder "output/fragments_json/" \
			--text_encoder_lanceDB_table_name "test" && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).lance_commit \
			--lanceDB_storage_type "local" \
			--lanceDB_uri "output/test.db/" \
			--lanceDB_data_uri "output/test.db/test.lance/" \
			--lanceDB_table_name "test" \
			--lanceDB_fragments_json_folder "output/fragments_json/" \
			--lanceDB_table_schema_folder "output/"

run-ray-cli-sample-parquet:
	make venv
	source venv/bin/activate && \
	rm -fr output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.runtime \
			--data_local_config "{ 'input_folder' : 'test-data/input/', 'output_folder' : 'output/'}" \
			--text_encoder_embeddings_in_parquet True \
			--text_encoder_embedding_batch_size 5 \
			--run_locally True

run-ray-cli-sample-lancedb:
	make venv
	source venv/bin/activate && \
	rm -rf output && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).ray.runtime \
            --data_local_config "{ 'input_folder' : 'test-data/input/', 'output_folder' : 'output/'}" \
			--text_encoder_lanceDB_data_uri "output/test.db/test.lance/"  \
			--text_encoder_lanceDB_batch_size 10 \
			--text_encoder_lanceDB_fragments_json_folder "output/fragments_json/" \
			--text_encoder_embedding_batch_size 5 \
			--text_encoder_lanceDB_table_name "test" \
			--run_locally True && \
	$(PYTHON) -m dpk_$(TRANSFORM_NAME).lance_commit \
			--lanceDB_storage_type "local" \
			--lanceDB_uri "output/test.db/" \
			--lanceDB_data_uri "output/test.db/test.lance/" \
			--lanceDB_table_name "test" \
			--lanceDB_fragments_json_folder "output/fragments_json/" \
			--lanceDB_table_schema_folder "output/"

