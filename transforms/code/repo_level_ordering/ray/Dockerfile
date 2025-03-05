ARG BASE_IMAGE=docker.io/rayproject/ray:2.24.0-py310

FROM ${BASE_IMAGE}

# see https://docs.openshift.com/container-platform/4.17/openshift_images/create-images.html#use-uid_create-images
USER root
RUN chown ray:root /home/ray && chmod g=u /home/ray
USER ray

RUN pip install --upgrade --no-cache-dir pip 

# install pytest
RUN pip install --no-cache-dir pytest
ARG DPK_WHEEL_FILE_NAME

# Copy and install data processing libraries 
# These are expected to be placed in the docker context before this is run (see the make image).
COPY --chmod=775 --chown=ray:root data-processing-dist data-processing-dist
RUN  pip install data-processing-dist/${DPK_WHEEL_FILE_NAME}[ray]

COPY --chmod=775 --chown=ray:root src/ src/
COPY --chmod=775 --chown=ray:root pyproject.toml pyproject.toml 
COPY --chmod=775 --chown=ray:root README.md README.md 
RUN pip install --no-cache-dir -e .

# copy source data
COPY --chmod=775 --chown=ray:root ./src/repo_level_order_transform_ray.py .
COPY --chmod=775 --chown=ray:root ./src/repo_level_order_local_ray.py local/
COPY --chmod=775 --chown=ray:root ./src/repo_level_order_s3_ray.py local/

# copy test
COPY --chmod=775 --chown=ray:root test/ test/
COPY --chmod=775 --chown=ray:root test-data/ test-data/

# Set environment
ENV PYTHONPATH /home/ray:/home/ray/src

# Put these at the end since they seem to upset the docker cache.
ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT
