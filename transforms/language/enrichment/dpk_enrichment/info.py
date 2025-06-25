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

import dpk_enrichment.features as fs

short_name = "enrichment"
description = "computes a number of features that can be used estimate data quality"

# parameter table: name, type, default_value, description
_param_table = [
        ("output_column_prefix", str, "", "Prefix to add to all output column names that are not explicitly defined"),
        ("content_column_name", str, "text", "Name of the content column"),
        ("lang_column_name", str, "lang", "Name of the column with the language identifier"),
        ("newline_normalized_column_name", str, "", "Name of an output column for newline normalized text"),
        ("error_column_name", str, "", "Name of an output column for the eventual error encountered during processing"),
    ]

def get_transform_params():
    table = [p for p in _param_table] + [(f"{k}_column_name", str, f"{k}", f"Column name for {k}") for k in fs.DEFAULT_TEXT_ENRICHER_DICT.keys()]
    return table

def get_transform_param_defaults():
    return {k: d for k, t, d, h  in get_transform_params()}

