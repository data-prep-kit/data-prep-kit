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
from typing import Any
from urllib.parse import urlparse

import nltk
import pyarrow as pa
from data_processing.data_access import DataAccessFactory
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_logger
from numpy.random import default_rng


logger = get_logger(__name__, level="INFO")
from typing import Any


short_name = "fineweb_quality"
cli_prefix = short_name + "_"

END_PUNCTUATION = (".", "?", "!", '"', "'")
ELLIPSIS = "..."

# configuration keys
contents_column_name_key = "contents_column_name"
""" Key holds the name of the column holding the document text."""
frac_line_punct_cname_key = "frac_line_punct_cname"
""" Key holds the name of the output table column storing the fraction of lines that end with punctuation."""
dup_line_char_frac_cname_key = "dup_line_char_frac_cname"
""" Key holds the name of the output table column storing the duplicate line character fraction"""
new_line_ratio_cname_key = "new_line_ratio_cname"
""" Key holds the name of the output table column storing the ratio between the number of new lines and the total number of words"""
short_line_frac_cname_key = "short_line_frac_cname"
""" Key holds the name of the output table column storing the fraction of short lines"""
short_line_length_key = "short_line_length"
""" Key holds the maximum length of a short line"""

# CLI parameters corresponding to each config key
contents_column_name_cli_param = f"{cli_prefix}{contents_column_name_key}"
""" Name of the column holding the document text"""
frac_line_punct_cname_cli_param = f"{cli_prefix}{frac_line_punct_cname_key}"
""" Name of the output table column storing the fraction of lines that end with punctuation."""
dup_line_char_frac_cname_cli_param = f"{cli_prefix}{dup_line_char_frac_cname_key}"
""" Name of the output table column storing the duplicate line character fraction"""
new_line_ratio_cname_cli_param = f"{cli_prefix}{new_line_ratio_cname_key}"
""" Name of the output table column storing the ratio between the number of new lines and the total number of words"""
short_line_frac_cname_cli_param = f"{cli_prefix}{short_line_frac_cname_key}"
""" Name of the output table column storing the fraction of short lines"""
short_line_length_cli_param = f"{cli_prefix}{short_line_length_key}"
""" Maximum length of a short line"""

captured_arg_keys = [
    contents_column_name_key,
    frac_line_punct_cname_key,
    dup_line_char_frac_cname_key,
    new_line_ratio_cname_key,
    short_line_frac_cname_key,
    short_line_length_key,
]
""" The set of keys captured from the command line """

# defaults - these are the values used in the datatrove c4 filter implementation
# https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/c4_filters.py
contents_column_name_default = "text"
""" The default name of the column holding the document text. Default is `text`."""
frac_line_punct_cname_default = "frac_line_punct"
""" Name of the output table column storing the fraction of lines that end with punctuation. Default is `frac_line_punct`."""
dup_line_char_frac_cname_default = "dup_line_char_frac"
""" Name of the output table column storing the duplicate line character fraction. Default is `dup_line_char_frac`."""
new_line_ratio_cname_default = "new_line_ratio"
""" Name of the output table column storing the ratio between the number of new lines and the total number of words. Default is `new_line_ratio`."""
short_line_frac_cname_default = "short_line_frac"
""" Name of the output table column storing the fraction of short lines. Default is `short_line_frac`."""
short_line_length_default = 30
""" Maximum length of a short line. Default is `30`."""

afwq_data_access_key = "data_access"
""" Key holds the data access for reading domain files.  If not present, then block_data_factory_key is expected"""


class FineWebQualityAnnotatorTransform(AbstractTableTransform):
    """This annotator applies heuristic rules described in page 7 of the
    [FineWeb Datasets paper](https://arxiv.org/pdf/2406.17557).
    It follows the [Datatrove reference implementation]
    (https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/fineweb_quality_filter.py).

    The annotator does not remove any data, it only stores for each document
    three values that can be subsequently used to filter out documents using
    specific threshold values, such as those specified in the FineWeb reference
    implementation of the FineWeb Quality filters:
    - Discard documents where the fraction of lines ending with punctuation is <= 0.12
    - Discard documents where the fraction of characters in duplicated lines is >= 0.1
    - Discard the documents where the fraction of lines shorter than 30 characters is >= 0.67
    - Discard the documents where the ratio between new lines ('\n') and words is >= 0.3

    Args:
        contents_column_name - the name of the column holding the document text. Default is `text`.
        frac_line_punct_cname - name of the output table column storing the fraction of lines that end with punctuation. Default is `frac_line_punct`.
        dup_line_char_frac_cname - name of the output table column storing the duplicate line character fraction. Default is `dup_line_char_frac`.
        new_line_ratio_cname - name of the output table column storing the ratio between the number of new lines and the total number of words. Default is `new_line_ratio`.
        short_line_frac_cname - Name of the output table column storing the fraction of short lines. Default is `short_line_frac`.
        short_line_length - maximum length of a short line. Default is `30`.
    """

    def __init__(self, config: dict):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, BlockListTransformRuntime.  If running from the Ray orchestrator,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        super().__init__(config)

        self.contents_column_name = config.get(contents_column_name_key, contents_column_name_default)
        self.frac_line_punct_cname = config.get(frac_line_punct_cname_key, frac_line_punct_cname_default)
        self.dup_line_char_frac_cname = config.get(dup_line_char_frac_cname_key, dup_line_char_frac_cname_default)
        self.new_line_ratio_cname = config.get(new_line_ratio_cname_key, new_line_ratio_cname_default)
        self.short_line_frac_cname = config.get(short_line_frac_cname_key, short_line_frac_cname_default)
        self.short_line_length = config.get(short_line_length_key, short_line_length_default)

        # download NLTK resources needed for sentence tokenizer
        try:
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            nltk.download("punkt_tab")

    def find_duplicates(self, x: list[str]) -> tuple[int, int]:
        unique_x = set()
        duplicate_chars = 0
        duplicate_elements = 0
        for element in x:
            if element in unique_x:
                duplicate_chars += len(element)
                duplicate_elements += 1

            else:
                unique_x.add(element)
        return duplicate_elements, duplicate_chars

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """ """

        def stat_update(dct: dict, stat_name: str):
            dct[stat_name] = dct.get(stat_name, 0) + 1

        frac_line_punct_column = [0.0] * table.num_rows
        dup_line_char_frac_column = [0.0] * table.num_rows
        new_line_ratio_column = [0.0] * table.num_rows
        short_line_frac_column = [0.0] * table.num_rows
        metadata = {
            "total_docs": 0,
        }
        table_length = table.num_rows
        for index, doc in enumerate(table[self.contents_column_name]):
            stat_update(metadata, "total_docs")
            if index % 1000 == 999:
                logger.debug(f"Processed {index + 1}/ {table_length} documents")
            doc_text = doc.as_py()
            lines = doc_text.split("\n")
            frac_line_punct_column[index] = sum(1 for line in lines if line.endswith(END_PUNCTUATION)) / len(lines)
            short_line_frac_column[index] = sum(1 for line in lines if len(line) <= self.short_line_length) / len(
                lines
            )
            non_empty_lines = [line for line in lines if line.strip() != ""]
            _, dup_chars = self.find_duplicates(non_empty_lines)
            dup_line_char_frac_column[index] = dup_chars / len(doc_text.replace("\n", ""))
            words = nltk.word_tokenize(doc_text)
            new_line_count = doc_text.count("\n")
            new_line_ratio_column[index] = new_line_count / len(words)

        logger.debug(f"Processed {table_length}/ {table_length} documents")
        res_table = TransformUtils.add_column(
            table=table, name=self.frac_line_punct_cname, content=frac_line_punct_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.dup_line_char_frac_cname, content=dup_line_char_frac_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.short_line_frac_cname, content=short_line_frac_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.new_line_ratio_cname, content=new_line_ratio_column
        )

        return [res_table], metadata


class FineWebQualityAnnotatorConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=FineWebQualityAnnotatorTransform,
            remove_from_metadata=[afwq_data_access_key],
        )
        self.daf = None

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the BlockListTransform.
        By convention a common prefix should be used for all mutator-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        # The DataAccess created by the DataAccessFactory below will use this url
        parser.add_argument(
            f"--{contents_column_name_cli_param}",
            type=str,
            required=False,
            default=contents_column_name_default,
            help="Name of the column holding the document text",
        )
        parser.add_argument(
            f"--{frac_line_punct_cname_cli_param}",
            type=str,
            required=False,
            default=frac_line_punct_cname_default,
            help="Name of the output table column storing the fraction of lines that end with punctuation.",
        )
        parser.add_argument(
            f"--{dup_line_char_frac_cname_cli_param}",
            type=str,
            required=False,
            default=dup_line_char_frac_cname_default,
            help="Name of the output table column storing the duplicate line character fraction.",
        )
        parser.add_argument(
            f"--{new_line_ratio_cname_cli_param}",
            type=str,
            required=False,
            default=new_line_ratio_cname_default,
            help="Name of the output table column storing the ratio between the number of new lines and the total number of words.",
        )
        parser.add_argument(
            f"--{short_line_frac_cname_cli_param}",
            type=str,
            required=False,
            default=short_line_frac_cname_default,
            help="Name of the output table column storing the fraction of short lines.",
        )
        parser.add_argument(
            f"--{short_line_length_cli_param}",
            type=int,
            required=False,
            default=short_line_length_default,
            help="Maximum length of a short line.",
        )

        # Create the DataAccessFactory to use CLI args with the given blocklist prefix.
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
        self.params[afwq_data_access_key] = self.daf
        # Validate and populate the transform's DataAccessFactory
        return self.daf.apply_input_params(args)
