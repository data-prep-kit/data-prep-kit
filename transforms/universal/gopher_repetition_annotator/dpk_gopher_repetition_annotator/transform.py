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
from collections import Counter
from typing import Any
import nltk
import pyarrow as pa
from data_processing.data_access import DataAccessFactory
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_logger
from typing import Any

short_name = "gra"
cli_prefix = short_name + "_"

# configuration keys
contents_column_name_key = "contents_column_name"
""" Key holds the name of the column holding the document text"""
dup_line_frac_cname_key = "dup_line_frac_cname"
""" Key holds the name of the output table column storing the duplicate line fraction"""
dup_para_frac_cname_key = "dup_para_frac_cname"
""" Key holds the name of the output table column storing the duplicate paragraph fraction"""
dup_line_char_frac_cname_key = "dup_line_char_frac_cname"
""" Key holds the name of the output table column storing the duplicate line character fraction"""
dup_para_char_frac_cname_key = "dup_para_char_frac_cname"
""" Key holds the name of the output table column storing the duplicate paragraph character fraction"""
top_2_grams_cname_key = "top_2_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters in the most frequent 2-grams"""
top_3_grams_cname_key = "top_3_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters in the most frequent 3-grams"""
top_4_grams_cname_key = "top_4_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters in the most frequent 4-grams"""
dup_5_grams_cname_key = "dup_5_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters contained within all duplicate 5-grams"""
dup_6_grams_cname_key = "dup_6_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters contained within all duplicate 6-grams"""
dup_7_grams_cname_key = "dup_7_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters contained within all duplicate 7-grams"""
dup_8_grams_cname_key = "dup_8_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters contained within all duplicate 8-grams"""
dup_9_grams_cname_key = "dup_9_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters contained within all duplicate 9-grams"""
dup_10_grams_cname_key = "dup_10_grams_cname"
""" Key holds the name of the output table column storing the fraction of characters contained within all duplicate 10-grams"""

# CLI parameters corresponding to each config key
contents_column_name_cli_param = f"{cli_prefix}{contents_column_name_key}"
""" Name of the column holding the document text"""
dup_line_frac_cname_cli_param = f"{cli_prefix}{dup_line_frac_cname_key}"
""" Name of the output table column storing the duplicate line fraction"""
dup_para_frac_cname_cli_param = f"{cli_prefix}{dup_para_frac_cname_key}"
""" Name of the output table column storing the duplicate paragraph fraction"""
dup_line_char_frac_cname_cli_param = f"{cli_prefix}{dup_line_char_frac_cname_key}"
""" Name of the output table column storing the duplicate line character fraction"""
dup_para_char_frac_cname_cli_param = f"{cli_prefix}{dup_para_char_frac_cname_key}"
""" Name of the output table column storing the duplicate paragraph character fraction"""
top_2_grams_cname_cli_param = f"{cli_prefix}{top_2_grams_cname_key}"
""" Name of the output table column storing the fraction of characters in the most frequent 2-grams"""
top_3_grams_cname_cli_param = f"{cli_prefix}{top_3_grams_cname_key}"
""" Name of the output table column storing the fraction of characters in the most frequent 3-grams"""
top_4_grams_cname_cli_param = f"{cli_prefix}{top_4_grams_cname_key}"
""" Name of the output table column storing the fraction of characters in the most frequent 4-grams"""
dup_5_grams_cname_cli_param = f"{cli_prefix}{dup_5_grams_cname_key}"
""" Name of the output table column storing the fraction of characters contained within all duplicate 5-grams"""
dup_6_grams_cname_cli_param = f"{cli_prefix}{dup_6_grams_cname_key}"
""" Name of the output table column storing the fraction of characters contained within all duplicate 6-grams"""
dup_7_grams_cname_cli_param = f"{cli_prefix}{dup_7_grams_cname_key}"
""" Name of the output table column storing the fraction of characters contained within all duplicate 7-grams"""
dup_8_grams_cname_cli_param = f"{cli_prefix}{dup_8_grams_cname_key}"
""" Name of the output table column storing the fraction of characters contained within all duplicate 8-grams"""
dup_9_grams_cname_cli_param = f"{cli_prefix}{dup_9_grams_cname_key}"
""" Name of the output table column storing the fraction of characters contained within all duplicate 9-grams"""
dup_10_grams_cname_cli_param = f"{cli_prefix}{dup_10_grams_cname_key}"
""" Name of the output table column storing the fraction of characters contained within all duplicate 10-grams"""

captured_arg_keys = [
    contents_column_name_key,
    dup_line_frac_cname_key,
    dup_para_frac_cname_key,
    dup_line_char_frac_cname_key,
    dup_para_char_frac_cname_key,
    top_2_grams_cname_key,
    top_3_grams_cname_key,
    top_4_grams_cname_key,
    dup_5_grams_cname_key,
    dup_6_grams_cname_key,
    dup_7_grams_cname_key,
    dup_8_grams_cname_key,
    dup_9_grams_cname_key,
    dup_10_grams_cname_key,
]
""" The set of keys captured from the command line """

# defaults
contents_column_name_default = "text"
""" The default name of the column holding the document text"""
dup_line_frac_cname_default = "dup_line_frac"
""" Name of the output table column storing the duplicate line fraction"""
dup_para_frac_cname_default = "dup_para_frac"
""" Name of the output table column storing the duplicate paragraph fraction"""
dup_line_char_frac_cname_default = "dup_line_char_frac"
""" Name of the output table column storing the duplicate line character fraction"""
dup_para_char_frac_cname_default = "dup_para_char_frac"
""" Name of the output table column storing the duplicate paragraph character fraction"""
top_2_grams_cname_default = "top_2_grams"
""" Name of the output table column storing the fraction of characters in the most frequent 2-grams"""
top_3_grams_cname_default = "top_3_grams"
""" Name of the output table column storing the fraction of characters in the most frequent 3-grams"""
top_4_grams_cname_default = "top_4_grams"
""" Name of the output table column storing the fraction of characters in the most frequent 4-grams"""
dup_5_grams_cname_default = "dup_5_grams"
""" Name of the output table column storing the fraction of characters contained within all duplicate 5-grams"""
dup_6_grams_cname_default = "dup_6_grams"
""" Name of the output table column storing the fraction of characters contained within all duplicate 6-grams"""
dup_7_grams_cname_default = "dup_7_grams"
""" Name of the output table column storing the fraction of characters contained within all duplicate 7-grams"""
dup_8_grams_cname_default = "dup_8_grams"
""" Name of the output table column storing the fraction of characters contained within all duplicate 8-grams"""
dup_9_grams_cname_default = "dup_9_grams"
""" Name of the output table column storing the fraction of characters contained within all duplicate 9-grams"""
dup_10_grams_cname_default = "dup_10_grams"
""" Name of the output table column storing the fraction of characters contained within all duplicate 10-grams"""

agr_data_access_key = "data_access"
""" Key holds the data access for reading domain files.  If not present, then block_data_factory_key is expected"""


class GopherRepetitionAnnotatorTransform(AbstractTableTransform):
    """Annotation that enables the application of the heuristic rules from Gopher Repetition Removal https://arxiv.org/pdf/2112.11446

    An indicator of poor quality data is excessive repetition of certain words or phrases within a document.
    This annotator helps identifying documents with a high proportion of repeated lines, paragraphs, or n-grams.
    It does not remove any data, subsequently data can be filtered out using a set of thresholds,
    like those defined in Table A1 from https://arxiv.org/pdf/2112.11446.pdf
    duplicate line fraction                 0.30
    duplicate paragraph fraction            0.30
    duplicate line character fraction       0.20
    duplicate paragraph character fraction  0.20

    top 2-gram character fraction           0.20
    top 3-gram character fraction           0.18
    top 4-gram character fraction           0.16

    duplicate 5-gram character fraction     0.15
    duplicate 6-gram character fraction     0.14
    duplicate 7-gram character fraction     0.13
    duplicate 8-gram character fraction     0.12
    duplicate 9-gram character fraction     0.11
    duplicate 10-gram character fraction    0.10

    Args:
        dup_line_frac_cname: output table column storing the duplicate line fraction
        dup_para_frac_cname: output table column storing the duplicate paragraph fraction
        dup_line_char_frac_cname: output table column storing the duplicate line character fraction
        dup_para_char_frac_cname: output table column storing the duplicate paragraph character fraction
        top_2_grams_cname: output table column storing the fraction of characters in the most frequent 2-grams
        top_3_grams_cname: output table column storing the fraction of characters in the most frequent 3-grams
        top_4_grams_cname: output table column storing the fraction of characters in the most frequent 4-grams
        dup_5_grams_cname: output table column storing the fraction of characters contained within all duplicate 5-grams
        dup_6_grams_cname: output table column storing the fraction of characters contained within all duplicate 6-grams
        dup_7_grams_cname: output table column storing the fraction of characters contained within all duplicate 7-grams
        dup_8_grams_cname: output table column storing the fraction of characters contained within all duplicate 8-grams
        dup_9_grams_cname: output table column storing the fraction of characters contained within all duplicate 9-grams
        dup_10_grams_cname: output table column storing the fraction of characters contained within all duplicate 10-grams
    """

    def __init__(self, config: dict):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, BlockListTransformRuntime.  If running from the Ray orchestrator,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.contents_column_name = config.get(contents_column_name_key, contents_column_name_default)
        self.dup_line_frac_cname = config.get(dup_line_frac_cname_key, dup_line_frac_cname_default)
        self.dup_para_frac_cname = config.get(dup_para_frac_cname_key, dup_para_frac_cname_default)
        self.dup_line_char_frac_cname = config.get(dup_line_char_frac_cname_key, dup_line_char_frac_cname_default)
        self.dup_para_char_frac_cname = config.get(dup_para_char_frac_cname_key, dup_para_char_frac_cname_default)
        self.top_2_grams_cname = config.get(top_2_grams_cname_key, top_2_grams_cname_default)
        self.top_3_grams_cname = config.get(top_3_grams_cname_key, top_3_grams_cname_default)
        self.top_4_grams_cname = config.get(top_4_grams_cname_key, top_4_grams_cname_default)
        self.dup_5_grams_cname = config.get(dup_5_grams_cname_key, dup_5_grams_cname_default)
        self.dup_6_grams_cname = config.get(dup_6_grams_cname_key, dup_6_grams_cname_default)
        self.dup_7_grams_cname = config.get(dup_7_grams_cname_key, dup_7_grams_cname_default)
        self.dup_8_grams_cname = config.get(dup_8_grams_cname_key, dup_8_grams_cname_default)
        self.dup_9_grams_cname = config.get(dup_9_grams_cname_key, dup_9_grams_cname_default)
        self.dup_10_grams_cname = config.get(dup_10_grams_cname_key, dup_10_grams_cname_default)

        self.paragraph_exp = re.compile(r"\n{2,}")
        self._line_splitter = re.compile("\n+")

        # download NLTK resources needed for sentence tokenizer
        try:
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            nltk.download("punkt_tab")
        # self.tokenizer = load_word_tokenizer(language)

    def get_n_grams(self, words: list[str], n: int) -> list[str]:
        return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]

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

    def find_top_duplicate(self, x: list[str]) -> int:
        counter = Counter()
        for element in x:
            counter[element] += 1
        top_n_gram = counter.most_common(1)[0]
        return len(top_n_gram[0]) * top_n_gram[1]

    def find_all_duplicate(self, words: list[str], n: int) -> int:
        n_words = len(words)
        unique = set()
        repeated_chars, idx = 0, 0
        while idx < n_words - n + 1:
            n_gram = "".join(words[idx : idx + n])
            if n_gram in unique:
                repeated_chars += len(n_gram)
                idx += n
            else:
                unique.add(n_gram)
                idx += 1
        assert repeated_chars <= len("".join(words))
        return repeated_chars

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """ """

        def stat_update(dct: dict, stat_name: str):
            dct[stat_name] = dct.get(stat_name, 0) + 1

        dup_line_frac_column = [0.0] * table.num_rows
        dup_para_frac_column = [0.0] * table.num_rows
        dup_line_char_frac_column = [0.0] * table.num_rows
        dup_para_char_frac_column = [0.0] * table.num_rows
        top_2_grams_column = [0.0] * table.num_rows
        top_3_grams_column = [0.0] * table.num_rows
        top_4_grams_column = [0.0] * table.num_rows
        dup_5_grams_column = [0.0] * table.num_rows
        dup_6_grams_column = [0.0] * table.num_rows
        dup_7_grams_column = [0.0] * table.num_rows
        dup_8_grams_column = [0.0] * table.num_rows
        dup_9_grams_column = [0.0] * table.num_rows
        dup_10_grams_column = [0.0] * table.num_rows

        metadata = {
            "total_docs": 0,
        }
        table_length = table.num_rows
        for index, doc in enumerate(table[self.contents_column_name]):
            if index % 1000 == 999:
                self.logger.debug(f"Processed {index + 1}/ {table_length} documents")
            stat_update(metadata, "total_docs")
            text = doc.as_py()

            lines = self._line_splitter.split(text)
            line_duplicates, char_duplicates = self.find_duplicates(lines)
            dup_line_frac_column[index] = line_duplicates / len(lines)
            dup_line_char_frac_column[index] = char_duplicates / len(text)

            paragraphs = self.paragraph_exp.split(text.strip())
            paragraphs_duplicates, char_duplicates = self.find_duplicates(paragraphs)
            dup_para_frac_column[index] = paragraphs_duplicates / len(paragraphs)
            dup_para_char_frac_column[index] = char_duplicates / len(text)

            words = nltk.word_tokenize(text)
            top_grams_columns = [
                top_2_grams_column,
                top_3_grams_column,
                top_4_grams_column,
            ]
            for n, top_grams_column in zip(range(2, 5), top_grams_columns):
                n_grams = self.get_n_grams(words, n)
                if not n_grams:
                    continue
                top_char_length = self.find_top_duplicate(n_grams)
                top_grams_column[index] = top_char_length / len(text)
            dup_grams_columns = [
                dup_5_grams_column,
                dup_6_grams_column,
                dup_7_grams_column,
                dup_8_grams_column,
                dup_9_grams_column,
                dup_10_grams_column,
            ]
            for n, dup_grams_column in zip(range(5, 11), dup_grams_columns):
                n_duplicates_char = self.find_all_duplicate(words, n)
                dup_grams_column[index] = n_duplicates_char / len(text)

        self.logger.debug(f"Processed {table_length}/ {table_length} documents")

        res_table = TransformUtils.add_column(table=table, name=self.dup_line_frac_cname, content=dup_line_frac_column)
        res_table = TransformUtils.add_column(
            table=res_table, name=self.dup_para_frac_cname, content=dup_para_frac_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.dup_line_char_frac_cname, content=dup_line_char_frac_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.dup_para_char_frac_cname, content=dup_para_char_frac_column
        )
        res_table = TransformUtils.add_column(table=res_table, name=self.top_2_grams_cname, content=top_2_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.top_3_grams_cname, content=top_3_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.top_4_grams_cname, content=top_4_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.dup_5_grams_cname, content=dup_5_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.dup_6_grams_cname, content=dup_6_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.dup_7_grams_cname, content=dup_7_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.dup_8_grams_cname, content=dup_8_grams_column)
        res_table = TransformUtils.add_column(table=res_table, name=self.dup_9_grams_cname, content=dup_9_grams_column)
        res_table = TransformUtils.add_column(
            table=res_table, name=self.dup_10_grams_cname, content=dup_10_grams_column
        )
        return [res_table], metadata


class GopherRepetitionAnnotatorConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name="gopher_repetition_annotator",
            transform_class=GopherRepetitionAnnotatorTransform,
            remove_from_metadata=[agr_data_access_key],
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
            f"--{dup_line_frac_cname_cli_param}",
            type=str,
            required=False,
            default=dup_line_frac_cname_default,
            help="Name of the output table column storing the duplicate line fraction",
        )
        parser.add_argument(
            f"--{dup_para_frac_cname_cli_param}",
            type=str,
            required=False,
            default=dup_para_frac_cname_default,
            help="Name of the output table column storing the duplicate paragraph fraction",
        )
        parser.add_argument(
            f"--{dup_line_char_frac_cname_cli_param}",
            type=str,
            required=False,
            default=dup_line_char_frac_cname_default,
            help="Name of the output table column storing the duplicate line character fraction",
        )
        parser.add_argument(
            f"--{dup_para_char_frac_cname_cli_param}",
            type=str,
            required=False,
            default=dup_para_char_frac_cname_default,
            help="Name of the output table column storing the duplicate paragraph character fraction",
        )
        parser.add_argument(
            f"--{top_2_grams_cname_cli_param}",
            type=str,
            required=False,
            default=top_2_grams_cname_default,
            help="Name of the output table column storing the fraction of characters in the most frequent 2-grams",
        )
        parser.add_argument(
            f"--{top_3_grams_cname_cli_param}",
            type=str,
            required=False,
            default=top_3_grams_cname_default,
            help="Name of the output table column storing the fraction of characters in the most frequent 3-grams",
        )
        parser.add_argument(
            f"--{top_4_grams_cname_cli_param}",
            type=str,
            required=False,
            default=top_4_grams_cname_default,
            help="Name of the output table column storing the fraction of characters in the most frequent 4-grams",
        )
        parser.add_argument(
            f"--{dup_5_grams_cname_cli_param}",
            type=str,
            required=False,
            default=dup_5_grams_cname_default,
            help="Name of the output table column storing the fraction of characters contained within all duplicate 5-grams",
        )
        parser.add_argument(
            f"--{dup_6_grams_cname_cli_param}",
            type=str,
            required=False,
            default=dup_6_grams_cname_default,
            help="Name of the output table column storing the fraction of characters contained within all duplicate 6-grams",
        )
        parser.add_argument(
            f"--{dup_7_grams_cname_cli_param}",
            type=str,
            required=False,
            default=dup_7_grams_cname_default,
            help="Name of the output table column storing the fraction of characters contained within all duplicate 7-grams",
        )
        parser.add_argument(
            f"--{dup_8_grams_cname_cli_param}",
            type=str,
            required=False,
            default=dup_8_grams_cname_default,
            help="Name of the output table column storing the fraction of characters contained within all duplicate 8-grams",
        )
        parser.add_argument(
            f"--{dup_9_grams_cname_cli_param}",
            type=str,
            required=False,
            default=dup_9_grams_cname_default,
            help="Name of the output table column storing the fraction of characters contained within all duplicate 9-grams",
        )
        parser.add_argument(
            f"--{dup_10_grams_cname_cli_param}",
            type=str,
            required=False,
            default=dup_10_grams_cname_default,
            help="Name of the output table column storing the fraction of characters contained within all duplicate 10-grams",
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
        self.params[agr_data_access_key] = self.daf
        # Validate and populate the transform's DataAccessFactory
        return self.daf.apply_input_params(args)
