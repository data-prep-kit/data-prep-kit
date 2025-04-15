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
from typing import Any

from data_processing.data_access import DataAccessFactoryBase
from data_processing.utils import ParamsUtils, get_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray.runtime_configuration import (
    DefaultRayTransformRuntime,
    RayTransformRuntimeConfiguration,
)
from dpk_proglang_select.transform import (
    ProgLangSelectTransformConfiguration,
    _get_supported_languages,
    lang_allowed_langs_file_key,
    lang_allowed_languages,
    lang_data_factory_key,
    lang_lang_column_key,
    lang_output_column_key,
)
from ray.actor import ActorHandle


logger = get_logger(__name__)


class ProgLangSelectRuntime(DefaultRayTransformRuntime):
    """
    Language selector runtime support
    """

    def __init__(self, params: dict[str, Any]):
        """
        Create filter runtime
        :param params: parameters, that should include
            ls_lang_column_key: name of the column with language
            ls_allowed_langs_file_key: location of the allowed languages file
            ls_known_selector: A flag on whether return rows with valid or invalid languages
        """
        super().__init__(params)
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__)

    def get_transform_config(
        self,
        data_access_factory: DataAccessFactoryBase,
        statistics: ActorHandle,
        files: list[str],
    ) -> dict[str, Any]:
        """
        Set environment for filter execution
        :param data_access_factory - data access factory
        :param statistics - reference to the statistics object
        :param files - list of files to process
        :return: dictionary of filter init params
        """
        lang_file = self.params.get(lang_allowed_langs_file_key, None)
        if lang_file is None:
            raise RuntimeError(f"Missing configuration key {lang_allowed_langs_file_key}")
        lang_data_access_factory = self.params.get(lang_data_factory_key, None)
        if lang_data_access_factory is None:
            raise RuntimeError(f"Missing configuration key {lang_data_factory_key}")
        lang_list = _get_supported_languages(
            lang_file=lang_file,
            data_access=lang_data_access_factory.create_data_access(),
            logger=self.logger,
        )
        # lang_refs = ray.put(list(lang_list))
        # logger.info(f"Placed language list into Ray object storage under reference{lang_refs}")
        # return {lang_allowed_languages: lang_refs} | self.params
        return {lang_allowed_languages: lang_list} | self.params


class ProgLangSelectRayConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=ProgLangSelectTransformConfiguration(), runtime_class=ProgLangSelectRuntime)


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
                    "../../test-data/languages/allowed-code-languages.txt",
                )
            )
        if lang_output_column_key not in self.params:
            self.params[lang_output_column_key] = default_annotated_column

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        # create launcher
        launcher = RayTransformLauncher(ProgLangSelectRayConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = RayTransformLauncher(ProgLangSelectRayConfiguration())
    launcher.launch()
