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

COMMENT_CLEANSER_PARAMS = "comment_cleanser"
import sys
from argparse import ArgumentParser, Namespace
from dpk_comment_cleanser.transform import CommentCleanserTransformConfiguration
from dpk_comment_cleanser.transform import CommentCleanserTransform
from data_processing.runtime.pure_python import (
    PythonTransformLauncher,
    PythonTransformRuntimeConfiguration,
)

from data_processing.transform import TransformConfiguration
from data_processing.utils import ParamsUtils, get_logger
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)

logger = get_logger(__name__)


class CommentCleanserConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name="comment_cleanser", transform_class=CommentCleanserTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--comment_cleanser_contents_column_name",
            required=False,
            type=str,
            dest="contents_column_name",
            default="contents",
            help="Name of the column holds the data to process",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        dargs = vars(args)

        self.params = {
            COMMENT_CLEANSER_PARAMS: {
                "contents_column_name": dargs.get("contents_column_name"),
            }
        }

        return True

class CommentCleanserRuntime(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CommentCleanserConfiguration())


class CommentCleanser:
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
        launcher = PythonTransformLauncher(CommentCleanserRuntime())
        return launcher.launch()
    

class CommentCleanserPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CommentCleanserTransformConfiguration())


if __name__ == "__main__":
    launcher = PythonTransformLauncher(CommentCleanserPythonTransformConfiguration())
    launcher.launch()