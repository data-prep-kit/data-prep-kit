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

from data_processing.utils import get_logger


short_name = "et"
cli_prefix = short_name + "_"

logger = get_logger(__name__)

# TODO: these go away configuration keys
contents_column_name_key = "contents_column_name"
""" Key holds the name of the column holding the document text."""
arrow_path_key = "arrow_path"
""" Key holds the arrow folder location"""

# CLI parameters corresponding to each config key
contents_column_name_cli_param = f"{cli_prefix}{contents_column_name_key}"
""" Name of the column holding the document text"""
arrow_path_cli_param = f"{cli_prefix}{arrow_path_key}"
""" Arrow folder location"""

captured_arg_keys = [
    contents_column_name_key,
    arrow_path_key,
]
""" The set of keys captured from the command line """

# defaults
contents_column_name_default = "text"
""" The default name of the column holding the document text. Default is `text`."""
arrow_path_default = None
""" The default location of the arrow folder."""

# data access configuration
extreme_tokenized_data_factory_key = f"{short_name}_data_factory"
extreme_tokenized_data_access_key = "data_access"
