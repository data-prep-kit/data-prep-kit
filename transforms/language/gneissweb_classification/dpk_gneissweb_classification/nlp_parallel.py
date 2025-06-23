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

from typing import Any
from functools import partial

import pyarrow as pa
import multiprocessing

from data_processing.utils import TransformUtils, get_logger, load_model
from dpk_gneissweb_classification.classification_models import ClassificationModel, FastTextModel

logger = get_logger(__name__)

global_model: ClassificationModel = None

def init_global_model(url: str, file_name: str, credential: str):
    global global_model
    model = load_model(url, "fasttext", credential, model_filename=file_name)
    global_model = FastTextModel(model, url)
    
    
def _process(text_list):
    return [global_model.detect_label(r) for r in text_list]


def split_lists(text_list: list[str] | tuple[str, ...], num_chunks: int) -> list[list[str]]:
    num_rows = len(text_list)
    chunk_size = num_rows // num_chunks

    chunks: list[list[str]] = []
    i = 0
    while i < num_chunks:
        if i == num_chunks - 1:
            remainder = num_rows % num_chunks
        else:
            remainder = 0
        chunk = text_list[i * chunk_size : i * chunk_size + chunk_size + remainder]
        chunks.append(list(chunk))
        i += 1

    return chunks


def get_label_ds_pa_parallel(
    table: pa.table,
    content_column_name: str,
    output_label_column_name: str,
    output_score_column_name: str,
    n_processes: int = 4,
    url: str = None,
    file_name: str = None,
    credential: str = None
) -> tuple[pa.table, dict[str, Any]]:
    
    table_chunks = split_lists(table[content_column_name].to_pylist(), n_processes)
    
    with multiprocessing.get_context("spawn").Pool(n_processes, initializer=init_global_model, initargs=(url, file_name, credential)) as p:
        pool_results = p.map(_process, table_chunks)
        classification_results = []
        for result in pool_results:
            classification_results += result
        labels, scores = zip(*classification_results)
        detected_label = {"label": list(labels), "score": list(scores)}
    
    stats = pa.table([detected_label["label"]], names=["label"]).group_by("label").aggregate([("label", "count")])
    stats_dict = {}
    for batch in stats.to_batches():
        d = batch.to_pydict()
        for label, count in zip(d["label"], d["label_count"]):
            stats_dict[label] = count
    result = TransformUtils.add_column(table=table, name=output_label_column_name, content=detected_label["label"])
    result = TransformUtils.add_column(table=result, name=output_score_column_name, content=detected_label["score"])
    return result, stats_dict
