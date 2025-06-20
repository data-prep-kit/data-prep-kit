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
import pyarrow.parquet as pq
from dpk_lang_id import LangIdentificationTransform
from dpk_doc_quality import DocQualityTransform
from data_processing.data_access import DataAccessLocal
from dpk_transform_chain import Orchestrator

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data"))

class TestTransformChain:
    def test_rep_removal(self):
        params = {"model_kind": "fasttext",
                  "model_url": "facebook/fasttext-language-identification",
                  "model_credential": os.environ.get('HF_READ_ACCESS_TOKEN', "PUT YOUR OWN HUGGINGFACE CREDENTIAL"),
                  "output_lang_column_name": "fasttext_dclm_oh_eli5_label",
                  "output_score_column_name": "fasttext_dclm_oh_eli5_prob",
                  "content_column_name": "text",
                  }

        lang_id = LangIdentificationTransform(params)

        dq = {"doc_content_column": "text",
              "bad_word_filepath": os.path.join(basedir,"ldnoobw", "en"),
              "text_lang": "en"

              }
        doc_quality = DocQualityTransform(dq)

        da_config = {
            "local_config": {
                "input_folder": os.path.join(basedir, "input"),
                "output_folder": os.path.join(basedir, "output"),
            },
            "files_to_use": [".parquet"]
        }

        data_access = DataAccessLocal(**da_config)

        orch = Orchestrator(
            data_access=data_access,
            transforms=[lang_id, doc_quality]
        )

        orch.run()

        table1 = pq.read_table(os.path.join(basedir, 'expected', 'test_01.parquet'))
        table2 = pq.read_table(os.path.join(basedir, 'output', 'test_01.parquet'))

        table3 = pq.read_table(os.path.join(basedir, 'expected', 'test_02.parquet'))
        table4 = pq.read_table(os.path.join(basedir, 'output', 'test_02.parquet'))

        table5 = pq.read_table(os.path.join(basedir, 'expected', 'test_03.parquet'))
        table6 = pq.read_table(os.path.join(basedir, 'output', 'test_03.parquet'))

        assert table1.equals(table2)
        assert table3.equals(table4)
        assert table5.equals(table6)