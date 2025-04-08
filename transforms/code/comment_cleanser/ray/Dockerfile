FROM docker.io/rayproject/ray:2.24.0-py310

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

COPY --chmod=775 --chown=ray:root python-transform/ python-transform 
RUN cd python-transform && pip install --no-cache-dir -e .

COPY --chmod=775 --chown=ray:root src/ src/
COPY --chmod=775 --chown=ray:root pyproject.toml pyproject.toml 
RUN pip install --no-cache-dir -e .
    
# copy source data
COPY --chmod=775 --chown=ray:root ./src/comment_cleanser_transform_ray.py .
COPY --chmod=775 --chown=ray:root src/comment_cleanser_local_ray.py local/

# copy test
COPY --chmod=775 --chown=ray:root test/ test/
COPY --chmod=775 --chown=ray:root test-data/ test-data/

# Copy the joblib model into a specific directory inside the image
COPY --chmod=775 --chown=ray:root ./model/ model/

# Set environment
ENV PYTHONPATH /home/ray

# Put these at the end since they seem to upset the docker cache.
ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT
