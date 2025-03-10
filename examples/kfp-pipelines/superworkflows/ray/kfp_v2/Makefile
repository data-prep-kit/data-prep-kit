REPOROOT=${CURDIR}/../../../../..
WORKFLOW_VENV_ACTIVATE=${REPOROOT}/transforms/venv/bin/activate
include $(REPOROOT)/transforms/.make.workflows

PYTHON_WF := $(shell find ./ -name "*_wf.py")
YAML_WF=$(patsubst %.py, %.yaml, ${PYTHON_WF})

# find all kfp_ray subdirs that have a src directory
KFP_SRC_DIRS := $(shell find ${REPOROOT}/transforms/ -type d -path '*/kfp_ray/src' | sed 's/src//' | tr '\n' ':' )

workflow-venv:: .check_python_version ${WORKFLOW_VENV_ACTIVATE}

worflow-clean:: .workflows.clean

.PHONY: workflow-build
workflow-build: workflow-venv
	@for file in $(YAML_WF); do \
		$(MAKE) KFP_COMPONENT_SPEC_PATH=${REPOROOT}/kfp/kfp_ray_components/ PYTHONPATH=${PYTHONPATH}:${REPOROOT}/transforms:${KFP_SRC_DIRS} $$file;       \
	done

workflow-test::

.PHONY: workflow-upload
workflow-upload: workflow-build
	@for file in $(YAML_WF); do \
                $(MAKE) .workflows.upload-pipeline PIPELINE_FILE=$$file; \
        done

.PHONY: clean
clean:
	rm -rf *.back || true
	rm -rf $(REPOROOT)/transforms/venv
