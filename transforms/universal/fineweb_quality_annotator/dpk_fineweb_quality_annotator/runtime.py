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
from data_processing.utils import get_logger, ParamsUtils
from dpk_fineweb_quality_annotator.transform import FineWebQualityAnnotatorConfiguration
logger = get_logger(__name__)


class FineWebQualityAnnotatorPythonConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=FineWebQualityAnnotatorConfiguration())


class FineWebQualityAnnotator:
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
        try:
            worker_options = {k: self.params[k] for k in ("num_cpus", "memory")}
            self.params["runtime_worker_options"] = ParamsUtils.convert_to_ast(worker_options)
            del self.params["num_cpus"]
            del self.params["memory"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        # create launcher
        launcher = PythonTransformLauncher(FineWebQualityAnnotatorPythonConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = PythonTransformLauncher(FineWebQualityAnnotatorPythonConfiguration())
    logger.info("Launching FineWebQualityAnnotator Pure Python transform")
    launcher.launch()