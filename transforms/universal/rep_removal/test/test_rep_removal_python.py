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

import os
import json
import tempfile
import pandas as pd
import pyarrow.parquet as pq
from dpk_rep_removal.runtime import RepRemoval

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))

class TestRepRemovalPython:
    def test_rep_removal(self):
        RepRemoval(input_folder=basedir + "/input",
                   output_folder=basedir + "/output",
                   rep_removal_contents_column_name='text',
                   ).transform()

        table1 = pq.read_table(os.path.join(basedir, 'expected', 'test1.parquet'))
        table2 = pq.read_table(os.path.join(basedir, 'output', 'test1.parquet'))

        assert table1.equals(table2)

    def test_wrong_contents_field(self):
        RepRemoval(input_folder=basedir + "/input",
                   output_folder=basedir + "/output",
                   rep_removal_contents_column_name='contents',
                   ).transform()

        with open(os.path.join(basedir, 'output', 'metadata.json'), 'r') as f:
            data = json.load(f)
            assert data['job_output_stats']['result_files'] == 0

    def test_remove_first_copy(self):
        RepRemoval(input_folder=basedir + "/input",
                   output_folder=basedir + "/output",
                   rep_removal_contents_column_name='text',
                   rep_removal_retain_first_copy=False,
                   ).transform()

        table1 = pq.read_table(os.path.join(basedir, 'expected', 'test1.parquet'))
        table2 = pq.read_table(os.path.join(basedir, 'output', 'test1.parquet'))

        assert not table1.equals(table2)

    def test_no_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            df = pd.read_parquet(os.path.join(basedir, 'expected', 'test1.parquet'))
            new_df = df.loc[[0, 1, 2, 3, 4, 10, 11, 12, 13, 14]].copy()
            os.mkdir(os.path.join(td, 'input'))
            new_df.to_parquet(os.path.join(td, 'input', 'test1.parquet'))

            RepRemoval(input_folder=os.path.join(td, 'input'),
                       output_folder=os.path.join(td, 'output'),
                       rep_removal_contents_column_name='text',
                       rep_removal_num_threads='1',
                       ).transform()

            with open(os.path.join(td, 'output', 'metadata.json'), 'r') as f:
                data = json.load(f)
                print(data)

                assert data['job_output_stats']['duplicates_found'] == 0
