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

# models
MODELS_URL=https://ibm.box.com/s/q6z20vjawbwqg29jd9l0q7gp8ou9jxgi
DOCLING_INNER_MODELS_URL=https://ibm.ent.box.com/s/a6m85dtjp3tztqrp808q6dgizhoqupf6


# The needed (large) models are stored in box

check_models: models/yolov8m_200e.pt models/yolov8m-seg.pt models/docling/model_artifacts/figure_classifier/clip_config.json models/ocr_iocr

models/yolov8m_200e.pt:
	@echo Please download $$(basename $@) from $(MODELS_URL) into $@
	curl --output models/yolov8m_200e.pt https://ibm.box.com/s/krx5nj4h3qczqgazkve0zhqwyrqrfx3n
	#@exit 1

models/yolov8m-seg.pt:
	@echo Please download $$(basename $@) from $(MODELS_URL) into $@
	curl --output models/yolov8m-seg.pt https://ibm.box.com/s/wwafzqoms8um08c5bltx3b8h5xyozszb
	#@exit 1

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


venv:: check_models 
	source venv/bin/activate && pip install $(PIP_INSTALL_EXTRA_ARGS) -r requirements-private.txt


test-mm-src:: venv
	@# Help: Run pytest on the test directory inside the venv 
	source venv/bin/activate;       \
	export PYTHONPATH=. ;  \
	$(PYTEST) test/bad_image ;  \
	$(PYTEST) test/faces_test ; \
	$(PYTEST) test/nsfw_test ; \
	$(PYTEST) test/p2j_test ; \
	$(PYTEST) test/people_test









