# SPDX-License-Identifier: Apache-2.0

import json

import pyarrow.parquet as pq
import pytest
from dpk_folder2parquet.runtime import Folder2Parquet


@pytest.mark.parametrize("folder_name", ["plain", "reader's files", r"notes\text"])
def test_local_paths_preserved(tmp_path, folder_name):
    input_folder = tmp_path / folder_name / "input"
    output_folder = tmp_path / folder_name / "output"
    input_folder.mkdir(parents=True)
    (input_folder / "document.txt").write_text("An original document.", encoding="utf-8")

    result = Folder2Parquet(
        input_folder=str(input_folder),
        output_folder=str(output_folder),
        data_files_to_use=[".txt"],
    ).transform()

    assert result == 0
    output_files = list(output_folder.glob("*.parquet"))
    assert len(output_files) == 1
    assert pq.read_table(output_files[0])["binary_contents"].to_pylist() == [b"An original document."]
    metadata = json.loads((output_folder / "metadata.json").read_text())
    assert metadata["source"]["name"] == str(input_folder)
    assert metadata["target"]["name"] == str(output_folder)
