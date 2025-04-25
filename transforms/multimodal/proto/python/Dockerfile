FROM docker.io/python:3.10.14-slim-bullseye

RUN pip install --upgrade --no-cache-dir pip 

ARG EXTRA_INDEX_URL

# Install pytest so we can test the image later
RUN pip install --no-cache-dir pytest

ARG PIP_INSTALL_EXTRA_ARGS

RUN apt update
RUN apt install vim -y
# for OpenCV dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN useradd -ms /bin/bash dpk
USER dpk
WORKDIR /home/dpk

# Install this project's source
COPY --chown=dpk:root src/  src/
COPY --chown=dpk:root pyproject.toml pyproject.toml
RUN pip install ${PIP_INSTALL_EXTRA_ARGS} --no-cache-dir -e .

# Pull the image entry point(s) to the home directory.
COPY ./src/faces/faces_transform_python.py .

RUN mkdir models
COPY ./models/* ./models
COPY test/ test/
COPY test-data/ test-data/

ENV PYTHONPATH /home/ray:/home/ray/src

# Put these at the end since they seem to upset the docker cache.
ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build-date=$BUILD_DATE
LABEL git-commit=$GIT_COMMIT
