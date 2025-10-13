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
from dpk_filter.runtime import Filter
from dpk_filter.transform import FilterTransform, filter_columns_to_drop_key, filter_criteria_key,filter_logical_operator_key
from data_processing.data_access import DataAccessLocal
from data_processing.utils import TransformUtils
import os
import tempfile


def test_transform_default():
    import pyarrow.parquet as pq
    FilterTransform(config={}).transform(pq.read_table('../test-data/input/test1.parquet'))


def test_empty_table():
    # nothing should match this criteria
    filter_criteria = [
        "docq_total_words > 10000 AND docq_total_words < 20000",
        "ibmkenlm_docq_perplex_score < 230",
    ]
    filter_logical_operator = "AND"
    filter_columns_to_drop = ["extra", "cluster"]

    filter_params = {
        filter_criteria_key: filter_criteria,
        filter_columns_to_drop_key: filter_columns_to_drop,
        filter_logical_operator_key: filter_logical_operator,
    }
    transform = FilterTransform(filter_params)

    input_folder = "../test-data/input"
    output_folder = "../test-data/output"
    local_conf = {
        "input_folder": input_folder,
        "output_folder": output_folder,
    }
    data_access = DataAccessLocal(local_conf)
    table, _ = data_access.get_table(os.path.join(input_folder, "test1.parquet"))

    table_list, metadata = transform.transform(table)
    assert len(table_list) > 0
    assert table_list[0].num_rows == 0

    # test with bad table name
    table_list, metadata = transform.transform(table, 'bad_name.par')
    assert len(table_list) > 0
    assert table_list[0].num_rows == 0


def test_empty_table_runtime():
    import pyarrow.parquet as pq
    with tempfile.TemporaryDirectory() as dir:
        Filter(input_folder="../test-data/input",
               output_folder=os.path.join(dir, 'parquet'),
               filter_columns_to_drop=["extra", "cluster"],
               filter_criteria_list=[
                   "docq_total_words > 10000 AND docq_total_words < 20000",
                   "ibmkenlm_docq_perplex_score < 230",
               ],
               filter_logical_operator="AND").transform()

        table = pq.read_table(os.path.join(dir, 'parquet', 'test1.parquet'))
        og_table = pq.read_table(os.path.join('../test-data', 'input', 'test1.parquet'))

        assert table.schema == og_table.schema
        assert table.num_rows == 0

def test_empty_binary_table():
    # nothing should match this criteria
    filter_criteria = [
        "docq_total_words > 10000 AND docq_total_words < 20000",
        "ibmkenlm_docq_perplex_score < 230",
    ]
    filter_logical_operator = "AND"
    filter_columns_to_drop = ["extra", "cluster"]

    filter_params = {
        filter_criteria_key: filter_criteria,
        filter_columns_to_drop_key: filter_columns_to_drop,
        filter_logical_operator_key: filter_logical_operator,
    }
    transform = FilterTransform(filter_params)

    input_folder = "../test-data/input"
    output_folder = "../test-data/output"
    local_conf = {
        "input_folder": input_folder,
        "output_folder": output_folder,
    }
    data_access = DataAccessLocal(local_conf)
    byte_array, _ = data_access.get_file(os.path.join(input_folder, "test1.parquet"))

    table_list, metadata = transform.transform_binary(os.path.join(input_folder, "test1.parquet"), byte_array)
    assert len(table_list) > 0

    bytes = table_list[0][0]
    table = TransformUtils.convert_binary_to_arrow(bytes)
    assert table.num_rows == 0
