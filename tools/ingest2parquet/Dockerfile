ARG BASE_IMAGE=docker.io/rayproject/ray:2.24.0-py310

FROM ${BASE_IMAGE}

# see https://docs.openshift.com/container-platform/4.17/openshift_images/create-images.html#use-uid_create-images
USER root
RUN chown ray:root /home/ray && chmod g=u /home/ray
USER ray

# install pytest
RUN pip install --no-cache-dir pytest
ARG DPK_WHEEL_FILE_NAME

# Copy and install data processing libraries 
# These are expected to be placed in the docker context before this is run (see the make image).
COPY --chmod=775 --chown=ray:root data-processing-dist data-processing-dist
RUN  pip install data-processing-dist/${DPK_WHEEL_FILE_NAME}[ray]

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r  requirements.txt

RUN rm requirements.txt
# copy source
COPY --chmod=775 --chown=ray:root ./src .
# copy test
COPY --chmod=775 --chown=ray:root test/ test/
COPY --chmod=775 --chown=ray:root test-data/ test-data/
# Set environment
ENV PYTHONPATH /home/ray
