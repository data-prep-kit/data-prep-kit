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

from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)
from data_processing.utils import ParamsUtils, get_logger
from dpk_collapse.transform import CollapseTransformConfiguration


logger = get_logger(__name__)



class CollapseRuntimeConfiguration(PythonTransformRuntimeConfiguration):
    """
    Implements the PythonTransformConfiguration for HTML2PARQUET as required by the PythonTransformLauncher.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=CollapseTransformConfiguration())


# Class used by the notebooks to ingest binary files and create parquet files
class Collapse:
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
        launcher = PythonTransformLauncher(CollapseRuntimeConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(CollapseRuntimeConfiguration())
    logger.info("Launching Collapse transform")
    launcher.launch()
