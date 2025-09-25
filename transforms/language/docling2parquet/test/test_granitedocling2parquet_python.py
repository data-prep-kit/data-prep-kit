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
import os
import tempfile
import pyarrow.parquet as pq
from dpk_docling2parquet.transform_python import Docling2Parquet
from dpk_docling2parquet.transform import docling2parquet_contents_types


def test_granite_docling():
    basedir = "../test-data"
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), basedir))
    with tempfile.TemporaryDirectory() as temp_dir:
        x = Docling2Parquet(input_folder=os.path.join(basedir, "granite_docling_input"),
                            output_folder=temp_dir,
                            data_files_to_use=['.pdf'],
                            docling2parquet_contents_type=docling2parquet_contents_types.JSON,
                            docling2parquet_pipeline="vlm").transform()

        table1 = pq.read_table(os.path.join(temp_dir, 'granite-docling.parquet')).to_pandas()
        table2 = pq.read_table(os.path.join(basedir, 'granite_docling_expected', 'granite-docling.parquet')).to_pandas()

        assert table1['num_doc_elements'].values[0] == table2['num_doc_elements'].values[0]
        assert table1['num_pages'].values[0] == table2['num_pages'].values[0]
        assert table1['num_tables'].values[0] == table2['num_tables'].values[0]