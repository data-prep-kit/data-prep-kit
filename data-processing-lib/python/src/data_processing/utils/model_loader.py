# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
import os
import tempfile
import shutil
from data_processing.utils import ParamsUtils, get_dpk_logger
from data_processing.utils.model_loader_registry import MODEL_LOADERS
logger = get_dpk_logger()


def load_model(model_path_or_url: str, model_type: str, token: str = None, **kwargs):
    """
    Load a model using a registered model loader type (plugin-style).
    """
    temp_dir = None
    model = None
    model_type = model_type.lower()

    # check if model_type is supported
    if model_type not in MODEL_LOADERS:
        logger.error(f"Unsupported model_type '{model_type}'. Available types: {list(MODEL_LOADERS)}")
        raise ValueError(f"Unsupported model_type '{model_type}'. Available types: {list(MODEL_LOADERS)}")

    try:
        # handle s3/COS
        if model_path_or_url.startswith("s3://"):
            from data_processing.data_access import DataAccessS3
            s3_url = model_path_or_url[5:]
            temp_dir = tempfile.mkdtemp()

            s3 = DataAccessS3(config={'prefix': kwargs.get('prefix')})
            files = s3._list_files_folder(s3_url)[0]

            if len(files) > 0:
                for file in files:
                    if file['name'].endswith('/'):
                        continue

                    # strip prefix to get relative path
                    relative_path = file['name'][len(s3_url):].lstrip('/')
                    if not relative_path or relative_path == "":
                        relative_path = os.path.basename(file['name'])

                    # construct local path
                    local_path = os.path.join(temp_dir, relative_path)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    bucket, s3_key = file['name'].split('/', 1)
                    s3.arrS3.s3_client.download_file(bucket, s3_key, local_path)

                model_path = temp_dir

            else:
                logger.error(f"No files found at S3 path: {model_path_or_url}")
                raise FileNotFoundError(f"No files found at S3 path: {model_path_or_url}")

        # check locally filesystem
        elif os.path.exists(model_path_or_url):
            model_path = model_path_or_url

        # assume hf hub
        else:
            model_path = model_path_or_url

        # dispatch to registered loader
        loader_fn = MODEL_LOADERS[model_type]
        model = loader_fn(model_path, token=token, **kwargs)
        return model

    except Exception as e:
        logger.error(f"Not able to download files at S3 path: {model_path_or_url}")
        raise RuntimeError(f"Failed to load model from '{model_path_or_url}': {e}")

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
