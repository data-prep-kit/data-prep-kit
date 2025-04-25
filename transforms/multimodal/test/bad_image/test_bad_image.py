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
import pyarrow as pa

from data_processing.test_support.transform.table_transform_test import (
    AbstractTableTransformTest,
)
from data_processing.test_support import get_tables_in_folder

from dpk_mm.bad_image.transform import bad_indexes_key, BadIndexTransform
from data_processing.utils import TransformUtils

class TestProtoTransform:
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """
    def _get_indexed_rows(self, table:pa.Table, to_keep:list[int]) -> pa.Table:

        orig_rows = table.num_rows
        table = table.take(to_keep)
        assert table.num_rows == len(to_keep)
        return table

    def _run_test(self, input_table:pa.Table, error_indexes:list[int], expected_rows:list[int]):
        config = {bad_indexes_key : error_indexes}
        transform = BadIndexTransform(config)
        expected = self._get_indexed_rows(input_table, expected_rows)
        output_list, metadata = transform.transform(input_table,"foo.parquet")
        output_table = output_list[0]
        output_table.drop_columns(["dummy"])
        assert output_table.num_rows == expected.num_rows
        # print(f"{input_table}")
        # print(f"expected index {expected.column('index')}")
        # print(f"output_index {output_table.column('index')}")
        e_ids = expected.column("index").to_pylist()
        o_ids = output_table.column("index").to_pylist()
        print (e_ids)
        print (o_ids)
        assert e_ids == o_ids

        nremoved = input_table.num_rows - len(expected_rows)
        assert nremoved == metadata["removed-row-count"]

    def test_erroring_rows(self) -> list[tuple]:
        test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test-data"))
        input_dir = os.path.join(test_data_dir, "bad_image/input")
        input_tables = get_tables_in_folder(input_dir)
        input_table = input_tables[0]

        # Tests below based on this
        # Expecting 0 images in first row, 2 images in 2nd row, 1 image in 3rd row
        # Row 0 has no images
        # Row 1 has image with indexes 0 and 1
        # Row 2 has image with index 2
        assert input_table.num_rows == 3

        # Add index column for use in row tracking.
        index = []
        for i in range(input_table.num_rows):
            index.append(i)
        input_table = TransformUtils.add_column(input_table, "index", index)

        # Fail on no images should leave all rows
        erroring_image_indexes = [ ]
        expected_rows = [ 0, 1, 2 ]     # rows with 0 images are passed through with dummy annotations
        self._run_test(input_table, erroring_image_indexes, expected_rows)

        # Fail on 1st image in row 1 should leave rows 0 and 2
        erroring_image_indexes = [ 0 ]
        expected_rows = [ 0, 2 ]

        # Fail on 2nd image in row 1 should leave rows 0 and 2
        self._run_test(input_table, erroring_image_indexes, expected_rows)
        erroring_image_indexes = [ 1 ]
        expected_rows = [ 0, 2 ]
        self._run_test(input_table, erroring_image_indexes, expected_rows)

        # Fail on 1st image in row 1 and image in row 2 should leave row 0
        erroring_image_indexes = [ 0, 2 ]
        expected_rows = [ 0 ]

        # Fail on 2nd image in row 1 and image in row 2 should leave row 0
        self._run_test(input_table, erroring_image_indexes, expected_rows)
        erroring_image_indexes = [ 1, 2 ]
        expected_rows = [ 0 ]
        self._run_test(input_table, erroring_image_indexes, expected_rows)

        # Fail on image in row 2 should leave row 0 and 1
        erroring_image_indexes = [ 2 ]
        expected_rows = [ 0, 1 ]
        self._run_test(input_table, erroring_image_indexes, expected_rows)


