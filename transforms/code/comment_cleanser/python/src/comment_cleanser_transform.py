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

import concurrent.futures
from functools import partial
import logging
import math
import multiprocessing
import os
from argparse import ArgumentParser, Namespace
from typing import Any
import warnings

import pyarrow as pa
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,
)
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, get_logger, str2bool
import timeout_timer
from joblib import load
import comment_parser.comment_parser as cmp


logger = get_logger(__name__)
logging.getLogger('bs4').setLevel(logging.ERROR)
logging.getLogger('timeout_timer').setLevel(logging.ERROR)
warnings.simplefilter('ignore', DeprecationWarning)

short_name = "comment_cleanser"
cli_prefix = short_name + "_"
COLUMN_KEY = "contents_column_name"
DEFAULT_DOCUMENT_ID_COLUMN = "doc_id_column_name"
DOCUMENT_ID_COLUMN_KEY = "document_id_column_name"
N_PROCESSES_KEY = "n_processes"
TIMEOUT_KEY = "timeout"
SKIP_TIMEOUT_KEY = "skip_timeout"

column_cli_params = f"{cli_prefix}{COLUMN_KEY}"
document_id_column_cli_params = f"{cli_prefix}{DOCUMENT_ID_COLUMN_KEY}"
n_processes_cli_params = f"{cli_prefix}{N_PROCESSES_KEY}"
timeout_cli_params = f"{cli_prefix}{TIMEOUT_KEY}"
skip_timeout_cli_params = f"{cli_prefix}{SKIP_TIMEOUT_KEY}"

DEFAULT_COLUMN = "contents"
DEFAULT_DOCUMENT_ID_COLUMN = "document_id"
DEFAULT_LICENSE = True
DEFAULT_COPYRIGHT = True
DEFAULT_N_PROCESSES = 5
DEFAULT_TIMEOUT = 300
DEFAULT_SKIP_TIMEOUT = False
DEFAULT_CHUNK_SIZE = os.getenv("DEFAULT_CHUNK_SIZE", 100)

EXTENSION_MIME_MAP = [
    "application/javascript",
    "text/html",
    "text/x-c",
    "text/x-c++",
    "text/x-c++",
    "text/x-go",
    "text/x-java",
    "text/x-python",
    "text/x-ruby",
    "text/x-shellscript",
    "text/xml"
]

def code_comment_index(code):
    # basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/"))
    # model = load(os.path.join(basedir,'input/clf_tfid_char_300k_clean.joblib'))
    # model = load(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test-data/input/clf_tfid_char_300k_clean.joblib")))
    model = load(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../model/clf_tfid_char.joblib")))
    comments = []
    code_comment_lines = []
    try:
        comments = cmp.extract_comments_from_str(code)
    except:
        for mime in EXTENSION_MIME_MAP:
            # print(mime)
            try:
                comments = cmp.extract_comments_from_str(code,mime=mime)
                if comments != []:
                    break
            except:
                pass
    if comments != []:
        for comment in comments:
            if model.predict([comment.text()]) == [1]:
                code_comment_lines.append(comment.line_number())
    else:
        print('Can not fetch comments')
    
    return code_comment_lines

def code_comment_removal(id_code: tuple[Any, str], timeout=-1, skip_timeout=False):
    doc_id,code = id_code
    try:
        with timeout_timer.timeout(timeout, timer="signal"):
            line_number = code_comment_index(code)
    except timeout_timer.TimeoutInterrupt:
        if skip_timeout:
            logger.warning(f"Skipping removing dead comments due to timeout: {doc_id}")
            line_number = []
        else:
            raise Exception(f"Timeout during comment scan: {doc_id}")
    if line_number != []:
        modified_code = "\n".join([line for i, line in enumerate(code.split("\n"), 1) if i not in line_number])
        return modified_code,len(line_number)
    else:
        return code,len(line_number)



class CommentCleanserTransform(AbstractTableTransform):
    def __init__(self, config: dict):
        super().__init__(config)

        self.column_name = config.get(COLUMN_KEY, DEFAULT_COLUMN)
        self.document_id_column_name = config.get(DOCUMENT_ID_COLUMN_KEY, DEFAULT_DOCUMENT_ID_COLUMN)
        n_processes = config.get(N_PROCESSES_KEY, DEFAULT_N_PROCESSES)
        self.n_processes = (
            max(1, multiprocessing.cpu_count() - 1)
            if n_processes < 0 or n_processes > (multiprocessing.cpu_count() - 1)
            else n_processes
        )
        logger.info(f"Running process: {self.n_processes}")
        self.timeout = config.get(TIMEOUT_KEY, DEFAULT_TIMEOUT)
        logger.info(f"Processing timeout: {self.timeout}")
        self.skip_timeout = config.get(SKIP_TIMEOUT_KEY, DEFAULT_SKIP_TIMEOUT)
        if self.skip_timeout:
            logger.info("Skip processing records when timeout occurs")

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict]:

        contents = table.column(self.column_name).to_pylist()
        if self.document_id_column_name in table.column_names:
            ids = table.column(self.document_id_column_name).to_pylist()
        else:
            ids = list(range(len(contents)))
        ids_contents = list(zip(ids, contents))

        f = code_comment_removal

        func = partial(f, timeout=self.timeout, skip_timeout=self.skip_timeout)
        updated_content = []
        remove_code_count = 0
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.n_processes) as executor:
            logger.debug(f"Start processing with {self.n_processes} executors")
            chunksize = 1
            if self.n_processes == 1:
                chunksize = len(contents)
            elif len(contents) > self.n_processes * DEFAULT_CHUNK_SIZE:
                chunksize = DEFAULT_CHUNK_SIZE
            elif len(contents) > self.n_processes * 2:
                chunksize = len(contents) // self.n_processes
            logger.debug(f"Breaking {len(contents)} contents into {math.ceil(len(contents) / chunksize)} chunks (size: {chunksize})")
            results = executor.map(func, ids_contents, chunksize=chunksize)
            for c, d in results:
                updated_content.append(c)
                remove_code_count += int(d)
        logger.debug(f"End processing: {len(updated_content)} ({remove_code_count} removed)")

        updated_content = pa.array(updated_content)

        table = table.set_column(table.column_names.index(self.column_name), self.column_name, updated_content)

        return [table], {"Removed code comment line": remove_code_count}


class CommentCleanserTransformConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name="comment_cleanser", transform_class=CommentCleanserTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            f"--{column_cli_params}",
            required=False,
            type=str,
            default=f"{DEFAULT_COLUMN}",
            help="Name of the column holds the data to process",
        )
        parser.add_argument(
            f"--{n_processes_cli_params}",
            required=False,
            type=int,
            default=f"{DEFAULT_N_PROCESSES}",
            help="Number of processes to scan codes in parallel",
        )
        parser.add_argument(
            f"--{timeout_cli_params}",
            required=False,
            type=int,
            default=f"{DEFAULT_TIMEOUT}",
            help="Timeout in seconds for code scan",
        )
        parser.add_argument(
            f"--{skip_timeout_cli_params}",
            required=False,
            type=lambda x: bool(str2bool(x)),
            default=f"{DEFAULT_SKIP_TIMEOUT}",
            help="Set True if records should be skipped when timeout occurrs during scanning",
        )
        parser.add_argument(
            f"--{document_id_column_cli_params}",
            required=False,
            type=str,
            default=f"{DEFAULT_DOCUMENT_ID_COLUMN}",
            help="Name of the column holds the document id",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        return True


class CommentCleanserPythonTransformConfiguration(PythonTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(transform_config=CommentCleanserTransformConfiguration())
