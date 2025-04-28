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

short_name = "ml_filter"
description = "filter using a per-language table of conditions"
ray_invocation = "-m dpk_ml_filter.ray.runtime"
invocation = "-m dpk_ml_filter.runtime"

Param = namedtuple("Param", "Name Required Type Default Description")
_param_table = [
        Param("column_prefix", False, str, "", "Prefix for to all columns referenced in the conditions table"),
        Param("lang_column_name", False, str, "lang", "Name of the column with the language identifier"),
        Param("config", False, str, os.path.expanduser("~/cleansing-config.yaml"), "File name for the condition table (yaml)"),
        Param("ignore_missing_columns", False, bool, False, "Ignore conditions that reference fields not present in the data"),
    ]

def get_transform_params():
    return _param_table

def get_transform_param_defaults():
    return {p.Name: p.Default for p in get_transform_params()}

