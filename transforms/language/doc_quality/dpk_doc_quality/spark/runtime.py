# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2025.
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
from typing import Any

from data_processing_spark.runtime.spark import (
    DefaultSparkTransformRuntime,
    SparkTransformLauncher,
    SparkTransformRuntimeConfiguration,
)
from dpk_doc_quality.transform import DocQualityTransformConfiguration


class DocQualitySparkTransformConfiguration(SparkTransformRuntimeConfiguration):
    """
    Implements the SparkTransformConfiguration for DocQuality transform.
    """

    def __init__(self):
        """
        Initialization
        Pass both transform_config AND runtime_class to the parent
        """
        super().__init__(
            transform_config=DocQualityTransformConfiguration(),
            runtime_class=DocQualitySparkTransformRuntime
        )


class DocQualitySparkTransformRuntime(DefaultSparkTransformRuntime):
    """
    DocQuality Spark runtime implementation.
    """

    def __init__(self, params: dict[str, Any]):
        """
        Constructor
        :param params: parameters dictionary
        """
        super().__init__(params=params)


if __name__ == "__main__":
    launcher = SparkTransformLauncher(DocQualitySparkTransformConfiguration())
    launcher.launch()
