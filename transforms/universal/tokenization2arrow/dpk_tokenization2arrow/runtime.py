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

import sys

from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
)
from data_processing.utils import ParamsUtils
from dpk_tokenization2arrow.transform import Tokenization2ArrowTransformConfiguration


class Tokenization2ArrowPythonConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=Tokenization2ArrowTransformConfiguration())


class Tokenization2Arrow:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        # if input_folder and output_folder are specified, then assume it is represent data_local_config
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        # create launcher
        launcher = PythonTransformLauncher(Tokenization2ArrowPythonConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(Tokenization2ArrowPythonConfiguration())
    launcher.launch()
