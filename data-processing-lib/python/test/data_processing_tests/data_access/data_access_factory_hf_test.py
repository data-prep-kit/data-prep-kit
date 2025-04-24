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

import sys
from argparse import ArgumentParser

from data_processing.data_access import DataAccessFactory, DataAccessHF
from data_processing.utils import ParamsUtils


def test_creating_hf_data_access():
    """
    Testing creation of HF data access
    :return: None
    """
    input_folder = "datasets/blublinsky/test/data"
    output_folder = "datasets/blublinsky/test/temp"
    hf_token = "token"
    hf_conf = {
        "hf_token": hf_token,
        "input_folder": input_folder,
        "output_folder": output_folder,
    }
    params = {}
    params["data_hf_config"] = hf_conf
    params["data_num_samples"] = 3
    params["data_data_sets"] = ["ds1"]
    params["data_files_to_use"] = [".nothere"]

    # Set the simulated command line args
    sys.argv = ParamsUtils.dict_to_req(params)
    daf = DataAccessFactory()
    parser = ArgumentParser()
    daf.add_input_params(parser)
    args = parser.parse_args()
    daf.apply_input_params(args)

    # create data_access
    data_access = daf.create_data_access()

    # validate created data access
    assert isinstance(data_access, DataAccessHF)
    assert data_access.input_folder == input_folder
    assert data_access.output_folder == output_folder
    assert data_access.fs.token == hf_token

    assert data_access.n_samples == 3
    assert data_access.d_sets == ["ds1"]
    assert data_access.files_to_use == [".nothere"]


