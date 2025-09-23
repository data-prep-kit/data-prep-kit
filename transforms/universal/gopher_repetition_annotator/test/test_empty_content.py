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
from dpk_gopher_repetition_annotator import GopherRepetitionAnnotatorTransform
import pyarrow as pa


def test_mytest():

    contents = pa.array(["Flamingo", "Horse", "Brittle stars", "", "Centipede"])
    urls = pa.array(['a.in', "abc.com", "test.org", "empty.com", "content.com"])


    table = pa.Table.from_arrays([contents, urls], names=["contents","url"])
    gra_transform = GopherRepetitionAnnotatorTransform(config={'contents_column_name': 'contents'})
    res_tables, metadata = gra_transform.transform(table=table)
    print(res_tables)
    assert res_tables[0]['dup_line_frac'][0].as_py() == 0.0
    assert res_tables[0]['dup_para_frac'][1].as_py() == 0.0
    assert res_tables[0]['dup_line_char_frac'][2].as_py() == 0.0
    assert res_tables[0]['dup_para_char_frac'][3].as_py() == -1.0
    assert res_tables[0]['dup_para_char_frac'][4].as_py() == 0
    assert metadata['total_docs'] == 5
