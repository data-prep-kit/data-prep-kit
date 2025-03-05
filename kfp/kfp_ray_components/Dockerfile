ARG BASE_IMAGE=docker.io/rayproject/ray:2.36.1-py312

FROM ${BASE_IMAGE}

# see https://docs.openshift.com/container-platform/4.17/openshift_images/create-images.html#use-uid_create-images
USER root
RUN chown ray:root /home/ray && chmod g=u /home/ray
USER ray

# install libraries
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r  requirements.txt

ARG DPK_WHEEL_FILE_NAME

# Copy and install data processing libraries 
# These are expected to be placed in the docker context before this is run (see the make image).
COPY --chmod=775 --chown=ray:root data-processing-dist data-processing-dist
RUN  pip install data-processing-dist/${DPK_WHEEL_FILE_NAME}[ray]

COPY --chmod=775 --chown=ray:root shared_workflow_support_lib shared_workflow_support_lib/
RUN cd shared_workflow_support_lib && pip install --no-cache-dir -e .

COPY --chmod=775 --chown=ray:root workflow_support_lib workflow_support_lib/
RUN cd workflow_support_lib && pip install --no-cache-dir -e .

# overwriting the installation of old versions of pydantic
RUN pip install --no-cache-dir pydantic==2.6.3

# remove credentials-containing file
RUN rm requirements.txt
# components
COPY --chmod=775 --chown=ray:root ./src /pipelines/component/src

# Set environment
ENV KFP_v2=$KFP_v2

# Put these at the end since they seem to upset the docker cache.
ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT
