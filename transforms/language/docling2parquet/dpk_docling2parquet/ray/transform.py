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

from data_processing.utils import ParamsUtils, get_logger


try:
    from data_processing_ray.runtime.ray import RayTransformLauncher
    from data_processing_ray.runtime.ray.runtime_configuration import (
        RayTransformRuntimeConfiguration,
    )
except ImportError:
    raise ImportError("Please install data_prep_toolkit[ray]")

from dpk_docling2parquet.transform import (
    Docling2ParquetTransform,
    Docling2ParquetTransformConfiguration,
)
from ray.util.metrics import Counter, Gauge


logger = get_logger(__name__)


class Docling2ParquetRayTransform(Docling2ParquetTransform):
    def __init__(self, config: dict):
        """ """
        super().__init__(config)

        self.doc_counter = Counter("worker_doc_count", "Number of documents converted by the worker")
        self.page_counter = Counter("worker_doc_pages_count", "Number of document pages converted by the worker")
        self.page_convert_gauge = Gauge(
            "worker_doc_page_avg_convert_time", "Average time for converting a single document page on each worker"
        )
        self.doc_convert_gauge = Gauge("worker_document_convert_time", "Time spent converting a single document")

    def _update_metrics(self, num_pages: int, elapse_time: float):
        if num_pages > 0:
            self.page_convert_gauge.set(elapse_time / num_pages)
            self.page_counter.inc(num_pages)
        self.doc_convert_gauge.set(elapse_time)
        self.doc_counter.inc(1)


class Docling2ParquetRayTransformConfiguration(RayTransformRuntimeConfiguration):
    """
    Implements the RayTransformConfiguration for docling2parquet as required by the RayTransformLauncher.
    """

    def __init__(self):
        """
        Initialization
        :param base_configuration - base configuration class
        """
        super().__init__(transform_config=Docling2ParquetTransformConfiguration(transform_class=Docling2ParquetRayTransform))


# Class used by the notebooks to ingest binary files and create parquet files
class Docling2Parquet:
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
        launcher = RayTransformLauncher(Docling2ParquetRayTransformConfiguration())
        # launch
        return_code = launcher.launch()
        return return_code


if __name__ == "__main__":
    launcher = RayTransformLauncher(Docling2ParquetRayTransformConfiguration())
    logger.info("Launching docling2parquet transform")
    launcher.launch()
