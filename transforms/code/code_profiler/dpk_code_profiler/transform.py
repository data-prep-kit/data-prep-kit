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

import atexit
import json
import os
import shutil
import subprocess
import uuid
from argparse import ArgumentParser, Namespace
from typing import Any
from sentence_transformers import SentenceTransformer, util
import numpy as np
import pandas as pd

import pyarrow as pa
from data_processing.transform import (
    AbstractBinaryTransform,
    AbstractTableTransform,
    TransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider, get_logger
from dpk_code_profiler.higher_order_concepts import *
from dpk_code_profiler.profiler_report import *
from dpk_code_profiler.semantic_concepts import *
from tree_sitter import Language
from tree_sitter import Parser as TSParser
from tree_sitter_languages import get_language
from dpk_code_profiler.UAST_parser import UASTParser, uast_read


short_name = "CodeProfiler"
cli_prefix = f"{short_name}_"
language = "programming_language"
contents = "contents"


class CodeProfilerTransform(AbstractTableTransform):
    """
    Implements a simple copy of a pyarrow Table.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        """

        super().__init__(config)

        self.contents = self.config.get("contents", "contents")
        self.language = self.config.get("programming_language", "programming_language")

        if not isinstance(self.contents, str):
            raise ValueError(f"'contents' should be a string, got {type(self.contents).__name__}")

        def ensure_tree_sitter_bindings():
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Generate a unique directory for the bindings based on a UUID
            bindings_dir = os.path.join(script_dir, f"tree-sitter-bindings-{uuid.uuid4()}")
            # Clone the bindings only if the unique directory does not exist
            if not os.path.exists(bindings_dir):
                print(f"Cloning tree-sitter bindings into {bindings_dir}...")
                result = subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/pankajskku/tree-sitter-bindings.git",
                        bindings_dir,
                    ]
                )
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to clone tree-sitter bindings into {bindings_dir}")
                return bindings_dir

        # Call this function before the main code execution
        self.bindings_dir = ensure_tree_sitter_bindings()

        # Use the correct architecture for runtime
        RUNTIME_HOST_ARCH = os.environ.get("RUNTIME_HOST_ARCH", "x86_64")
        self.extract_comments = os.environ.get("EXTRACT_COMMENTS", "false").lower() == "true"

        bindings_path = self.bindings_dir + "/" + RUNTIME_HOST_ARCH  # for MAC: mach-arm64
        print(f"Bindings bindings_dir: {self.bindings_dir}")
        print(f"Bindings path: {bindings_path}")

        # Check if the bindings path exists
        if not os.path.exists(bindings_path):
            raise FileNotFoundError(f"Bindings path does not exist: {bindings_path}")

        try:
            AGDA_LANGUAGE = Language(os.path.join(bindings_path, "agda-bindings.so"), "agda")
            C_LANGUAGE = get_language("c")
            CPP_LANGUAGE = get_language("cpp")
            CSHARP_LANGUAGE = Language(os.path.join(bindings_path, "c_sharp-bindings.so"), "c_sharp")
            D_LANGUAGE = Language(os.path.join(bindings_path, "d-bindings.so"), "d")
            DART_LANGUAGE = Language(os.path.join(bindings_path, "dart-bindings.so"), "dart")
            ELM_LANGUAGE = Language(os.path.join(bindings_path, "elm-bindings.so"), "elm")
            GOLANG_LANGUAGE = Language(os.path.join(bindings_path, "go-bindings.so"), "go")
            HASKELL_LANGUAGE = Language(os.path.join(bindings_path, "haskell-bindings.so"), "haskell")
            JAVA_LANGUAGE = get_language("java")
            JAVASCRIPT_LANGUAGE = Language(os.path.join(bindings_path, "js-bindings.so"), "javascript")
            KOTLIN_LANGUAGE = Language(os.path.join(bindings_path, "kotlin-bindings.so"), "kotlin")
            NIM_LANGUAGE = Language(os.path.join(bindings_path, "nim-bindings.so"), "nim")
            # OBJECTIVE_C_LANGUAGE = Language(os.path.join(bindings_path, 'objc-bindings.so'), 'objc')
            OCAML_LANGUAGE = get_language("ocaml")
            PERL_LANGUAGE = get_language("perl")
            PY_LANGUAGE = get_language("python")
            QMLJS_LANGUAGE = Language(os.path.join(bindings_path, "qmljs-bindings.so"), "qmljs")
            RUST_LANGUAGE = get_language("rust")
            SCALA_LANGUAGE = Language(os.path.join(bindings_path, "scala-bindings.so"), "scala")
            TYPESCRIPT_LANGUAGE = get_language("typescript")
        except Exception as e:
            self.clean_bindings()
            raise Exception("Bindings are not loaded", e)

        self.clean_bindings()

        # Language map for supported languages
        self.language_map = {
            "Agda": AGDA_LANGUAGE,
            "C": C_LANGUAGE,
            "C#": CSHARP_LANGUAGE,
            "Csharp": CSHARP_LANGUAGE,
            "Cpp": CPP_LANGUAGE,
            "D": D_LANGUAGE,
            "Dart": DART_LANGUAGE,
            "Elm": ELM_LANGUAGE,
            "Go": GOLANG_LANGUAGE,
            "Haskell": HASKELL_LANGUAGE,
            "Java": JAVA_LANGUAGE,
            "JavaScript": JAVASCRIPT_LANGUAGE,
            "Kotlin": KOTLIN_LANGUAGE,
            "Nim": NIM_LANGUAGE,
            "Ocaml": OCAML_LANGUAGE,
            # "Objective-C": OBJECTIVE_C_LANGUAGE,
            "Perl": PERL_LANGUAGE,
            "Python": PY_LANGUAGE,
            "Qmljs": QMLJS_LANGUAGE,
            "Rust": RUST_LANGUAGE,
            "Scala": SCALA_LANGUAGE,
            "TypeScript": TYPESCRIPT_LANGUAGE,
        }
        self.uast_language_map = {
            "Agda": "agda",
            "C": "c",
            "C#": "c_sharp",
            "Csharp": "c_sharp",
            "C++": "cpp",
            "Cpp": "cpp",
            "D": "d",
            "Dart": "dart",
            "Elm": "elm",
            "Go": "go",
            "Haskell": "haskell",
            "Java": "java",
            "JavaScript": "js",
            "Kotlin": "kotlin",
            "Nim": "nim",
            "Ocaml": "ocaml",
            # "Objective-C": 'objc',
            "Perl": "perl",
            "Python": "py",
            "Qmljs": "qmljs",
            "Rust": "rust",
            "Scala": "scala",
            "TypeScript": "typescript",
        }
        self.logger = get_logger(__name__)
        self.ruleset_file = os.path.dirname(os.path.abspath(__file__))

        # Semantic profiling related inits
        self.ikb_file = config.get("ikb_file", "semantic-ruleset/ikb_model.csv")
        self.null_libs_file = config.get("null_libs_file", "semantic-ruleset/null_libs.csv")
        self.comments_concepts_file = config.get("comments_concepts_file", "semantic-ruleset/comments_concepts.csv")

        src_file_dir = os.path.abspath(os.path.dirname(__file__))
        # Check if the file exists; if not, update the default path
        if not os.path.exists(self.ikb_file):
            print(f"File not found at {self.ikb_file}. Updating to '../semantic-ruleset/ikb_model.csv'")
            self.ikb_file = os.path.join(src_file_dir, "semantic-ruleset/ikb_model.csv")
        # Raise an error if the file still doesn't exist
        if not os.path.exists(self.ikb_file):
            raise FileNotFoundError(f"File not found: {self.ikb_file}")

        # Check if the file exists; if not, update the default path
        if not os.path.exists(self.null_libs_file):
            print(f"File not found at {self.null_libs_file}. Updating to '../semantic-ruleset/null_libs.csv'")
            self.null_libs_file = os.path.join(src_file_dir, "semantic-ruleset/null_libs.csv")
        # Raise an error if the file still doesn't exist
        if not os.path.exists(self.null_libs_file):
            raise FileNotFoundError(f"File not found: {self.null_libs_file}")

        # Check if the file exists; if not, update the default path
        if not os.path.exists(self.comments_concepts_file):
            print(f"File not found at {self.comments_concepts_file}. Updating to '../semantic-ruleset/comments_concepts.csv'")
            self.comments_concepts_file = os.path.join(src_file_dir, "semantic-ruleset/comments_concepts.csv")
        # Raise an error if the file still doesn't exist
        if not os.path.exists(self.comments_concepts_file):
            raise FileNotFoundError(f"File not found: {self.comments_concepts_file}")

        # Higher order semantic features
        self.metrics_list = config.get("metrics_list", ["ccr", "code_snippet_len", "avg_fn_len_in_snippet"])

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Extracts the syntactic constructs
        """
        print("Transforming the the input dataframe")

        ts_parser = TSParser()
        uast_parser = UASTParser()

        def get_uast_json(code, lang):
            # Create case-insensitive mappings
            language_map_lower = {key.lower(): value for key, value in self.language_map.items()}
            uast_language_map_lower = {key.lower(): value for key, value in self.uast_language_map.items()}

            # Check for the lowercase version of `lang`
            lang_lower = lang.lower()
            if lang_lower in language_map_lower:
                ts_parser.set_language(language_map_lower[lang_lower])
                uast_parser.set_language(uast_language_map_lower[lang_lower])
                ast = ts_parser.parse(bytes(code, encoding="utf8"))
                uast = uast_parser.parse(ast, code)
                return uast.get_json()
            return None

        def extract_syntactic_constructs_from_uast(uast_json):
            """Extract package names from the UAST JSON where node_type is 'uast_package'."""
            package_list = []
            comments_list = []

            try:
                uast_data = json.loads(uast_json)
                if uast_data is not None:
                    nodes = uast_data.get("nodes", {})
                else:
                    nodes = {}
                    print("Warning: uast_data is None. Check the data source or initialization process.")
                    return "", ""
                # Iterate through nodes to find nodes with type 'uast_package'
                for node_id, node_data in nodes.items():
                    if node_data.get("node_type") == "uast_package":
                        # Extract the package name from the 'code_snippet' (after 'uast_package ')
                        package_name = node_data["code_snippet"].split(" ")[1]
                        package_list.append(package_name)                
                    if node_data.get("node_type") == "uast_comment":
                        # Extract the package name from the 'code_snippet' (after 'uast_package ')
                        comment_content = node_data["code_snippet"].split("uast_comment ")[1]
                        comments_list.append(comment_content)

            except json.JSONDecodeError as e:
                print(f"Failed to parse UAST JSON: {e}")
                return "", ""

            return ",".join(package_list), ",".join(comments_list)  # Return as a comma-separated string

        def assign_concept_comments(comments_lists):
            # Extract comments from the UAST column
            import pandas as pd
            comment_rows = []
            for idx, comment_str in enumerate(comments_lists):
                if comment_str:  # non-empty string
                    for comment in comment_str.split(","):
                        clean_comment = comment.strip()
                        # print(f"Comment: {clean_comment}")
                        if len(clean_comment.split()) >= 3:
                            comment_rows.append((idx, clean_comment))
                            # print(f"Comment: {clean_comment}")
            # Create the exploded comment dataframe
            comments_df = pd.DataFrame(comment_rows, columns=["index", "comment"])

            # Embed concept summaries once and save
            concepts_df = pd.read_csv(self.comments_concepts_file)
            model = SentenceTransformer('all-MiniLM-L6-v2')
            concept_embeddings = model.encode(concepts_df['Concept Summary'].tolist(), convert_to_tensor=True)

            # Embed comments and map to concept labels
            def map_comments_to_concepts(comments, concept_embeddings, concepts_df):
                comment_embeddings = model.encode(comments, convert_to_tensor=True)
                cosine_scores = util.cos_sim(comment_embeddings, concept_embeddings)
                top_matches = np.argmax(cosine_scores.cpu().numpy(), axis=1)
                labels = concepts_df['Concept Label'].iloc[top_matches].tolist()
                return labels

            # Assuming you have comments_df ready from earlier step:
            comments = comments_df['comment'].tolist()
            comments_df['comment_concepts'] = map_comments_to_concepts(comments, concept_embeddings, concepts_df)

            # Print each comment and its assigned concept
            for comment, label in zip(comments_df['comment'], comments_df['comment_concepts']):
                print(f"{comment:<60} --> {label}")
            
            return comments_df

        def get_uast_parquet(tmp_table):
            # df = pd.read_parquet(f'{db_path}/{filename}', 'pyarrow')
            # df = df.reindex(columns=all_columns)

            # Extract language and content arrays from the table using PyArrow
            print(self.language)
            lang_array = tmp_table.column(self.language)
            content_array = tmp_table.column(self.contents)
            # Ensure both arrays have the same length
            assert len(lang_array) == len(content_array)

            # Generate UASTs using a list comprehension
            uasts = [
                json.dumps(get_uast_json(content_array[i].as_py(), lang_array[i].as_py()))
                for i in range(len(content_array))
            ]
            # Extract package lists from the UAST column
            results = [extract_syntactic_constructs_from_uast(uast) for uast in uasts]
            package_lists, comments_lists = zip(*results)
            # print("###### pankaj: ", self.extract_comments)

            # Add the UAST array as a new column in the PyArrow table
            uast_column = pa.array(uasts)
            package_list_column = pa.array(package_lists)

            tmp_table_with_uast = tmp_table.append_column("uast", uast_column)
            # Add the uast_package column
            table_with_package_list = tmp_table_with_uast.append_column("uast_package_list", package_list_column)
        
            comment_concepts_df = assign_concept_comments(comments_lists)
            # Group by snippet index, get all unique concept labels as a comma-separated string
            multi_concepts = (
                comment_concepts_df
                .groupby("index")["comment_concepts"]
                .apply(lambda x: ", ".join(sorted(set(x))))
                .reindex(range(len(comments_lists)), fill_value="Unknown")
                .tolist()
            )

            # Convert to PyArrow array and append
            comments_semantic_column = pa.array([str(x) for x in multi_concepts])
            table_with_package_list = table_with_package_list.append_column("comments_semantic_concept", comments_semantic_column)            
            return table_with_package_list

        table_with_uast = get_uast_parquet(table)

        ## Semantic profiling
        self.logger.debug(f"Semantic profiling of one table with {len(table_with_uast)} rows")

        # Load Knowledge Base
        print(self.ikb_file)
        print(self.null_libs_file)
        ikb = knowledge_base(self.ikb_file, self.null_libs_file)
        ikb.load_ikb_trie()

        # Extract concept from IKB
        libraries = table_with_uast.column("uast_package_list").to_pylist()
        language = table_with_uast.column("programming_language").to_pylist()
        concepts = [concept_extractor(lib, lang, ikb) for lib, lang in zip(libraries, language)]

        # Append concepts column to table and record unknown libraries
        new_col = pa.array(concepts)
        table_with_uast = table_with_uast.append_column("concepts", new_col)
        ikb.write_null_files()

        # Higher order syntactic profiler
        self.logger.debug(f"Transforming one table with {len(table_with_uast)} rows")

        if self.metrics_list is not None:
            uasts = [uast_read(uast_json) for uast_json in table_with_uast["uast"].to_pylist()]
            ccrs = []
            code_snippet_len = []
            avg_fn_len_in_snippet = []

            for uast in uasts:
                if "ccr" in self.metrics_list:
                    ccrs.append(extract_ccr(uast))
                if "code_snippet_len" in self.metrics_list:
                    code_snippet_len.append(extract_code_snippet_length(uast))
                if "avg_fn_len_in_snippet" in self.metrics_list:
                    avg_fn_len_in_snippet.append(extract_code_avg_fn_len_in_snippet(uast))

            if "ccr" in self.metrics_list:
                table_with_uast = table_with_uast.append_column("ccr", pa.array(ccrs))
            if "code_snippet_len" in self.metrics_list:
                table_with_uast = table_with_uast.append_column("code_snippet_len", pa.array(code_snippet_len))
            if "avg_fn_len_in_snippet" in self.metrics_list:
                table_with_uast = table_with_uast.append_column(
                    "avg_fn_len_in_snippet", pa.array(avg_fn_len_in_snippet)
                )

        self.logger.debug(f"Transformed one table with {len(table_with_uast)} rows")
        metadata = {"nfiles": 1, "nrows": len(table_with_uast)}
        # Report generation
        if "uast" in table_with_uast.schema.names and "concepts" in table_with_uast.schema.names:
            generate_report(table_with_uast, self.metrics_list)

        # Add some sample metadata.
        self.logger.debug(f"Transformed one table with {len(table_with_uast)} rows")
        # report statistics
        stats = {
            "source_documents": table.num_columns,
            "result_documents": table_with_uast.num_columns,
        }
        return [table_with_uast], stats

    def clean_bindings(self):
        try:
            # Use an OS command to remove the folder and its contents
            subprocess.run(["rm", "-rf", self.bindings_dir], check=True)
            print(f"Successfully deleted: {self.bindings_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting {self.bindings_dir}: {e}")


class CodeProfilerTransformConfiguration(TransformConfiguration):
    def __init__(self, transform_class: type[AbstractBinaryTransform] = CodeProfilerTransform):
        super().__init__(
            name=short_name,
            transform_class=transform_class,
        )

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            f"--{language}",
            type=str,
            default="programming_language",
            help="Column name that denotes the programming language",
        )
        parser.add_argument(
            f"--{contents}",
            type=str,
            default="contents",
            help="Column name that contains code snippets",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = captured
        return True
