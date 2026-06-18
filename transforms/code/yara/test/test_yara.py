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

import os
from typing import Tuple

import pyarrow as pa
from data_processing.test_support.transform.table_transform_test import (
    AbstractTableTransformTest,
)
from dpk_yara.transform import YaraTransform


EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
BENIGN = b"hello world"

TEST_RULES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-rules"))

input_table = pa.table(
    {
        "file_name": pa.array(["benign.txt", "eicar.txt"]),
        "binary_contents": pa.array([BENIGN, EICAR], type=pa.binary()),
    }
)
expected_table = pa.table(
    {
        "file_name": pa.array(["benign.txt", "eicar.txt"]),
        "binary_contents": pa.array([BENIGN, EICAR], type=pa.binary()),
        "yara_matched": pa.array([False, True], type=pa.bool_()),
        "yara_rules": pa.array([[], ["EICAR_Test_String"]], type=pa.list_(pa.string())),
        "yara_tags": pa.array([[], []], type=pa.list_(pa.string())),
        "yara_categories": pa.array([[], ["eicar"]], type=pa.list_(pa.string())),
    }
)
# Metadata is asserted exactly (AbstractTableTransformTest compares the full
# dict). These per-rule / per-category keys (rule_*, docs_infected_by_*) are
# stable here because this test compiles only the local test-rules/ directory
# (one EICAR rule in category "eicar"), not the image's full ruleset.
expected_metadata_list = [
    {
        "total_docs": 2,
        "docs_clean": 1,
        "docs_infected": 1,
        "total_rule_hits": 1,
        "unique_rules_matched": 1,
        "docs_infected_by_eicar": 1,
        "rule_EICAR_Test_String": 1,
    },
    {},
]


class TestYaraTransform(AbstractTableTransformTest):
    def get_test_transform_fixtures(self) -> list[Tuple]:
        return [
            (
                YaraTransform({"yara_rules_dir": TEST_RULES_DIR}),
                [input_table],
                [expected_table],
                expected_metadata_list,
            ),
        ]
