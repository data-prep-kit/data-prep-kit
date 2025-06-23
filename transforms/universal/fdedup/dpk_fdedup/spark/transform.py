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

from dpk_fdedup.cluster_analysis.spark.transform import ClusterAnalysisSparkTransformConfiguration
from dpk_fdedup.data_cleaning.spark.transform import DataCleaningSparkTransformConfiguration
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing_spark.runtime.spark import SparkTransformLauncher
from dpk_fdedup.transform_python import ServiceOrchestrator, parse_args
from dpk_fdedup.get_duplicate_list.transform_python import (
    GetDuplicateListPythonTransformConfiguration,
)
from dpk_fdedup.signature_calc.spark.transform import (
    SignatureCalculationSparkTransformConfiguration,
)


s3_creds = {
    "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "url": os.getenv("AWS_ENDPOINT_URL"),
}


class SparkServiceOrchestrator(ServiceOrchestrator):
    def __init__(self, global_params: argparse.Namespace = None):
        super().__init__(global_params=global_params)

    def execute_service(self, service_short_name: str, params: list) -> int:
        sys.argv = params
        if service_short_name == "minhash":
            launcher = SparkTransformLauncher(runtime_config=SignatureCalculationSparkTransformConfiguration())
        elif service_short_name == "cluster":
            launcher = SparkTransformLauncher(runtime_config=ClusterAnalysisSparkTransformConfiguration())
        elif service_short_name == "fdlist":
            launcher = PythonTransformLauncher(runtime_config=GetDuplicateListPythonTransformConfiguration())
        elif service_short_name == "fdclean":
            launcher = SparkTransformLauncher(runtime_config=DataCleaningSparkTransformConfiguration())
        status = launcher.launch()
        return status


if __name__ == "__main__":

    # Parse command line arguments
    args = parse_args()
    # Initialize the orchestrator
    orchestrator = SparkServiceOrchestrator(global_params=args)
    # Launch spark fuzzy dedup execution
    orchestrator.orchestrate()
