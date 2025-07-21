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

import argparse
import os
import sys

from dpk_fdedup.cluster_analysis.ray.transform import ClusterAnalysisRayTransformConfiguration
from dpk_fdedup.data_cleaning.ray.transform import DataCleaningRayTransformConfiguration
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.utils import ParamsUtils
from data_processing_ray.runtime.ray import RayTransformLauncher
from dpk_fdedup.transform_python import ServiceOrchestrator, parse_args
from dpk_fdedup.get_duplicate_list.transform_python import (
    GetDuplicateListPythonTransformConfiguration,
)
from dpk_fdedup.get_duplicate_list.ray.transform import (
    GetDuplicateListRayRuntime,
    GetDuplicateListRayTransformConfiguration,
)
from dpk_fdedup.signature_calc.ray.transform import SignatureCalculationRayTransformConfiguration


s3_creds = {
    "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "url": os.getenv("AWS_ENDPOINT_URL"),
}


ray_worker_options = {"num_cpus": 0.8}
ray_params = {
    # where to run
    "run_locally": True,
    # orchestrator
    "runtime_worker_options": ParamsUtils.convert_to_ast(ray_worker_options),
    "runtime_num_workers": 3,
}

ray_params_argv = ParamsUtils.dict_to_req(ray_params)


class RayServiceOrchestrator(ServiceOrchestrator):
    def __init__(self, global_params: argparse.Namespace = None):
        super().__init__(global_params=global_params)

    def execute_service(self, service_short_name: str, params: list) -> int:
        sys.argv = params if service_short_name == "fdlist" else ray_params_argv + params[1:]
        if service_short_name == "minhash":
            launcher = RayTransformLauncher(runtime_config=SignatureCalculationRayTransformConfiguration())
        elif service_short_name == "cluster":
            launcher = RayTransformLauncher(runtime_config=ClusterAnalysisRayTransformConfiguration())
        elif service_short_name == "fdlist":
            launcher = RayTransformLauncher(runtime_config=GetDuplicateListRayTransformConfiguration())
        elif service_short_name == "fdclean":
            launcher = RayTransformLauncher(runtime_config=DataCleaningRayTransformConfiguration())
        status = launcher.launch()
        return status


# Class used by the notebooks to ingest binary files and create parquet files
class Fdedup:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        args = parse_args()
        # Initialize the orchestrator
        orchestrator = RayServiceOrchestrator(global_params=args)
        # Launch python fuzzy dedup execution
        return orchestrator.orchestrate()


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    # Initialize the orchestrator
    orchestrator = RayServiceOrchestrator(global_params=args)
    # Launch ray fuzzy dedup execution
    orchestrator.orchestrate()
