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
from typing import Any, Union


class DPKConfig:
    @staticmethod
    def _get_first_env_var(env_var_list: list[str], default_value: str=None) -> Union[str, None]:
        for var in env_var_list:
            value = os.environ.get(var, None)
            if value is not None:
                # print(f"Found env var {var}", flush=True)
                return value
        # print(f"Did not find any of the following env vars {env_var_list}")
        return default_value

    HUGGING_FACE_TOKEN = _get_first_env_var(["DPK_HUGGING_FACE_TOKEN"])
    """ Set from DPK_HUGGING_FACE_TOKEN env var(s) """


    @staticmethod
    def set_env_var(var: str, value: str, force: bool=True) -> str:
        prev = os.environ.get(var, None)
        if (prev is None) or force:
            os.environ[var]=value
            return value
        return prev

def add_if_missing(config: dict[str, Any], key: str, dflt: Any):
    """
    Add the given default key value if there no value for the key in the dictionary.
    :param config:
    :param key:
    :param dflt:
    :return:
    """
    if config is None:
        return
    value = config.get(key)
    if value is None:
        config[key] = dflt
