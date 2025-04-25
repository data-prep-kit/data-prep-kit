ARG BASE_IMAGE=docker.io/rayproject/ray:2.24.0-py310

FROM ${BASE_IMAGE}

RUN pip install --upgrade --no-cache-dir pip 

ARG EXTRA_INDEX_URL
ARG PIP_INSTALL_EXTRA_ARGS

# Install pytest so we can test the image later
RUN pip install --no-cache-dir pytest

USER root
RUN apt update
RUN apt install vim -y
# for OpenCV dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
USER ray

# Needed for iocr
RUN which python
RUN conda install -c conda-forge python=3.11 -y


# Install code from adjacent python directory, expected here via Makefile
COPY --chown=ray:users python-transform/  python-transform/
# Inner repo does yet 
RUN cd python-transform && pip install ${PIP_INSTALL_EXTRA_ARGS} --no-cache-dir -e .


# Install this project's source
COPY --chown=ray:users src/  src/
COPY --chown=ray:users pyproject.toml pyproject.toml
RUN pip install ${PIP_INSTALL_EXTRA_ARGS} --no-cache-dir -e .

# Pull the image entry point(s) to the home directory.
COPY ./src/nsfw_ray/nsfw_transform_ray.py .
COPY ./src/doc_nsfw_ray/doc_nsfw_transform_ray.py .
COPY ./src/people_ray/people_transform_ray.py .
COPY ./src/p2j_ray/p2j_transform_ray.py .
COPY ./src/j2p_ray/j2p_transform_ray.py .
COPY ./src/j2j_ray/j2j_transform_ray.py .
COPY ./src/child_ray/child_transform_ray.py .
COPY ./src/iocr_ray/iocr_transform_ray.py .

RUN mkdir models
COPY models/ models/
COPY test/ test/
COPY test-data/ test-data/

# For MatPlotLib
RUN mkdir /home/ray/.config && chmod -R 777 /home/ray/.config

# For HF in NSFW 
RUN chmod -R 777 /home/ray/.cache

ENV PYTHONPATH /home/ray:/home/ray/src

# Put these at the end since they seem to upset the docker cache.
ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT
RUN python --version
