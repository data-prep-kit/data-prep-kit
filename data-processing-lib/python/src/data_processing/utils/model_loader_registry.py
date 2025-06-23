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
import fasttext
from huggingface_hub import hf_hub_download
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification

MODEL_LOADERS = {}


def register_model_loader(model_type: str):
    def wrapper(func):
        MODEL_LOADERS[model_type.lower()] = func
        return func
    return wrapper


@register_model_loader("transformers")
def load_transformers_model(model_path: str, token: str = None, **kwargs):
    model = AutoModel.from_pretrained(model_path, token=token, **kwargs)
    return model


@register_model_loader("tokenizer")
def load_transformers_model(model_path: str, token: str = None, **kwargs):
    tokenizer = AutoTokenizer.from_pretrained(model_path, token=token, **kwargs)
    return tokenizer

@register_model_loader("sequence")
def load_transformers_model(model_path: str, token: str = None, **kwargs):
    model = AutoModelForSequenceClassification.from_pretrained(model_path, token=token, **kwargs)
    return model


@register_model_loader("fasttext")
def load_fasttext_model(model_path: str, token: str = None, **kwargs):
    if os.path.isfile(model_path):
        model_path = model_path

    elif os.path.isdir(model_path):
        found = False
        for root, _, files in os.walk(model_path):
            for f in files:
                if f.endswith(".bin"):
                    model_path = os.path.join(root, f)
                    found = True
                    break
        if not found:
            raise FileNotFoundError(f"No .bin file found in : {model_path}")

    else:
        # assume hugging face repo and download .bin
        filename = kwargs.get("model_filename", "model.bin")
        model_path = hf_hub_download(repo_id=model_path, filename=filename, token=token)

    model = fasttext.load_model(model_path)
    return model
