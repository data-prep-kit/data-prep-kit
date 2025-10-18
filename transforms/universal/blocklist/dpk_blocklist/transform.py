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

import re
from argparse import ArgumentParser, Namespace
from typing import Any
from urllib.parse import urlparse

import pyarrow as pa
import pygtrie
from data_processing.data_access import DataAccess, DataAccessFactory
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_logger


logger = get_logger(__name__)
from typing import Any


def reverse_url(url: str) -> str:
    url_list = re.sub("[a-zA-Z]+:/+", "", url).split(".")
    url_list.reverse()
    return ".".join(url_list)


def _extract_domain_list(file_contents: bytes) -> list[str]:
    domains = file_contents.decode("utf-8").split("\n")
    return [domain.strip() for domain in domains if not domain.startswith("#")]


def _get_domain_list(domain_list_url: str, data_access: DataAccess) -> set[str]:
    domain_list = set()
    logger.info(f"Reading domain list from {domain_list_url} ")
    blocklist_file_dict, _ = data_access.get_folder_files(domain_list_url)
    for file_name, file_contents in blocklist_file_dict.items():
        domain_list.update(_extract_domain_list(file_contents))
    logger.info(f"Added {len(domain_list)} domains to domain list")
    return domain_list


short_name = "blocklist"
cli_prefix = short_name + "_"

annotation_column_name_key = "annotation_column_name"
""" Key holds the name of the column to create in the output table"""
source_url_column_name_key = "source_url_column_name"
""" Key holds the name of the column holding the URL from which the document was retrieved"""
blocked_domain_list_path_key = "blocked_domain_list_path"
""" Key holds the directory holding 1 or more domain* files listing the urls to identify """

annotation_column_name_cli_param = f"{cli_prefix}{annotation_column_name_key}"
""" Key holds the name of the column to create in the output table"""
source_url_column_name_cli_param = f"{cli_prefix}{source_url_column_name_key}"
""" Key holds the name of the column holding the URL from which the document was retrieved"""
blocked_domain_list_path_cli_param = f"{cli_prefix}{blocked_domain_list_path_key}"
""" Key holds the directory holding 1 or more domain* files listing the urls to identify """

blocklist_data_factory_key = "data_factory"
blocklist_data_access_key = "data_access"
""" Key holds the data access for reading domain files.  If not present, then block_data_factory_key is expected"""
captured_arg_keys = [blocked_domain_list_path_key, annotation_column_name_key, source_url_column_name_key]
""" The set of keys captured from the command line """

# defaults
blocked_domain_list_path_default = "cos-optimal-llm-pile/spark_test/remove-cma-1/blocklists_refinedweb_subset/"
""" The default value for the domain list URL"""
annotation_column_name_default = "blocklisted"
""" The default name of the annotation column """
source_column_name_default = "title"
""" The default name of the column containing the source url"""


class BlockListTransform(AbstractTableTransform):
    """
    Implements block listing - given a set of documents and the URLs they were
    downloaded from, mark the documents that are from block listed domains
    """

    def __init__(self, config: dict):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, BlockListTransformRuntime.  If running from the Ray orchestrator,
        these will be provided by that class with help from the RayMutatingDriver.
        """

        super().__init__(config)
        self.blocklist_annotation_column_name = config.get(annotation_column_name_key)
        if self.blocklist_annotation_column_name is None:
            raise RuntimeError(f"Missing configuration value for key {annotation_column_name_key}")
        self.source_url_column_name = config.get(source_url_column_name_key)
        if self.source_url_column_name is None:
            raise RuntimeError(f"Missing configuration value for key {source_url_column_name_key}")

        url = config.get(blocked_domain_list_path_key, None)
        if url is None:
            raise RuntimeError(f"Missing configuration value for key {blocked_domain_list_path_key}")
        data_access = config.get(blocklist_data_access_key, None)
        if data_access is None:
            daf = config.get(blocklist_data_factory_key, None)
            if daf is None:
                raise RuntimeError(f"Missing configuration value for key {blocklist_data_factory_key}")
            data_access = daf.create_data_access()
        domain_list = _get_domain_list(url, data_access)
        # build trie structure for block listing
        logger.info(f"Loading trie with {len(domain_list)} items.")
        # logger.info(f"Loading trie with {domain_list}.")
        self.trie = pygtrie.StringTrie(separator=".")
        for url in domain_list:
            self.trie[reverse_url(url)] = ""
        del domain_list

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        This implementation makes no modifications so effectively implements a copy of the input
        parquet to the output folder, without modification.
        :param table: input table
        :return: list of output tables and custom statistics
        """

        def check_blocklist_trie(url) -> str:
            """
            Check if url is block listed
            :param url:
            :return: block listing value
            """
            url_netloc = urlparse(url).netloc
            if isinstance(
                self.trie.shortest_prefix(reverse_url(url_netloc)),
                pygtrie.Trie._Step,
            ):
                return url_netloc
            else:
                return ""

        block_listed = [""] * table.num_rows
        index = 0
        block_listed_docs_count = 0
        for url_value in table[self.source_url_column_name]:
            block_listed_value = check_blocklist_trie(str(url_value))
            if block_listed_value != "":
                block_listed_docs_count += 1
            block_listed[index] = block_listed_value
            index += 1
        metadata = {
            "total_docs_count": table.num_rows,
            "block_listed_docs_count": block_listed_docs_count,
        }
        return [
            TransformUtils.add_column(table=table, name=self.blocklist_annotation_column_name, content=block_listed)
        ], metadata


class BlockListConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=BlockListTransform,
            remove_from_metadata=[blocklist_data_factory_key],
        )
        self.daf = None

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the BlockListTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{blocked_domain_list_path_cli_param}",
            type=str,
            required=False,
            default=blocked_domain_list_path_default,
            help="S3/COS URL or local folder (file or directory) that points to the list of block listed domains. ",
        )
        parser.add_argument(
            f"--{annotation_column_name_cli_param}",
            type=str,
            required=False,
            default=annotation_column_name_default,
            help="Name of the table column that contains the block listed domains",
        )

        parser.add_argument(
            f"--{source_url_column_name_cli_param}",
            type=str,
            required=False,
            default=source_column_name_default,
            help="Name of the table column that has the document download URL",
        )
        # Create the DataAccessFactor to use CLI args with the given blocklist prefix.
        self.daf = DataAccessFactory(cli_prefix, False)
        # Add the DataAccessFactory parameters to the transform's configuration parameters.
        self.daf.add_input_params(parser)

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        # Capture the args that are specific to this transform
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        # Add the DataAccessFactory to the transform's configuration parameters.
        self.params[blocklist_data_factory_key] = self.daf
        # Validate and populate the transform's DataAccessFactory
        return self.daf.apply_input_params(args)
