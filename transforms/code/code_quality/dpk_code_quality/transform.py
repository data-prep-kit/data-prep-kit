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
from typing import Any

import numpy as np
import pyarrow as pa
import sqlglot
from dpk_code_quality.code_complexity_metrics import create_complexity_metrics
from data_processing.utils import TransformUtils
from dpk_code_quality.transform_base import CodeQualityBaseTransform

from sqlglot import Dialects
from tree_sitter import Parser
from tree_sitter_languages import get_language

import tempfile
import subprocess


CODE_QUALITY_PARAMS = "code_quality_params"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Collection of code data specific annotations
# Inspired from:
# Codeparrot  https://github.com/huggingface/transformers/tree/main/examples/research_projects/codeparrot
# Starcoder https://github.com/bigcode-project/bigcode-dataset/tree/main/preprocessing

code_complexity_metrics_key = "code_complexity_metrics"
has_sqlglot_key = "has_sqlglot"
has_ast_key = "has_ast"
has_syntax_checker_bash_key = "has_syntax_checker_bash"
syntax_bash_path_key = "syntax_bash_path"
set_sqlglot_all_dialects_key = "set_sqlglot_all_dialects"
is_openshift_k8_yaml_key = "is_openshift_k8_yaml"
is_ansible_yaml_key = "is_ansible_yaml"

def traverse_tree (tree):
    cursor = tree.walk()
    visited_children = False
    while True:
        if not visited_children:
            yield cursor.node
            if not cursor.goto_first_child():
                visited_children = True
        elif cursor.goto_next_sibling():
            visited_children = False
        elif not cursor.goto_parent():
            break

def node_text(source, node):
    return source[node.start_byte:node.end_byte]

def bad_function_body (body):
    t = body.strip()
    if ((len(t) < 7) and \
        (len(t) == 0 or t == "pass" or t == "return")):
        return True
    return False

def find_empty_functions (script, traverse):
    discard = []
    good_function_flag = True
    for n in traverse:
        if (n.type == "function_definition"):
            body_node = n.child_by_field_name("body")
            body_text = node_text (script, body_node).decode('utf8')
            if (bad_function_body (body_text)):
                if (n.parent.type == "decorated_definition"):
                    good_function_flag = True
                else:
                    good_function_flag = False
    return good_function_flag

def ast_no_error(node):
    if True in [child.type == "ERROR" for child in node.children]:
        flag = False
    else:
        flag = True
    return flag


def has_ast(data, language):
    """
    Check if input code has valid ast, returns True/False
    """
    supported_languages = [
        "python",
        "java",
    ]
    
    '''
    supported_languages = [
        "python",
        "java",
        "javascript",
        "c",
        "cpp",
        "php",
        "c_sharp",
        "go",
        "sql",
        "typescript",
        "ruby",
        "rust",
    ]'''

    if language == "C++":
        arg_lang = "cpp"
    elif language == "C-sharp":
        arg_lang = "c_sharp"
    else:
        arg_lang = language.lower()

    try:
        if arg_lang in supported_languages:
           parser = Parser()
           lang = get_language(arg_lang)

           parser.set_language(lang)
           tree = parser.parse(data.encode())
           astflag = ast_no_error(tree.root_node)

           if astflag == True and arg_lang == 'python':
               try:
                   traverse = traverse_tree(tree)
                   badfunctionflag = find_empty_functions (data.encode('utf8'), traverse)
                   return badfunctionflag
               except Exception as e1:
                   print(f"Empty function check failed with exception: {e1}")
                   return astflag
           else:
               return  astflag
        
        else:
           return True
    except Exception as e2:
        print(f"ast parser failed with exception: {e2}")
        return True 


def add_code_complexity(data, lang):
    """
    Check if input code is python, get complexity metrics
    """
    try:
        if lang.lower() == "python":
            new_dict = create_complexity_metrics(data)
        else:
            new_dict = {}
    except:
        new_dict = {}

    return new_dict


def is_sqlglot_parseable(data, language, sqlglot_dialect_list):
    """
    Validate that the content is valid SQL using a parser.

    Only supoprts "sql" as language right now.

    :param data: The data as a string.
    :param language: The language as a string.
    :sqlglot_dialect_list: A list of strings specifying sqlglot dialtects.
    """
    if language.lower() == "sql":
        # Iterate over all set dialects
        for dialect in sqlglot_dialect_list:
            try:
                parsed_data_elements = sqlglot.parse(data, dialect=dialect)
                if len(parsed_data_elements) == 1 and parsed_data_elements[0] == None:
                    # Only a comment without SQL code
                    return False
                # Extracts the SQL statements
                _ = [element.sql() for element in parsed_data_elements if element is not None]
                return True
            except Exception:
                pass
    return True

def is_openshift_k8_yaml(content, language):
    if language.lower() == "unknown" or language.lower() == "yaml":
        if validation_tools.kubeconform_k8s_check(content) or validation_tools.kubeconform_openshift_check(content) or validation_tools.kubeconform_crd_check(content):
            return True
    return False

def syntax_checker_bash(data, language, tmp_dir):
    """
    Validate that the bash content is syntactically correct using shellcheck
    """
    if language.lower()=="shell" and data.startswith("#!") and ("bash" in data.split("\n")[0] or "/sh" in data.split("\n")[0]):
        try:
            # Write data to a temporary file.
            tmp = tempfile.NamedTemporaryFile(dir=tmp_dir)
            with open(tmp.name, 'w') as f:
                f.write(data)
            
            # Run shellcheck command
            cmd = f"shellcheck -e SC2068 {tmp.name}"
            try:
                output = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                tmp.close()
                if output.stderr=="" and '(error)' not in output.stdout:
                    return True 
                else:
                    return False
            except:
                tmp.close()      
                           
        except:
            return True
    return True

def is_ansible_yaml(content, language):
    if language.lower() == "unknown" or language.lower() == "yaml":
        if validation_tools.validate_ansible(content):
            return True
    return False

class CodeQualityTransform(CodeQualityBaseTransform):
    """
    Defines Code Quality specific annotation for code data. Some of the methods inspired from CodeParrot and StarCoder.
    """


    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Chain all preprocessing steps into one function to not fill cache.
        """
        table, metadata = super().transform(table, file_name)
        table = table[0]

        if not (
            self.code_quality[code_complexity_metrics_key]
            or self.code_quality[has_sqlglot_key]
            or self.code_quality[has_ast_key]
            or self.code_quality[has_syntax_checker_bash_key]
            or self.code_quality[is_openshift_k8_yaml_key]
            or self.code_quality[is_ansible_yaml_key]
        ):
            return [table], metadata

        contents = table.column(self.code_quality["contents_column_name"]).to_pylist()
        languages = table.column(self.code_quality["language_column_name"]).to_pylist()
        logical_loc = []
        halstead_volume = []
        cyclomatic_complexity = []
        percent_lines_of_comment = []
        maintanability_index = []
        is_sqlglot_parseable_values = []
        has_ast_values = []
        syntactic_correctness_bash = []
        is_openshift_k8_yaml_values = []
        is_ansible_yaml_values = []

        # loop over rows and compute filter stats
        if self.code_quality[code_complexity_metrics_key]:
            for c, l in zip(contents, languages):
                temp_dict = add_code_complexity(c, l)
                if temp_dict != {}:
                    logical_loc.append(temp_dict["logical_loc"])
                    halstead_volume.append(temp_dict["halstead_volume"])
                    cyclomatic_complexity.append(temp_dict["cyclomatic_complexity"])
                    percent_lines_of_comment.append(temp_dict["percent_lines_of_comment"])
                    maintanability_index.append(temp_dict["maintanability_index"])
                else:
                    logical_loc.append(-999)
                    halstead_volume.append(-999)
                    cyclomatic_complexity.append(-999)
                    percent_lines_of_comment.append(-999)
                    maintanability_index.append(-999)
            table = TransformUtils.add_column(table, "logical_loc", content=logical_loc)
            table = TransformUtils.add_column(table, "halstead_volume", content=halstead_volume)
            table = TransformUtils.add_column(table, "cyclomatic_complexity", content=cyclomatic_complexity)
            table = TransformUtils.add_column(table, "percent_lines_of_comment", content=percent_lines_of_comment)
            table = TransformUtils.add_column(table, "maintanability_index", content=maintanability_index)

        if self.code_quality[has_sqlglot_key]:
            sqlglot_dialect_list = [""]
            if self.code_quality[set_sqlglot_all_dialects_key]:
                sqlglot_dialect_list = list(Dialects)
            for c, l in zip(contents, languages):
                # compute lines statisticszw
                is_sqlglot_parseable_values.append(
                    is_sqlglot_parseable(c, l, sqlglot_dialect_list=sqlglot_dialect_list)
                )
            table = TransformUtils.add_column(table, "is_sqlglot_parseable", content=is_sqlglot_parseable_values)

        if self.code_quality[has_ast_key]:
            for c, l in zip(contents, languages):
                has_ast_values.append(has_ast(c, l))
            table = TransformUtils.add_column(table, "has_ast", content=has_ast_values)

        if self.code_quality[has_syntax_checker_bash_key]:
            for c, l in zip(contents, languages):
                syntactic_correctness_bash.append(syntax_checker_bash(c, l, self.code_quality[syntax_bash_path_key]))
            table = TransformUtils.add_column(table, "is_syntactically_correct_bash", content=syntactic_correctness_bash)
            
        if self.code_quality[is_openshift_k8_yaml_key]:
            for c, l in zip(contents, languages):
                is_openshift_k8_yaml_values.append(is_openshift_k8_yaml(c, l))
            table = TransformUtils.add_column(table, "is_openshift_k8_yaml", content=is_openshift_k8_yaml_values)
        
        if self.code_quality[is_ansible_yaml_key]:
            for c, l in zip(contents, languages):
                is_ansible_yaml_values.append(is_ansible_yaml(c, l))
            table = TransformUtils.add_column(table, "is_ansible_yaml", content=is_ansible_yaml_values)
        
        return [table], {}

