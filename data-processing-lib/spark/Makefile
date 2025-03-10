# Use make help, to see the available rules
REPOROOT=../..
include $(REPOROOT)/.make.defaults
DOCKER_IMAGE_NAME=$(DOCKER_SPARK_BASE_IMAGE_NAME)


.check-env::
	@echo "Checks passed"

setup::

set-versions: .check-env
	$(MAKE) TOML_VERSION=$(DPK_LIB_VERSION) .defaults.update-toml
	if [ -e pyproject.toml ]; then					\
		cat pyproject.toml | sed -e 's/"spark[default]==.*",/"spark[default]==$(SPARK_VERSION)",/' > tt.toml; \
		mv tt.toml pyproject.toml; \
	fi
	if [ -e requirements.txt ]; then					\
		cat requirements.txt | sed -e 's/ray[default]==.*/ray[default]==$(SPARK_VERSION)/' > tt.txt; \
		mv tt.txt requirements.txt; \
	fi

build:: build-dist 

#build:: update-toml .defaults.build-dist 
build-dist :: .defaults.build-dist 

publish:: publish-dist 

publish-dist :: .check-env .defaults.publish-dist 

publish-image:: .defaults.publish-image

venv::
	$(MAKE) .defaults.spark-lib-src-venv
	pip install pytest pytest-cov 

image:: image-spark

image-spark:: Dockerfile
	@# Help: Build the bare Spark image 
	$(MAKE) .defaults.image

docker-save-image: .defaults.docker-save-image

docker-load-image: .defaults.docker-load-image

clean:: .defaults.clean
	@# Help: Clean up the distribution build and the venv
	-rm -rf dist > /dev/null 2>&1

test::  venv
	@# Help: Use the already-built virtual environment to run pytest on the test directory. 
	source venv/bin/activate; export PYTHONPATH=../src; cd test; $(PYTEST)  data_processing_spark_tests/launch/spark/spark_launcher_test.py;
	source venv/bin/activate; export PYTHONPATH=../src; cd test; $(PYTEST)  data_processing_spark_tests/launch/spark/test_noop_launch.py;
