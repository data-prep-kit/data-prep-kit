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
from collections import namedtuple

__version__ = "1.0.1"
short_name = "lang_id"
description = "language identification (currently fasstext only)"
ray_invocation = "-m dpk_lang_id.ray.transform"
invocation = "-m dpk_lang_id.transform_python"

Param = namedtuple("Param", "Name Required Type Default Description")
_param_table = [
        Param("content_column_name", False, str, "contents", "Column name to get the content from"),
        Param("model_credential", False, str, os.environ.get("HF_READ_ACCESS_TOKEN", ""), "Credential to access the model for language detection placed in URL. When not set the environment variable \"HF_READ_ACCESS_TOKEN\" is used."),
        Param("model_kind", True, str, "", "Kind of model for language detection. Currently only fasttext is supported."),
        Param("model_url", True, str, "", "URL of model for language detection"),
        Param("output_lang_column_name", False, str, "lang", "Column name to store the identified language label"),
        Param("output_score_column_name", False, str, "score", "Column name to store the score of language identification"),
    ]

def get_transform_params():
    return _param_table

def get_transform_param_defaults():
    return {p.Name: p.Default for p in get_transform_params()}

