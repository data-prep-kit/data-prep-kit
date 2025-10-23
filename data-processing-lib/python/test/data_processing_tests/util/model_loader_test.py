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
from pathlib import Path
from transformers import AutoTokenizer
from data_processing.utils import get_dpk_logger
from data_processing.utils import load_model

logger = get_dpk_logger()


def test_load_hf():
    hf_repo = 'bigcode/starcoder'
    t = load_model(hf_repo, 'tokenizer')

    assert t.vocab_size == 49152
    assert t.name_or_path == hf_repo


def test_load_local():
    hf_repo = 'bigcode/starcoder'
    tokenizer = AutoTokenizer.from_pretrained(hf_repo)

    with tempfile.TemporaryDirectory() as temp_dir_path:
        tokenizer.save_pretrained(temp_dir_path)

        t = load_model(temp_dir_path, 'tokenizer')
        assert t.vocab_size == 49152
        assert t.name_or_path == temp_dir_path


def test_load_s3(s3_url):
    t = load_model(s3_url, 'tokenizer')

    assert t.vocab_size == 49152
