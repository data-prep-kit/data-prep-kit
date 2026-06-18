# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

from typing import Any

from data_processing.runtime.pure_python import (
    DefaultPythonTransformRuntime,
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
    Transform,
)
from data_processing.transform import TransformStatistics
from data_processing.utils import get_dpk_logger
from dpk_yara.transform import YaraTransformConfiguration


logger = get_dpk_logger()


class YaraPythonTransformRuntime(DefaultPythonTransformRuntime):
    """Custom runtime that computes percentage stats after all batches are aggregated."""

    def __init__(self, params: dict[str, Any]):
        super().__init__(params)

    def compute_execution_stats(self, stats: TransformStatistics) -> None:
        s = stats.get_execution_stats()
        total = s.get("total_docs", 0)
        if total > 0:
            s["pct_docs_infected"] = round(100.0 * s.get("docs_infected", 0) / total, 2)
            s["pct_docs_clean"] = round(100.0 * s.get("docs_clean", 0) / total, 2)


class YaraPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(
            transform_config=YaraTransformConfiguration(),
            runtime_class=YaraPythonTransformRuntime,
        )


class Yara(Transform):
    def __init__(self, **kwargs):
        super().__init__(YaraTransformConfiguration(), **kwargs)
        self.runtime = YaraPythonTransformConfiguration()


if __name__ == "__main__":
    launcher = PythonTransformLauncher(YaraPythonTransformConfiguration())
    logger.info("Launching yara transform")
    launcher.launch()
