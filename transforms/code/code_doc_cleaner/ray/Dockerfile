FROM docker.io/rayproject/ray:2.24.0-py310

ARG EXTRA_INDEX_URL

COPY requirements.txt requirements.txt
RUN pip uninstall data-prep-toolkit data-prep-toolkit-ray -y
RUN pip install --no-cache-dir --extra-index-url $EXTRA_INDEX_URL -r requirements.txt

RUN mkdir dmf_datasets
RUN chmod a+r+w+x -R dmf_datasets/
RUN mkdir dmf_models
RUN chmod a+r+w+x -R dmf_models/
RUN mkdir dmf_tokenizers
RUN chmod a+r+w+x -R dmf_tokenizers/

# copy source data
COPY src/*.py /home/ray/

# Install pytest so we can test the image later
RUN pip install --no-cache-dir pytest
COPY test/ test/
COPY test-data/ test-data/

USER root
RUN chown -R ray /home/ray/test
RUN chown -R ray /home/ray/test-data
USER ray

# Set environment
ENV PYTHONPATH /home/ray

# Put these at the end since they seem to upset the docker cache.
ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT