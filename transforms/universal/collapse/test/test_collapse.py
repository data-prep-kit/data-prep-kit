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

import pyarrow.parquet as pq
from dpk_collapse.transform import *

config={"collapse_input_columns":["title","contents"],"collapse_output_column":"text2"}

table = pq.read_table('../test-data/input/sample1.parquet')

def test_basic_functionality():
    collapse=CollapseTransform(config)
    results, stats=collapse.transform(table)
    initial_columns=table.column_names
    new_columns=results[0].column_names
    assert config["collapse_input_columns"]==[x for x in initial_columns if x not in new_columns]
    assert [config['collapse_output_column']]==[x for x in new_columns if x not in initial_columns]

