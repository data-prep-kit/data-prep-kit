REPOROOT=../..
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
TRANSFORM_PYTHON_SRC="-m dpk_mm.$(TRANSFORM_NAME).transform_python"
TRANSFORM_RAY_SRC="-m dpk_mm.ray.$(TRANSFORM_NAME).transform"





# for iocr
EXTRA_INDEX_IOCR_URL=https://${ARTIFACTORY_USER}:${ARTIFACTORY_API_KEY}@na.artifactory.swg-devops.com/artifactory/api/pypi/wcp-ai-foundation-team-pypi-local/simple
# for docling-ibm
EXTRA_INDEX_DOCLING_URL=https://${ARTIFACTORY_USER}:${ARTIFACTORY_API_KEY}@eu.artifactory.swg-devops.com/artifactory/api/pypi/res-zurich-ski-team-inner-source-pypi-local/simple

PIP_INSTALL_EXTRA_ARGS=--extra-index-url=${EXTRA_INDEX_DOCLING_URL} --extra-index-url=${EXTRA_INDEX_IOCR_URL}

# cpu-only torch
OS := $(shell uname -s)
ifeq ($(OS),Linux)
PIP_INSTALL_EXTRA_ARGS=--extra-index-url=https://download.pytorch.org/whl/cpu ${PIP_INSTALL_EXTRA_ARGS}
endif

# propagate extras to docker
DOCKER_BUILD_EXTRA_ARGS=--build-arg "PIP_INSTALL_EXTRA_ARGS=${PIP_INSTALL_EXTRA_ARGS}"

# large files are stored in seperate git repo or can be obtained from HF
models: models/yolov8m_200e.pt models/yolov8m-seg.pt models/yolov8n-face.pt

models/yolov8n-face.pt:
	@echo Downloading $@
	mkdir -p models
	curl -L --output models/yolov8n-face.pt https://github.com/touma-I/large-files/raw/refs/heads/main/models/yolov8n-face.pt

models/yolov8m_200e.pt:
	@echo Downloading $@
	mkdir -p models
	curl -L --output models/yolov8m_200e.pt https://github.com/touma-I/large-files/raw/refs/heads/main/models/yolov8m_200e.pt

models/yolov8m-seg.pt:
	@echo Downloading $@
	mkdir -p models
	curl -L --output models/yolov8m-seg.pt https://github.com/touma-I/large-files/raw/refs/heads/main/models/yolov8m-seg.pt


venv:: models


test-mm-src: venv
	@# Help: Run pytest on the test directory inside the venv 
	source venv/bin/activate;       \
	export PYTHONPATH=. ;  \
	$(PYTEST) test/faces_test ; \
	$(PYTEST) test/nsfw_test ; \
	$(PYTEST) test/people_test












