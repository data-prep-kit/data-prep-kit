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

from data_processing.test_support import get_tables_in_folder
from dpk_similarity.transform import SimilarityTransform, ES_ENDPOINT_KEY


def _normalize(value):
    """
    Recursively normalize a value decoded from a pyarrow column so that two tables
    holding the same data compare equal regardless of representation differences that
    vary across pyarrow/pandas versions:
      - struct field ordering (dict key order)
      - string vs large_string and list child naming (item vs element) collapse to
        plain Python str/list once decoded via to_pylist().
    """
    if isinstance(value, dict):
        return {k: _normalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def assert_tables_equivalent(actual, expected):
    """
    Compare two pyarrow tables by data only, tolerating schema-representation drift.

    The similarity transform round-trips the table through pandas, so the output
    `contents` type (string vs large_string) and list field naming (item vs element)
    depend on the installed pyarrow/pandas versions and on whether a table was read
    from parquet or built in memory. We therefore compare column names and decoded,
    key-sorted data rather than exact schemas.
    """
    assert sorted(actual.column_names) == sorted(expected.column_names), (
        f"Column names differ: {actual.column_names} vs {expected.column_names}"
    )
    assert actual.num_rows == expected.num_rows, (
        f"Row count differs: {actual.num_rows} vs {expected.num_rows}"
    )
    for name in expected.column_names:
        a = _normalize(actual.column(name).to_pylist())
        e = _normalize(expected.column(name).to_pylist())
        assert a == e, f"Column {name!r} differs.\nactual:   {a}\nexpected: {e}"


class TestSimilarityTransform:
    """
    Validate the similarity transform's output data against the expected fixture using a
    representation-tolerant comparison (see assert_tables_equivalent). Exact schema
    comparison is intentionally avoided because the transform's output schema varies with
    the pyarrow/pandas versions installed.
    """

    def test_transform(self):
        src_file_dir = os.path.abspath(os.path.dirname(__file__))
        input_dir = os.path.join(src_file_dir, "../test-data/input")
        expected_dir = os.path.join(src_file_dir, "../test-data/expected")
        input_tables = get_tables_in_folder(input_dir)
        expected_tables = get_tables_in_folder(expected_dir)

        transform = SimilarityTransform({ES_ENDPOINT_KEY: None})

        actual_tables = []
        for in_table in input_tables:
            table_list, _ = transform.transform(in_table)
            actual_tables.extend(table_list)
        flush_list, _ = transform.flush()
        actual_tables.extend(flush_list)

        assert len(actual_tables) == len(expected_tables), (
            f"Produced {len(actual_tables)} tables, expected {len(expected_tables)}"
        )
        for actual, expected in zip(actual_tables, expected_tables):
            assert_tables_equivalent(actual, expected)
