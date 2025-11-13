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


from typing import Any

from data_processing_spark.runtime.spark import (
    DefaultSparkTransformRuntime,
    SparkTransformLauncher,
    SparkTransformRuntimeConfiguration,
)

from dpk_docling2parquet.transform import Docling2ParquetTransformConfiguration


class Docling2ParquetSparRuntime(DefaultSparkTransformRuntime):
    def __init__(self, params: dict[str, Any]):
        """
        Create/config this runtime.
        :param params: parameters, often provided by the CLI arguments as defined by a TableTansformConfiguration.
        """
        super().__init__(params)


class Docling2ParquetSparkTransformConfiguration(SparkTransformRuntimeConfiguration):
    """
    Implements the SparkTransformConfiguration for Docling2Parquet transform.
    """

    def __init__(self):
        """
        Initialization
        Pass both transform_config AND runtime_class to the parent
        """
        super().__init__(transform_config=Docling2ParquetTransformConfiguration(), runtime_class=Docling2ParquetSparRuntime)


if __name__ == "__main__":
    launcher = SparkTransformLauncher(Docling2ParquetSparkTransformConfiguration())
    launcher.launch()
