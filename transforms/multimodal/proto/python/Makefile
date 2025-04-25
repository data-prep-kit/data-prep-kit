# Define the root of the local git clone for the common rules to be able 
# know where they are running from.
REPOROOT=../../../..
# Include a library of common .transform.* targets which most
# transforms should be able to reuse.  However, feel free
# to override/redefine the rules below. 
include $(REPOROOT)/transforms/.make.transforms

TRANSFORM_RUNTIME_SRC_FILE=faces_transform_python.py
TRANSFORM_NAME=multimodal

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

# models
MODELS_URL=https://ibm.box.com/s/q6z20vjawbwqg29jd9l0q7gp8ou9jxgi
DOCLING_INNER_MODELS_URL=https://ibm.ent.box.com/s/a6m85dtjp3tztqrp808q6dgizhoqupf6

venv::  .transforms.python-venv

# The needed (large) models are stored in box

check_models: models/yolov8m_200e.pt models/yolov8m-seg.pt models/docling/model_artifacts/figure_classifier/clip_config.json models/ocr_iocr

models/yolov8m_200e.pt:
	@echo Please download $$(basename $@) from $(MODELS_URL) into $@
	@exit 1

models/yolov8m-seg.pt:
	@echo Please download $$(basename $@) from $(MODELS_URL) into $@
	@exit 1

models/docling/model_artifacts/figure_classifier/clip_config.json:
	@echo Please download $$(basename $@) from $(DOCLING_INNER_MODELS_URL) into $@
	@exit 1

models/ocr_iocr:
	@echo "Downloading iocr model weights..."
	$(call check_defined, ARTIFACTORY_USER)
	$(call check_defined, ARTIFACTORY_API_KEY)
	curl --fail -u ${ARTIFACTORY_USER}:${ARTIFACTORY_API_KEY} -o models/ocr_iocr_v0-1-1_2024-05-08_13_21_02-989049-light.zip https://na.artifactory.swg-devops.com/artifactory/wcp-ai-foundation-team-watson-du-generic-local/models/ocr_iocr/ocr_iocr_v0-1-1_2024-05-08_13_21_02-989049-light.zip
	@echo "Unzipping model weights..."
	mkdir models/ocr_iocr
	unzip models/ocr_iocr_v0-1-1_2024-05-08_13_21_02-989049-light.zip -d models/ocr_iocr
	@echo "Cleaning up..."
	rm models/ocr_iocr_v0-1-1_2024-05-08_13_21_02-989049-light.zip
	@echo "Download and extraction complete."

venv::  check_models .transforms.python-venv 

test::  check_models .transforms.python-test

clean:: .transforms.clean

image:: check_models .transforms.python-image

test-src:: check_models .transforms.test-src

setup:: check_models .transforms.setup

test-image:: .transforms.python-test-image

build:: build-dist image

publish: publish-image

publish-image:: .transforms.publish-image-python
