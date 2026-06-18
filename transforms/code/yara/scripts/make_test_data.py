#!/usr/bin/env python3
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
#
# Regenerate test-data/input/sample.parquet and test-data/expected/sample.parquet
# used by test_yara_python.py / test_yara_ray.py. Run from the transform root:
#
#   python scripts/make_test_data.py
#
# Requires pyarrow (already a DPK dependency).

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
BENIGN = b"hello world"


def main() -> None:
    here = Path(__file__).resolve().parent.parent
    input_dir = here / "test-data" / "input"
    expected_dir = here / "test-data" / "expected"
    input_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)

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

    pq.write_table(input_table, input_dir / "sample.parquet")
    pq.write_table(expected_table, expected_dir / "sample.parquet")
    print(f"wrote {input_dir / 'sample.parquet'}")
    print(f"wrote {expected_dir / 'sample.parquet'}")

    # AbstractTransformLauncherTest compares output vs expected by directory
    # contents; the launcher always writes metadata.json, so expected/ must
    # contain one too. Content diffs in metadata.json are explicitly ignored
    # (abstract_test.py:213), so a stub is sufficient.
    metadata_path = expected_dir / "metadata.json"
    if not metadata_path.exists():
        metadata_path.write_text(json.dumps({"_stub": "ignored by test framework"}) + "\n")
        print(f"wrote {metadata_path}")


if __name__ == "__main__":
    main()
