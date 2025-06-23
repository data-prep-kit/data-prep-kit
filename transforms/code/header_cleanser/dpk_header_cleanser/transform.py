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
HEADER_CLEANSER_PARAMS = "header_cleanser"

import concurrent.futures
from functools import partial
import logging
import math
import multiprocessing
import os
import tempfile
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
from scancode import api


logger = get_logger(__name__)
logging.getLogger('bs4').setLevel(logging.ERROR)
logging.getLogger('timeout_timer').setLevel(logging.ERROR)
warnings.simplefilter('ignore', DeprecationWarning)

short_name = "header_cleanser"
cli_prefix = short_name + "_"
COLUMN_KEY = "contents_column_name"
DEFAULT_DOCUMENT_ID_COLUMN = "doc_id_column_name"
DOCUMENT_ID_COLUMN_KEY = "document_id_column_name"
LICENSE_KEY = "license"
COPYRIGHT_KEY = "copyright"
N_PROCESSES_KEY = "n_processes"
TMP_DIR_KEY = "tmp_dir"
TIMEOUT_KEY = "timeout"
SKIP_TIMEOUT_KEY = "skip_timeout"

column_cli_params = f"{cli_prefix}{COLUMN_KEY}"
document_id_column_cli_params = f"{cli_prefix}{DOCUMENT_ID_COLUMN_KEY}"
license_cli_params = f"{cli_prefix}{LICENSE_KEY}"
copyright_cli_params = f"{cli_prefix}{COPYRIGHT_KEY}"
n_processes_cli_params = f"{cli_prefix}{N_PROCESSES_KEY}"
tmp_dir_cli_params = f"{cli_prefix}{TMP_DIR_KEY}"
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


def file_generate(content, tmp_dir=None):
    """
    Generate temporary file so that it can be passed to scancode-toolkit.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", dir=tmp_dir) as temp_file:
            temp_file.write(content.encode("utf-8"))
            temp_file_path = temp_file.name
    except Exception as e:
        logger.error(f"Failed to create file : {e}")
    return temp_file_path


def fetch_index(dict_data):
    """
    Extract License and copyright start and endline from dictonary
    """
    ignore_lines = []
    if dict_data.get("license_detections", None) != None:
        for licenses in dict_data.get("license_detections"):
            for match in licenses.get("matches"):
                start_line = match["start_line"] - 1
                end_line = match["end_line"] - 1
                ignore_lines.extend([i for i in range(start_line, end_line + 1)])

    if dict_data.get("copyrights", None) != None:
        for copyrights in dict_data.get("copyrights"):
            start_line = copyrights.get("start_line") - 1
            end_line = copyrights.get("end_line") - 1
            ignore_lines.extend([i for i in range(start_line, end_line + 1)])

    return ignore_lines


def check_empty_comment(code, ignore_lines):
    min_index = min(ignore_lines)
    max_index = max(ignore_lines)
    code_list = code.split("\n")
    if min_index != 0:
        min_index = min_index - 1

    if max_index <= len(code_list):
        max_index = max_index + 2
    max_index = min(max_index, len(code_list))

    for index in range(min_index, max_index):
        if all(
            not isinstance(x, (int, float, complex))
            and not isinstance(x, str)
            or (isinstance(x, str) and not x.isalnum())
            for x in code_list[index]
        ):
            if index not in ignore_lines:
                ignore_lines.append(index)

    return ignore_lines


def remove_copyright(id_code: tuple[Any, str], tmp_dir=None, timeout=-1, skip_timeout=False):
    """
    Using scancode.api function to detecte and remove copyright.
    """
    doc_id, code = id_code
    file_path = file_generate(content=code, tmp_dir=tmp_dir)
    try:
        with timeout_timer.timeout(timeout, timer="signal"):
            copyright_dict = api.get_copyrights(file_path)
    except timeout_timer.TimeoutInterrupt:
        if skip_timeout:
            logger.warning(f"Skipping removing copyrights due to timeout: {doc_id}")
            copyright_dict = {}
        else:
            raise Exception(f"Timeout during copyright scan: {doc_id}")
    os.remove(file_path)
    ignore_lines = fetch_index(copyright_dict)
    if ignore_lines != []:
        modified_code = "\n".join([line for i, line in enumerate(code.split("\n"), 0) if i not in ignore_lines])
        return modified_code, ignore_lines != []
    else:
        return code, False


def remove_license(id_code: tuple[Any, str], tmp_dir=None, timeout=-1, skip_timeout=False):
    """
    Using scancode.api function to detecte and remove license.
    """
    doc_id, code = id_code
    file_path = file_generate(content=code, tmp_dir=tmp_dir)
    try:
        with timeout_timer.timeout(timeout, timer="signal"):
            license_dict = api.get_licenses(file_path)
    except timeout_timer.TimeoutInterrupt:
        if skip_timeout:
            logger.warning(f"Skipping removing licenses due to timeout: {doc_id}")
            license_dict = {}
        else:
            raise Exception(f"Timeout during license scan: {doc_id}")
    os.remove(file_path)
    ignore_lines = fetch_index(license_dict)
    if ignore_lines != []:
        modified_code = "\n".join([line for i, line in enumerate(code.split("\n"), 0) if i not in ignore_lines])
        return modified_code, ignore_lines != []
    else:
        return code, False


def remove_license_copyright(id_code: tuple[Any, str], tmp_dir=None, timeout=-1, skip_timeout=False):
    doc_id, code = id_code
    file_path = file_generate(code, tmp_dir=tmp_dir)
    try:
        with timeout_timer.timeout(timeout, timer="signal"):
            copyright_dict = api.get_copyrights(file_path)
    except timeout_timer.TimeoutInterrupt:
        if skip_timeout:
            logger.warning(f"Skipping removing copyrights due to timeout: {doc_id}")
            copyright_dict = {}
        else:
            raise Exception(f"Timeout during copyright scan: {doc_id}")
    try:
        with timeout_timer.timeout(timeout, timer="signal"):
            license_dict = api.get_licenses(file_path)
    except timeout_timer.TimeoutInterrupt:
        if skip_timeout:
            logger.warning(f"Skipping removing licenses due to timeout: {doc_id}")
            license_dict = {}
        else:
            raise Exception(f"Timeout during license scan: {doc_id}")
    os.remove(file_path)
    ignore_lines_license = fetch_index(license_dict)
    ignore_lines_copyright = fetch_index(copyright_dict)
    ignore_lines = ignore_lines_license + ignore_lines_copyright
    if ignore_lines != []:
        ignore_lines = check_empty_comment(code, ignore_lines)
        modified_code = "\n".join([line for i, line in enumerate(code.split("\n"), 0) if i not in ignore_lines])
        return modified_code, True
    else:
        return code, False


class HeaderCleanserTransform(AbstractTableTransform):
    def __init__(self, config: dict):
        super().__init__(config)

        self.column_name = config.get(COLUMN_KEY, DEFAULT_COLUMN)
        self.license = config.get(LICENSE_KEY, DEFAULT_LICENSE)
        self.copyright = config.get(COPYRIGHT_KEY, DEFAULT_COPYRIGHT)
        self.document_id_column_name = config.get(DOCUMENT_ID_COLUMN_KEY, DEFAULT_DOCUMENT_ID_COLUMN)
        n_processes = config.get(N_PROCESSES_KEY, DEFAULT_N_PROCESSES)
        self.n_processes = (
            max(1, multiprocessing.cpu_count() - 1)
            if n_processes < 0 or n_processes > (multiprocessing.cpu_count() - 1)
            else n_processes
        )
        logger.info(f"Running process: {self.n_processes}")
        tmp_dir = config.get(TMP_DIR_KEY, None)
        self.tmp_dir = tmp_dir if tmp_dir else None
        if self.tmp_dir:
            logger.info(f"Using for tmp dir: {self.tmp_dir}")
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

        if self.license and self.copyright:
            f = remove_license_copyright

        elif self.copyright:
            f = remove_copyright

        elif self.license:
            f = remove_license

        else:
            return [table], {"Removed code count": 0}
        
        func = partial(f, tmp_dir=self.tmp_dir, timeout=self.timeout, skip_timeout=self.skip_timeout)
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

        return [table], {"Removed code count": remove_code_count}


class HeaderCleanserTransformConfiguration(TransformConfiguration):
    def __init__(self):
        super().__init__(name="header_cleanser", transform_class=HeaderCleanserTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            f"--{column_cli_params}",
            required=False,
            type=str,
            default=f"{DEFAULT_COLUMN}",
            help="Name of the column holds the data to process",
        )
        parser.add_argument(
            f"--{license_cli_params}",
            required=False,
            type=lambda x: bool(str2bool(x)),
            default=f"{DEFAULT_LICENSE}",
            help="Set False if license should not be removed",
        )
        parser.add_argument(
            f"--{copyright_cli_params}",
            required=False,
            type=lambda x: bool(str2bool(x)),
            default=f"{DEFAULT_COPYRIGHT}",
            help="Set False if copyright should not be removed ",
        )
        parser.add_argument(
            f"--{n_processes_cli_params}",
            required=False,
            type=int,
            default=f"{DEFAULT_N_PROCESSES}",
            help="Number of processes to scan codes in parallel",
        )
        parser.add_argument(
            f"--{tmp_dir_cli_params}",
            required=False,
            type=str,
            default=None,
            help="Set a path if tmp directory should be specified",
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