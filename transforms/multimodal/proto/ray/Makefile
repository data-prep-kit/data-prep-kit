# Define the root of the local git clone for the common rules to be able 
# know where they are running from.
REPOROOT=../../../..
# Include a library of common .transform.* targets which most
# transforms should be able to reuse.  However, feel free
# to override/redefine the rules below. 
include $(REPOROOT)/transforms/.make.transforms

TRANSFORM_RUNTIME_SRC_FILE=faces_transform_ray.py
TRANSFORM_NAME=multimodal
BASE_IMAGE=${RAY_BASE_IMAGE}
DOCKER_IMAGE_VERSION=39

# for iocr
EXTRA_INDEX_IOCR_URL=https://${ARTIFACTORY_USER}:${ARTIFACTORY_API_KEY}@na.artifactory.swg-devops.com/artifactory/api/pypi/wcp-ai-foundation-team-pypi-local/simple
# for docling-ibm
EXTRA_INDEX_DOCLING_URL=https://${ARTIFACTORY_USER}:${ARTIFACTORY_API_KEY}@eu.artifactory.swg-devops.com/artifactory/api/pypi/res-zurich-ski-team-inner-source-pypi-local/simple

# Instead of DOCKER_BUILD_EXTRA_ARGS, which in the inner needs a ?= instead of =, as is now in the outer. 
PIP_INSTALL_EXTRA_ARGS=--extra-index-url=${EXTRA_INDEX_DOCLING_URL} --extra-index-url=${EXTRA_INDEX_IOCR_URL}

# cpu-only torch
OS := $(shell uname -s)
ifeq ($(OS),Linux)
PIP_INSTALL_EXTRA_ARGS=--extra-index-url=https://download.pytorch.org/whl/cpu ${PIP_INSTALL_EXTRA_ARGS}
endif

# propagate extras to docker
DOCKER_BUILD_EXTRA_ARGS=--build-arg "PIP_INSTALL_EXTRA_ARGS=${PIP_INSTALL_EXTRA_ARGS}"


cp-python:
	(cd ../python; $(MAKE) check_models)
	cp -R ../python/models .
	cp -R ../python/test-data .
	
venv::  .transforms.ray-venv

test::  .transforms.ray-test

clean:: .transforms.clean

image:: cp-python .transforms.ray-image

test-src:: cp-python .transforms.test-src

setup:: .transforms.setup

test-image:: cp-python .transforms.ray-test-image

build:: build-dist image

publish: publish-image

publish-image:: 
	@# Help: Publish the Ray image to us.icr.io/cil15-shared-registry/preprocessing-pipelines/multimodal-ray:$(DOCKER_IMAGE_VERSION)
	@echo ""
	@echo NOTE: Please be sure IBM_CLOUD_USER and IBM_CLOUD_APIKEY env vars are set to access us.icr.io container registry
	@echo You may also need to run this with '"'make DOCKER=podman ...'"' if using podman
	@echo ""
	ibmcloud login -u $(IBM_CLOUD_USER) -apikey $(IBM_CLOUD_APIKEY) 
	ibmcloud cr region-set us-south
	ibmcloud target -g fmc-preprocessing
	ibmcloud cr login --client $(DOCKER) 
	$(DOCKER) push us.icr.io/cil15-shared-registry/preprocessing-pipelines/multimodal-ray:$(DOCKER_IMAGE_VERSION)
	# $(MAKE) DPK_DOCKER_REGISTRY_USER=$(IBM_CLOUD_USER) DPK_DOCKER_REGISTRY_KEY=$(IBM_CLOUD_APIKEY) .transforms.publish-image-ray



test-run-people:
	docker run --rm  -v $$(pwd)/test-data/j2p/expected:/input -v $$(pwd)/output:/output $(TRANSFORM_NAME)-ray:$(DOCKER_IMAGE_VERSION) \
		python people_transform_ray.py --run_locally True --people_mode blur --people_model_path models/yolov8m_200e.pt \
		--data_local_config '{ "input_folder": "/input", "output_folder": "/output"  }'

