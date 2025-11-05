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
import pyarrow
from data_processing.data_access import DataAccessLocal, DataAccessMemory, DataAccessFactory
from data_processing.utils import get_dpk_logger

logger = get_dpk_logger()

path = os.path.join(os.path.dirname(__file__), "../../../test-data/data_processing/input/")
def test_save_get_table():
    dal = DataAccessLocal({"input_folder": path, "output_folder": path})
    dam = DataAccessMemory()

    t, _ = dal.get_table(os.path.join(path, 'sample1.parquet'))

    assert len(dam.tables.keys()) == 0
    dam.save_table(os.path.join(path, 'sample1.parquet'), t)

    assert len(dam.tables.keys()) == 1

    assert type(dam.get_table((os.path.join(path, 'sample1.parquet')))[0]) == pyarrow.lib.Table
    assert dam.get_table((os.path.join(path, 'no_file.parquet')))[0] is None


def test_factory_instance():
    config = {"data_config": {"da_class": "data_processing.data_access.DataAccessMemory"},
              "data_checkpoint": False,
              }
    factory = DataAccessFactory()
    success = factory.apply_input_params(config)

    assert success

    da = factory.create_data_access()
    assert type(da) == DataAccessMemory
