CODE_QUALITY_PARAMS = "code_quality"
import sys
from argparse import ArgumentParser, Namespace
from dpk_code_quality.transform import CodeQualityTransformConfiguration
from dpk_code_quality.transform import CodeQualityTransform
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

class CodeQualityConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name="code_quality", transform_class=CodeQualityTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--cq_contents_column_name",
            required=False,
            type=str,
            dest="contents_column_name",
            default="contents",
            help="Name of the column holds the data to process",
        )
        parser.add_argument(
            "--cq_language_column_name",
            required=False,
            type=str,
            dest="language_column_name",
            default="language",
            help="Name of the column holds the programming language details.",
        )
        parser.add_argument(
            "--cq_tokenizer",
            required=False,
            type=str,
            dest="tokenizer",
            default="codeparrot/codeparrot",
            help="Name or path to the tokenizer.",
        )
        parser.add_argument(
            "--cq_hf_token",
            required=False,
            type=str,
            dest="hf_token",
            default=None,
            help="Huggingface auth token to download and use the tokenizer.",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        dargs = vars(args)

        self.params = {
            CODE_QUALITY_PARAMS: {
                "contents_column_name": dargs.get("contents_column_name"),
                "language_column_name": dargs.get("language_column_name"),
                "tokenizer": dargs.get("tokenizer"),
                "hf_token": dargs.get("hf_token"),
            }
        }

        return True

class CodeQualityRuntime(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CodeQualityConfiguration())


class CodeQuality:
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
        launcher = PythonTransformLauncher(CodeQualityRuntime())
        return launcher.launch()
    

class CodeQualityPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CodeQualityTransformConfiguration())


if __name__ == "__main__":
    launcher = PythonTransformLauncher(CodeQualityPythonTransformConfiguration())
    launcher.launch()