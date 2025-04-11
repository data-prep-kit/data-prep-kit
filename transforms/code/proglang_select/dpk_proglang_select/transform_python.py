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
import sys

from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
)
from data_processing.utils import ParamsUtils, get_logger
from dpk_proglang_select.transform import (
    ProgLangSelectTransformConfiguration,
    lang_allowed_langs_file_key,
    lang_lang_column_key,
    lang_output_column_key,
)


logger = get_logger(__name__)


class ProgLangSelectPythonConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=ProgLangSelectTransformConfiguration())


class ProglangSelect:
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

        # create parameters
        default_language_column = "language"
        default_annotated_column = "lang_selected"
        if lang_lang_column_key not in self.params:
            self.params[lang_lang_column_key] = default_language_column
        if lang_allowed_langs_file_key not in self.params:
            self.params[lang_allowed_langs_file_key] = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "../test-data/languages/allowed-code-languages.txt",
                )
            )
        if lang_output_column_key not in self.params:
            self.params[lang_output_column_key] = default_annotated_column

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        # create launcher
        launcher = PythonTransformLauncher(ProgLangSelectPythonConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(ProgLangSelectPythonConfiguration())
    launcher.launch()
