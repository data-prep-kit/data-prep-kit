REPOROOT=${CURDIR}/../../../../
WORKFLOW_VENV_ACTIVATE=${REPOROOT}/transforms/venv/bin/activate
include $(REPOROOT)/transforms/.make.workflows


# Include the common configuration for this transform
#include ../transform.config

SRC_DIR=${CURDIR}/../
# Use the docker image that is built for ray runtime
TRANSFORM_RUNTIME=ray
## override settings in .make.default as they assume old structure with ray being the current folder
DOCKER_IMAGE_NAME=$(TRANSFORM_NAME)-$(TRANSFORM_RUNTIME)
DOCKER_LOCAL_IMAGE=$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_VERSION)


# Only build the image with -f Dockerfile.ray
BUILD_SPECIFIC_RUNTIME=ray

PYTHON_WF := $(shell find ./ -name '*_wf.py')
YAML_WF := $(patsubst %.py, %.yaml, ${PYTHON_WF})

workflow-venv: .check_python_version ${WORKFLOW_VENV_ACTIVATE}

.PHONY: clean
clean:
	@# Help: Clean up the virtual environment.
	rm -rf ${REPOROOT}/transforms/venv


.PHONY: workflow-build
workflow-build: workflow-venv
	$(MAKE) $(YAML_WF)

.PHONY: workflow-test
workflow-test: workflow-build
	$(MAKE) TRANSFORM_SRC=${SRC_DIR} \
		TRANSFORM_RUNTIME=$(TRANSFORM_RUNTIME) \
		TRANSFORM_NAME=$(TRANSFORM_NAME) \
		BUILD_SPECIFIC_RUNTIME=$(BUILD_SPECIFIC_RUNTIME) \
		PIPELINE_FILE=$(TRANSFORM_NAME)_wf.yaml .workflows.test-pipeline

.PHONY: workflow-upload
workflow-upload:
	@for file in $(YAML_WF); do \
		$(MAKE) .workflows.upload-pipeline PIPELINE_FILE=$$file; \
	done
