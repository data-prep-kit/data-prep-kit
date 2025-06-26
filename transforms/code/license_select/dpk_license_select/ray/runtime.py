# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from data_processing.utils import ParamsUtils

################################################################################
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray.runtime_configuration import (
    RayTransformRuntimeConfiguration,
)
from dpk_license_select.transform import LicenseSelectTransformConfiguration


class LicenseSelectRayTransformConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=LicenseSelectTransformConfiguration())


class LicenseSelect:
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
        default_language_column = "license"
        if "lc_license_column_name" not in self.params:
            self.params["lc_license_column_name"] = default_language_column
        if "lc_licenses_file" not in self.params:
            approved_license_file = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../test-data/sample_approved_licenses.json")
            )

            self.params["lc_licenses_file"] = approved_license_file

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        # create launcher
        launcher = RayTransformLauncher(LicenseSelectRayTransformConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


def main():
    launcher = RayTransformLauncher(LicenseSelectRayTransformConfiguration())
    launcher.launch()


if __name__ == "__main__":
    main()
