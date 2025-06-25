# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
HEADER_CLEANSER_PARAMS = "header_cleanser"
import sys
from argparse import ArgumentParser, Namespace
from dpk_header_cleanser.transform import HeaderCleanserTransformConfiguration
from dpk_header_cleanser.transform import HeaderCleanserTransform
from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
)

from data_processing.transform import TransformConfiguration
from data_processing.utils import ParamsUtils, CLIArgumentProvider, get_logger
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)

logger = get_logger(__name__)




class HeaderCleanserConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name="header_cleanser", transform_class=HeaderCleanserTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--header_cleanser_contents_column_name",
            required=False,
            type=str,
            dest="contents_column_name",
            default="contents",
            help="Name of the column holding the content to cleanse",
        )
        parser.add_argument(
            "--header_cleanser_document_id_column_name",
            required=False,
            type=str,
            dest="document_id_column_name",
            default="document_id",
            help="Name of the document ID column",
        )
        parser.add_argument(
            "--header_cleanser_license",
            required=False,
            type=bool,
            dest="license",
            default=True,
            help="Whether to remove license text",
        )
        parser.add_argument(
            "--header_cleanser_copyright",
            required=False,
            type=bool,
            dest="copyright",
            default=True,
            help="Whether to remove copyright text",
        )
        parser.add_argument(
            "--header_cleanser_timeout",
            required=False,
            type=int,
            dest="timeout",
            default=300,
            help="Timeout (in seconds) for each document's ScanCode run",
        )
        parser.add_argument(
            "--header_cleanser_skip_timeout",
            required=False,
            type=bool,
            dest="skip_timeout",
            default=False,
            help="Whether to skip documents that timeout",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        dargs = vars(args)
        self.params = {
            HEADER_CLEANSER_PARAMS: {
                "contents_column_name": dargs.get("contents_column_name"),
                "document_id_column_name": dargs.get("document_id_column_name"),
                "license": dargs.get("license"),
                "copyright": dargs.get("copyright"),
                "timeout": dargs.get("timeout"),
                "skip_timeout": dargs.get("skip_timeout"),
            }
        }
        return True

class HeaderCleanserRuntime(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=HeaderCleanserConfiguration())

class HeaderCleanser:
    def __init__(self, **kwargs):
        self.params = {k: v for k, v in kwargs.items()}
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(self.params)
        launcher = PythonTransformLauncher(HeaderCleanserRuntime())
        return launcher.launch()

 
class HeaderCleanserPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=HeaderCleanserTransformConfiguration())


if __name__ == "__main__":
    launcher = PythonTransformLauncher(HeaderCleanserPythonTransformConfiguration())
    launcher.launch()