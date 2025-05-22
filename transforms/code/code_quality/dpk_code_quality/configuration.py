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

from argparse import ArgumentParser, Namespace

from data_processing.utils import str2bool
from data_processing.transform import TransformConfiguration
from dpk_code_quality.transform_base import CODE_QUALITY_PARAMS
from dpk_code_quality.transform import (
    CodeQualityTransform, 
    code_complexity_metrics_key,
    has_sqlglot_key,
    has_ast_key,
    has_syntax_checker_bash_key,
    syntax_bash_path_key,
    set_sqlglot_all_dialects_key,
    is_openshift_k8_yaml_key,
    is_ansible_yaml_key
 )

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
        parser.add_argument(
            "--cq_calculate_complexity",
            required=False,
            type = lambda x: bool(str2bool(x)),
            dest="calculate_complexity",
            default=False,
            help="Boolean field to compute python complexity metrics only",
        )
        parser.add_argument(
            "--cq_has_ast",
            required=False,
            type = lambda x: bool(str2bool(x)),
            dest="has_ast_status",
            default=False,
            help="Option to enable code syntax validation using ast parser",
        )
        parser.add_argument(
            "--cq_sqlglot",
            required=False,
            type = lambda x: bool(str2bool(x)),
            dest="has_sqlglot",
            default=False,
            help="Option to enable SQL code validation",
        )
        parser.add_argument(
            "--cq_check_syntax_bash",
            required=False,
            type=lambda x: ast.literal_eval,
            dest="check_syntax_bash",
            default=False,
            help="Option to enable Bash syntax checking",
        )
        parser.add_argument(
            "--cq_syntax_bash_tmp_path",
            required=False,
            type=str,
            dest="syntax_bash_tmp_path",
            default='/tmp',
            help="Path to temperory save directory",
        )
        parser.add_argument(
            "--cq_sqlglot_all_dialects",
            required=False,
            type=lambda x: bool(str2bool(x)),
            dest="set_sqlglot_all_dialects",
            default=False,
            help="If set tries to parse with all possible sqlglot dialects",
        )
        parser.add_argument(
            "--cq_is_openshift_k8_yaml",
            required=False,
            type=lambda x: bool(str2bool(x)),
            dest="is_openshift_k8_yaml",
            default=False,
            help="If set tries to check if openshift/k8s yaml",
        )
        parser.add_argument(
            "--cq_is_ansible_yaml",
            required=False,
            type=lambda x: bool(str2bool(x)),
            dest="is_ansible_yaml",
            default=False,
            help="If set tries to check if ansible yaml",
        )


    def apply_input_params(self, args: Namespace) -> bool:
        dargs = vars(args)

        self.params = {
            CODE_QUALITY_PARAMS: {
                "contents_column_name": dargs.get("contents_column_name"),
                "language_column_name": dargs.get("language_column_name"),
                "tokenizer": dargs.get("tokenizer"),
                "hf_token": dargs.get("hf_token"),
                code_complexity_metrics_key: dargs.get("calculate_complexity"),
                has_ast_key: dargs.get("has_ast_status"),
                has_sqlglot_key: dargs.get("has_sqlglot"),
                has_syntax_checker_bash_key: dargs.get("check_syntax_bash"),
                syntax_bash_path_key: dargs.get("syntax_bash_tmp_path"),
                set_sqlglot_all_dialects_key: dargs.get("set_sqlglot_all_dialects"),
                is_openshift_k8_yaml_key: dargs.get("is_openshift_k8_yaml"),
                is_ansible_yaml_key: dargs.get("is_ansible_yaml")
            }
        }


        return True