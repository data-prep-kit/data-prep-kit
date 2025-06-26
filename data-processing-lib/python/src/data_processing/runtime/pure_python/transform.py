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

from data_processing.utils import ParamsUtils
from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
)


class Transform:
    """
    Used for streamlining API when calling transforms from notebook
    """
    def __init__(self, transform_config, **kwargs):
        """
        Cound be involed using TransformConfiguration and Runtime class 
        exaamples for invocation:
            super().__init(DocIDTransformConfiguration(), **kwargs)
        """
        self.params = {}
        self.runtime = PythonTransformRuntimeConfiguration(transform_config)
        for key in kwargs:
            self.params[key] = kwargs[key]
        # if input_folder and output_folder are specified, then assume it is represent data_local_config
        try:
            data_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            if data_conf['input_folder'].lower().startswith('s3:'):
                self.params["data_s3_config"]=ParamsUtils.convert_to_ast(data_conf)
            else:
                self.params["data_local_config"] = ParamsUtils.convert_to_ast(data_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass

    def transform(self):
        import sys
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        launcher = PythonTransformLauncher(self.runtime)
        return_code = launcher.launch()
        return return_code


    @staticmethod
    def launch(transform_config):
        """
        Cound be involed using TransformConfiguration and Runtime class 
        exaamples for invocation:
            Transform.launch(DocIDTransformConfiguration(), DocIDRuntime, **kwargs)
        """
        runtime = PythonTransformRuntimeConfiguration(transform_config)
        launcher = PythonTransformLauncher(runtime)
        return_code = launcher.launch()
        return return_code

