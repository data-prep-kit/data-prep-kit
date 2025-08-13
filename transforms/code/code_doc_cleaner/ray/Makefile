# Define the root of the local git clone for the common rules to be able 
# know where they are running from.
REPOROOT=../../../..
# Include a library of common .transform.* targets which most
# transforms should be able to reuse.  However, feel free
# to override/redefine the rules below. 
include $(REPOROOT)/transforms/.make.transforms

TRANSFORM_RUNTIME_SRC_FILE=code_doc_cleaner_transform_ray_ibm.py
TRANSFORM_NAME=code-doc-cleaner
# $(REPOROOT)/.make.versions file contains the versions
DOCKER_IMAGE_VERSION=${CODE_DOC_CLEANER_VERSION}
DOCKER_NAMESPACE=cil15-shared-registry/preprocessing-pipelines/modules

venv::  .transforms.ray-venv

# We rely on the outer source to do the source level testing and don't have the test files here.
#test::  .transforms.ray-test
test::  .transforms.ray-test-image

clean:: .transforms.clean

image:: .transforms.ray-image

# We rely on the outer source to do the source level testing and don't have the test files here.
test-src:: #.transforms.test-src
	@# Help: Source level testing not enabled.

setup:: .transforms.setup

test-image:: .transforms.ray-test-image

build:: build-dist image

publish: publish-image

publish-image:: .transforms.publish-image-ray
