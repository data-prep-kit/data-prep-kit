# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2025.
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


short_name = "readability"
cli_prefix = short_name + "_"

# create parameters
# when running as a packaged module, we need to use curent folder: python -m readability_local
# During development, this is usuall run from the Python folder: python src/readability_local.py
input_folder = os.path.abspath(os.path.join(os.getcwd(), "test-data", "input"))
output_folder = os.path.abspath(os.path.join(os.getcwd(), "test-data", "output"))
expected_folder = os.path.abspath(os.path.join(os.getcwd(), "test-data", "expected"))


local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}

####################################################################
# configuration keys. Also used as column names for various scores
flesch_ease_textstat = "flesch_ease_textstat"
"""Key holds the flesch_ease_textstat R score threshold parameter"""
flesch_ease_pypi = "flesch_ease_pypi"
"""Key holds the flesch_ease_pypi R score threshold parameter"""
flesch_kincaid_textstat = "flesch_kincaid_textstat"
"""Key holds the flesch_kincaid_textstat R score threshold parameter"""
flesch_kincaid_pypi = "flesch_kincaid_pypi"
"""Key holds the flesch_kincaid_pypi R score threshold parameter"""
gunning_fog_textstat = "gunning_fog_textstat"
"""Key holds the gunning_fog_textstat R score threshold parameter"""
gunning_fog_pypi = "gunning_fog_pypi"
"""Key holds the gunning_fog_pypi R score threshold parameter"""
smog_index_textstat = "smog_index_textstat"
"""Key holds the smog_index_textstat R score threshold parameter"""
coleman_liau_index_textstat = "coleman_liau_index_textstat"
"""Key holds the coleman_liau_index_textstat R score threshold parameter"""
automated_readability_index_textstat = "automated_readability_index_textstat"
"""Key holds the automated_readability_index_textstat R score threshold parameter"""
dale_chall_readability_score_textstat = "dale_chall_readability_score_textstat"
"""Key holds the dale_chall_readability_score_textstat R score threshold parameter"""
difficult_words_textstat = "difficult_words_textstat"
"""Key holds the difficult_words_textstat R score threshold parameter"""
linsear_write_formula_textstat = "linsear_write_formula_textstat"
"""Key holds the linsear_write_formula_textstat R score threshold parameter"""
text_standard_textstat = "text_standard_textstat"
"""Key holds the text_standard_textstat R score threshold parameter"""
spache_readability_textstat = "spache_readability_textstat"
"""Key holds the spache_readability_textstat R score threshold parameter"""
mcalpine_eflaw_textstat = "mcalpine_eflaw_textstat"
"""Key holds the mcalpine_eflaw_textstat R score threshold parameter"""
reading_time_textstat = "reading_time_textstat"
"""Key holds the reading_time_textstat R score threshold parameter"""
contents_column_name = "contents_column_name"
"""Contents column name for the input parquet table to the transform"""
score_list = "score_list"
"""list of readability scores to be computed by the transform"""


########################################################################################
# CLI parameters corresponding to each config key
"""avg_grade_level R score threshold parameter"""
contents_column_name_cli_param = f"{cli_prefix}{contents_column_name}"
"""Content column name for parquet input table to transform"""
score_list_cli_param = f"{cli_prefix}{score_list}"
"""list of readability scores or a single readability scores to be computed by the transform"""


# The set of default value that can be overwritten from the CLI """
contents_column_name_default = "contents"
"""The default value for contents_column_name"""
score_list_default = mcalpine_eflaw_textstat
"""readability score that is computed by default"""
