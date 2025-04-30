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

import dpk_enrichment.features as fs
from collections import namedtuple

__version__ = "1.0.0"
short_name = "enrichment"
description = "computes a number of features that can be used estimate data quality"
ray_invocation = "-m dpk_enrichment.ray.runtime"
invocation = "-m dpk_enrichment.runtime"

Param = namedtuple("Param", "Name Required Type Default Description")
_param_table = [
        Param("output_column_prefix", False, str, "", "Prefix to add to all output column names that are not explicitly defined"),
        Param("content_column_name", False, str, "text", "Name of the content column"),
        Param("lang_column_name", False, str, "lang", "Name of the column with the language identifier"),
        Param("newline_normalized_column_name", False, str, "", "Name of an output column for newline normalized text"),
        Param("error_column_name", False, str, "", "Name of an output column for the eventual error encountered during processing"),
    ]

def get_transform_params():
    table = [p for p in _param_table] + [Param(f"{k}_column_name", False, str, f"{k}", f"Column name for {k}") for k in fs.DEFAULT_TEXT_ENRICHER_DICT.keys()]
    return table

def get_transform_param_defaults():
    return {p.Name: p.Default for p in get_transform_params()}

