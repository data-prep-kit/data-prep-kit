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

import heapq
import json
import re
from argparse import ArgumentParser, Namespace
from typing import Any
from urllib.parse import urlparse

import nltk
import pyarrow as pa
import requests
from data_processing.data_access import DataAccessFactory
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, get_dpk_logger
from numpy.random import default_rng


logger = get_dpk_logger()
from typing import Any


short_name = "c4a"
cli_prefix = short_name + "_"

CITATION_REGEX = re.compile(r"\[\d*]|\[edit]|\[citation needed]")
END_PUNCTUATION = (".", "?", "!", '"', "'")
ELLIPSIS = "..."
POLICY_SUBSTRINGS = [
    "terms of use",
    "privacy policy",
    "cookie policy",
    "uses cookies",
    "use of cookies",
    "use cookies",
]
_EN_BADWORDS_URL = "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/25e679f03d96baa721cde20db9944649e8d0a844/en"
_BADWORDS_ALLOWLIST = {}

# configuration keys
contents_column_name_key = "contents_column_name"
""" Key holds the name of the column holding the document text"""
clean_contents_column_name_key = "clean_contents_column_name"
""" Key holds the name of the column where the clean text is saved"""
drop_reason_column_name_key = "drop_reason_column_name"
""" Key holds the name of the column where the reason to drop a doc (an empty string for kept docs) is saved"""
doc_stats_column_name_key = "doc_stats_column_name"
""" Key holds the name of the column where the document stats are saved"""
tokenizer_language_key = "tokenizer_language"
""" Key holds the language for which a specific punkt tokenizer from nltk will be loaded"""
split_paragraph_key = "split_paragraph"
""" If key is True, split on \"\n\" Set to \"False\" to apply the filters to each sentence instead of to each line"""
remove_citations_key = "remove_citations"
""" If key is True, remove wikipedia style citations from the text"""
filter_no_terminal_punct_key = "filter_no_terminal_punct"
""" If key is True, remove lines without terminal punctuation marks"""
min_num_sentences_key = "min_num_sentences"
""" Key holds the minimum number of sentences (after line filtering) in a valid document. Set to -1 to disable"""
min_words_per_line_key = "min_words_per_line"
""" Key holds the minimum number of words in a valid line. Set to -1 to disable"""
max_word_length_key = "max_word_length"
""" Key holds the maximum length of a valid word. Drop the lines with words longer than this limit. Set to -1 to disable"""
filter_lorem_ipsum_key = "filter_lorem_ipsum"
""" If key is True, mark for deletion the documents that contain 'lorem ipsum' """
filter_javascript_key = "filter_javascript"
""" If key is True, drop lines mentioning 'javascript' """
filter_curly_bracket_key = "filter_curly_bracket"
""" If key is True, drop documents containing '{' """
filter_policy_key = "filter_policy"
""" If key is True, drop lines containing any of the phrases in POLICY_SUBSTRINGS"""
min_paragraphs_key = "min_paragraphs"
""" Key holds the minimum number of valid paragraphs in a valid document. Set to -1 to disable"""
min_paragraph_len_key = "min_paragraph_len"
""" Key holds the minimum length of a valid paragraph in a document. Set to -1 to disable"""
paragraph_delimiter_key = "paragraph_delimiter"
""" Key holds the character used to delimit paragraphs"""
ldnoobw_url_key = "ldnoobw_url"
""" Key holds the URL from which the LDNOOBW list will be retrieved"""
filter_badwords_key = "filter_badwords"
""" If key is True, mark for deletion documents containing bad words """
badwords_keep_fraction_key = "badwords_keep_fraction"
""" Key holds the percentage of pages containing bad words that should be kept"""
badwords_seed_key = "badwords_seed"
""" Key holds the seed used for the uniform distribution generator for use with keep_fraction"""

# CLI parameters corresponding to each config key
contents_column_name_cli_param = f"{cli_prefix}{contents_column_name_key}"
""" Name of the column holding the document text"""
clean_contents_column_name_cli_param = f"{cli_prefix}{clean_contents_column_name_key}"
""" Name of the column where the cleaned document is saved in the output table"""
drop_reason_column_name_cli_param = f"{cli_prefix}{drop_reason_column_name_key}"
""" Name of the column where the reason to drop a doc (an empty string for kept docs) is saved"""
doc_stats_column_name_cli_param = f"{cli_prefix}{doc_stats_column_name_key}"
""" Name of the column where the document stats are saved"""
tokenizer_language_cli_param = f"{cli_prefix}{tokenizer_language_key}"
""" Language for which a specific punkt tokenizer from nltk will be loaded"""
split_paragraph_cli_param = f"{cli_prefix}{split_paragraph_key}"
""" If True, split on \"\n\" Set to \"False\" to apply the filters to each sentence instead of to each line"""
remove_citations_cli_param = f"{cli_prefix}{remove_citations_key}"
""" If True, remove wikipedia style citations from the text"""
filter_no_terminal_punct_cli_param = f"{cli_prefix}{filter_no_terminal_punct_key}"
""" If True, remove lines without terminal punctuation marks"""
min_num_sentences_cli_param = f"{cli_prefix}{min_num_sentences_key}"
""" Minimum number of sentences (after line filtering) in a valid document. Set to -1 to disable"""
min_words_per_line_cli_param = f"{cli_prefix}{min_words_per_line_key}"
""" Minimum number of words in a valid line. Set to -1 to disable"""
max_word_length_cli_param = f"{cli_prefix}{max_word_length_key}"
""" Maximum length of a valid word. Drop the lines with words longer than this limit. Set to -1 to disable"""
filter_lorem_ipsum_cli_param = f"{cli_prefix}{filter_lorem_ipsum_key}"
""" If True, mark for deletion the documents that contain \"lorem ipsum\" """
filter_javascript_cli_param = f"{cli_prefix}{filter_javascript_key}"
""" If True, drop lines mentioning \"javascript\" """
filter_curly_bracket_cli_param = f"{cli_prefix}{filter_curly_bracket_key}"
""" If True, drop documents containing '{' or '}' """
filter_policy_cli_param = f"{cli_prefix}{filter_policy_key}"
""" If True, drop lines containing any of the phrases in POLICY_SUBSTRINGS"""
min_paragraphs_cli_param = f"{cli_prefix}{min_paragraphs_key}"
""" Minimum number of valid paragraphs in a valid document. Set to -1 to disable"""
min_paragraph_len_cli_param = f"{cli_prefix}{min_paragraph_len_key}"
""" Minimum length of a valid paragraph in a document. Set to -1 to disable"""
paragraph_delimiter_cli_param = f"{cli_prefix}{paragraph_delimiter_key}"
""" The character used to delimit paragraphs"""
ldnoobw_url_cli_param = f"{cli_prefix}{ldnoobw_url_key}"
""" The URL from which the LDNOOBW list will be retrieved """
filter_badwords_cli_param = f"{cli_prefix}{filter_badwords_key}"
""" If True, mark for deletion documents containing bad words """
badwords_keep_fraction_cli_param = f"{cli_prefix}{badwords_keep_fraction_key}"
""" Percentage of pages containing bad words that should be kept"""
badwords_seed_cli_param = f"{cli_prefix}{badwords_seed_key}"
""" The seed used for the uniform distribution generator for use with keep_fraction"""

captured_arg_keys = [
    contents_column_name_key,
    clean_contents_column_name_key,
    drop_reason_column_name_key,
    doc_stats_column_name_key,
    tokenizer_language_key,
    split_paragraph_key,
    remove_citations_key,
    filter_no_terminal_punct_key,
    min_num_sentences_key,
    min_words_per_line_key,
    max_word_length_key,
    filter_lorem_ipsum_key,
    filter_javascript_key,
    filter_curly_bracket_key,
    filter_policy_key,
    min_paragraphs_key,
    min_paragraph_len_key,
    paragraph_delimiter_key,
    ldnoobw_url_key,
    filter_badwords_key,
    badwords_keep_fraction_key,
    badwords_seed_key,
]
""" The set of keys captured from the command line """

# defaults - these are the values used in the datatrove c4 filter implementation
# https://github.com/huggingface/datatrove/blob/main/src/datatrove/pipeline/filters/c4_filters.py
contents_column_name_default = "text"
""" The default name of the column holding the document content"""
clean_contents_column_name_default = "clean_contents"
""" The default name of the column where the clean text is saved"""
drop_reason_column_name_default = "drop_reason"
""" Name of the column where the reason to drop a doc (an empty string for kept docs) is saved"""
doc_stats_column_name_default = "doc_stats"
""" Name of the column where the document stats are saved"""
tokenizer_language_default = "en"
""" Language for which a specific punkt tokenizer from nltk will be loaded"""
split_paragraph_default = True
""" If True, split on \"\n\" Set to \"False\" to apply the filters to each sentence instead of to each line"""
remove_citations_default = True
""" If True, remove wikipedia style citations from the text"""
filter_no_terminal_punct_default = True
""" If True, remove lines without terminal punctuation marks"""
min_num_sentences_default = 5
""" Minimum number of sentences (after line filtering) in a valid document. Set to -1 to disable"""
min_words_per_line_default = 3
""" Minimum number of words in a valid line. Set to -1 to disable"""
max_word_length_default = 1000
""" Maximum length of a valid word. Drop the lines with words longer than this limit. Set to -1 to disable"""
filter_lorem_ipsum_default = True
""" If True, mark for deletion the documents that contain \"lorem ipsum\" """
filter_javascript_default = True
""" If True, drop lines mentioning \"javascript\" """
filter_curly_bracket_default = True
""" If True, drop documents containing '{' or '}' """
filter_policy_default = True
""" If True, drop lines containing any of the phrases in POLICY_SUBSTRINGS"""
min_paragraphs_default = 3
""" Minimum number of valid paragraphs in a valid document. Set to -1 to disable"""
min_paragraph_len_default = 200
""" Minimum length of a valid paragraph in a document. Set to -1 to disable"""
paragraph_delimiter_default = "\n"
""" Character used to delimit paragraphs"""
ldnoobw_url_default = _EN_BADWORDS_URL
""" The default URL to retrieve LDNOOBW (English) """
filter_badwords_default = False
""" If True, mark for deletion documents containing bad words """
badwords_keep_fraction_default = 0.0
""" Percentage of pages containing bad words that should be kept"""
badwords_seed_default = 43
""" The seed used for the uniform distribution generator for use with keep_fraction"""

c4a_data_access_key = "data_access"
""" Key holds the data access for reading domain files.  If not present, then block_data_factory_key is expected"""


class C4AnnotatorTransform(AbstractTableTransform):
    """Applies heuristic rules from C4 https://jmlr.org/papers/volume21/20-074/20-074.pdf

    - We only retained lines that ended in a terminal punctuation mark (! . " ?)
    - We discarded any page with fewer than 5 sentences and only retained lines that contained at least 3 words
    - [NOT IMPLEMENTED] We removed any page that contained any word on the “List of Dirty, Naughty, Obscene or Otherwise Bad Words”
    - We removed any line with the word Javascript.
    - We removed any page where the phrase “lorem ipsum” appeared
    - We removed any pages that contained a curly bracket
    Additional filters not mentioned on the list from the paper but on the code:
    - Remove lines with one word over 1000 chars
    - Remove lines with cookies and terms of use keywords
    Apply paragraph filtering from C4
    - Remove the documents that have too few or too short paragraphs.
    Apply badwords filter from C4
    - Remove the documents containing more than a specific fraction of bad words

    Reference implementation: https://github.com/tensorflow/datasets/blob/master/tensorflow_datasets/text/c4_utils.py#L197
    Args:
        split_paragraph: by default (as in the paper) split on "\n".
            Set to "False" to apply the filters to each sentence instead of to each line
        remove_citations: remove wikipedia style citations from the text
        filter_no_terminal_punct: remove lines without terminal punctuation marks
        min_num_sentences: remove documents that do not have at least this number of sentences (after line filtering).
            set to -1 to disable
        min_words_per_line: drop lines without this min number of words
            set to -1 to disable
        max_word_length: drop lines where at least one word has more than this number of characters
            set to -1 to disable
        filter_lorem_ipsum: drop documents that contain "lorem ipsum"
        filter_javascript: drop lines mentioning "javascript"
        filter_curly_bracket: drop documents containing {
        filter_policy: drop lines containing any of the phrases in POLICY_SUBSTRINGS
        min_paragraphs: minimum number of valid paragraphs in a valid document
            set to -1 to disable
        min_paragraph_len: minimum length of a valid paragraph in a document
            set to -1 to disable
        paragraph_delimiter_cli_param:the character used to delimit paragraphs
        badwords_keep_fraction (float): what percentage of pages containing bad words should be kept
        badwords_seed (int): used for the uniform distribution generator for use with keep_fraction
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
        self.clean_contents_column_name = config.get(
            clean_contents_column_name_key, clean_contents_column_name_default
        )
        self.drop_reason_column_name = config.get(drop_reason_column_name_key, drop_reason_column_name_default)
        self.doc_stats_column_name = config.get(doc_stats_column_name_key, doc_stats_column_name_default)
        self.tokenizer_language = config.get(tokenizer_language_key, tokenizer_language_default)
        self.split_paragraph = config.get(split_paragraph_key, split_paragraph_default)
        self.remove_citations = config.get(remove_citations_key, remove_citations_default)
        self.filter_no_terminal_punct = config.get(filter_no_terminal_punct_key, filter_no_terminal_punct_default)
        self.min_num_sentences = config.get(min_num_sentences_key, min_num_sentences_default)
        self.min_words_per_line = config.get(min_words_per_line_key, min_words_per_line_default)
        self.max_word_length = config.get(max_word_length_key, max_word_length_default)
        self.filter_lorem_ipsum = config.get(filter_lorem_ipsum_key, filter_lorem_ipsum_default)
        self.filter_javascript = config.get(filter_javascript_key, filter_javascript_default)
        self.filter_curly_bracket = config.get(filter_curly_bracket_key, filter_curly_bracket_default)
        self.filter_policy = config.get(filter_policy_key, filter_policy_default)
        self.min_paragraphs = config.get(min_paragraphs_key, min_paragraphs_default)
        self.min_paragraph_len = config.get(min_paragraph_len_key, min_paragraph_len_default)
        self.paragraph_delimiter = config.get(paragraph_delimiter_key, paragraph_delimiter_default)
        self.filter_badwords = config.get(filter_badwords_key, filter_badwords_default)
        self.badwords_keep_fraction = config.get(badwords_keep_fraction_key, badwords_keep_fraction_default)
        self.badwords_seed = int(config.get(badwords_seed_key, badwords_seed_default))
        self.uniform = default_rng(self.badwords_seed).uniform
        self.ldnoobw_url = config.get(ldnoobw_url_key, ldnoobw_url_default)
        self.badwords_regex = self._get_badwords()

        # download NLTK resources needed for sentence tokenizer
        from random import randint
        from time import sleep

        # possible race condition although when actor restarts automatically, it will skip nltk download
        while True:
            try:
                nltk.data.find("tokenizers/punkt_tab")
                break
            except LookupError as e:
                sleep(randint(1, 10))
                try:
                    nltk.data.find("tokenizers/punkt_tab")
                except LookupError:
                    #
                    import ssl

                    try:
                        _create_unverified_https_context = ssl._create_unverified_context
                    except AttributeError:
                        pass
                    else:
                        ssl._create_default_https_context = _create_unverified_https_context
                    nltk.download("punkt_tab")

    def _get_badwords(self) -> re.Pattern:
        headers = requests.utils.default_headers()
        res = requests.get(self.ldnoobw_url, headers=headers)
        if res.status_code != 200:
            logger.error(f"Failed to get the bad words list: {res.text}, (status {res.status_code})")
            return None
        badwords: set[str] = set()
        badwords.update(line.strip() for line in res.text)
        for lang, allowlist in _BADWORDS_ALLOWLIST.items():
            if lang == "en":
                badwords -= allowlist
        words = [re.escape(w) for w in badwords]
        badwords_regex = re.compile(r"(?:\W|^)({})(?:\W|$)".format("|".join(words)))
        return badwords_regex

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """ """

        def stat_update(dct: dict, stat_name: str):
            dct[stat_name] = dct.get(stat_name, 0) + 1

        def set_drop_reason(doc_drop_reason: str, drop_reason: str, dct: dict) -> tuple[str, str]:
            if doc_drop_reason == "":
                doc_drop_reason = drop_reason
                stat_update(metadata, "dropped_docs")
                stat_update(metadata, drop_reason)
            return doc_drop_reason, doc_drop_reason

        def add_doc_stats_to_global_stats(all_doc_stats: dict, doc_stats: dict):
            for doc_stats_key, doc_stats_value in doc_stats.items():
                all_doc_stats[doc_stats_key] = all_doc_stats.get(doc_stats_key, 0) + doc_stats_value

        clean_contents_column = [""] * table.num_rows
        drop_reason_column = [""] * table.num_rows
        doc_stats_column = [{}] * table.num_rows
        metadata = {
            "total_docs": 0,
            "dropped_docs": 0,
        }
        table_length = table.num_rows
        all_doc_stats = {}
        for index, doc in enumerate(table[self.contents_column_name]):
            stat_update(metadata, "total_docs")
            if index % 1000 == 999:
                logger.debug(f"Processed {index + 1}/ {table_length} documents")
            keep_doc = True
            drop_reason = ""
            if doc.is_valid:
                doc_str = doc.as_py()
                lines = doc_str.splitlines() if self.split_paragraph else nltk.sent_tokenize(doc_str)
                paragraphs = doc_str.split(self.paragraph_delimiter)
            else:
                lines = []
                paragraphs = []
                keep_doc = False
                drop_reason, drop_reason_column[index] = set_drop_reason(
                    drop_reason,
                    "drop_invalid_document",
                    metadata,
                )
            num_sentences = 0
            kept_lines = []
            doc_stats = {}
            for line in lines:
                line = line.strip()
                words = line.split()
                stat_update(doc_stats, "line-total")
                # check line has too long word
                if self.max_word_length != -1 and any(len(word) > self.max_word_length for word in words):
                    stat_update(doc_stats, "line-filter-too_long_word")
                    continue
                # remove citation
                if self.remove_citations:
                    line = CITATION_REGEX.sub("", line)
                # end punctuation
                if self.filter_no_terminal_punct and (not line.endswith(END_PUNCTUATION) or line.endswith(ELLIPSIS)):
                    stat_update(doc_stats, "line-filter-no_terminal_punc")
                    continue
                # min words per line
                if len(words) < self.min_words_per_line:
                    stat_update(doc_stats, "line-filter-too_few_words")
                    continue
                line_l = line.lower()
                # lorem ipsum
                if self.filter_lorem_ipsum and "lorem ipsum" in line_l:
                    keep_doc = False
                    drop_reason, drop_reason_column[index] = set_drop_reason(
                        drop_reason,
                        "drop_lorem_ipsum",
                        metadata,
                    )
                    break
                # javascript
                if self.filter_javascript and "javascript" in line_l:
                    stat_update(doc_stats, "line-filter-javascript")
                    continue
                # bracket
                if self.filter_curly_bracket and "{" in line:
                    keep_doc = False
                    drop_reason, drop_reason_column[index] = set_drop_reason(
                        drop_reason,
                        "drop_curly_bracket",
                        metadata,
                    )
                    break
                # policy
                if self.filter_policy and any(p in line_l for p in POLICY_SUBSTRINGS):
                    stat_update(doc_stats, "line-filter-policy")
                    continue
                if self.min_num_sentences != -1:
                    num_sentences += len(nltk.sent_tokenize(line)) if self.split_paragraph else 1
                kept_lines.append(line)
                stat_update(doc_stats, "line-kept")
            if num_sentences < self.min_num_sentences:
                keep_doc = False
                drop_reason, drop_reason_column[index] = set_drop_reason(
                    drop_reason,
                    "drop_too_few_sentences",
                    metadata,
                )

            if len(paragraphs) < self.min_paragraphs:
                keep_doc = False
                drop_reason, drop_reason_column[index] = set_drop_reason(
                    drop_reason,
                    "drop_too_few_paragraphs",
                    metadata,
                )
            else:
                min_paragraph_length_in_doc = min(
                    heapq.nlargest(
                        self.min_paragraphs if self.min_paragraphs > 0 else 1,
                        [len(paragraph) for paragraph in paragraphs],
                    )
                )
                if min_paragraph_length_in_doc < self.min_paragraph_len:
                    keep_doc = False
                    drop_reason, drop_reason_column[index] = set_drop_reason(
                        drop_reason,
                        "drop_too_short_paragraphs",
                        metadata,
                    )
            if self.filter_badwords and self.badwords_regex:
                badwords_found = self.badwords_regex.search(doc_str.lower())
                if badwords_found is not None:
                    if self.badwords_keep_fraction <= 0.0 or self.uniform() > self.badwords_keep_fraction:
                        keep_doc = False
                        drop_reason, drop_reason_column[index] = set_drop_reason(
                            drop_reason,
                            "drop_bad_words",
                            metadata,
                        )
            if keep_doc:
                clean_contents_column[index] = ("\n" if self.split_paragraph else " ").join(kept_lines).strip()
                doc_stats_column[index] = json.dumps(doc_stats)
                add_doc_stats_to_global_stats(all_doc_stats, doc_stats)
            else:
                doc_stats_column[index] = json.dumps(doc_stats)
        metadata.update(all_doc_stats)
        # metadata["doc_line_stats"] = all_doc_stats
        logger.debug(f"Processed {table_length}/ {table_length} documents")
        res_table = TransformUtils.add_column(
            table=table, name=self.clean_contents_column_name, content=clean_contents_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.drop_reason_column_name, content=drop_reason_column
        )
        res_table = TransformUtils.add_column(
            table=res_table, name=self.doc_stats_column_name, content=doc_stats_column
        )

        return [res_table], metadata


class C4AnnotatorTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args and combining of metadata.
    """

    def __init__(self):
        super().__init__(
            name="c4_annotator",
            transform_class=C4AnnotatorTransform,
            remove_from_metadata=[c4a_data_access_key],
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
            f"--{clean_contents_column_name_cli_param}",
            type=str,
            required=False,
            default=clean_contents_column_name_default,
            help="Name of the column where the cleaned document is saved in the output table",
        )
        parser.add_argument(
            f"--{drop_reason_column_name_cli_param}",
            type=str,
            required=False,
            default=drop_reason_column_name_default,
            help="Name of the column where the keep document decision (true/false) is saved",
        )
        parser.add_argument(
            f"--{doc_stats_column_name_cli_param}",
            type=str,
            required=False,
            default=doc_stats_column_name_default,
            help="Name of the column where the document stats are saved",
        )
        parser.add_argument(
            f"--{tokenizer_language_cli_param}",
            type=str,
            required=False,
            default=tokenizer_language_default,
            help="Language for which a specific punkt tokenizer from nltk will be loaded",
        )
        parser.add_argument(
            f"--{split_paragraph_cli_param}",
            type=bool,
            required=False,
            default=split_paragraph_default,
            help="If True, split on '\n' Set to False to apply the filters to each sentence instead of to each line",
        )
        parser.add_argument(
            f"--{remove_citations_cli_param}",
            type=bool,
            required=False,
            default=remove_citations_default,
            help="If True, remove wikipedia style citations from the text",
        )
        parser.add_argument(
            f"--{filter_no_terminal_punct_cli_param}",
            type=bool,
            required=False,
            default=filter_no_terminal_punct_default,
            help="If True, remove lines without terminal punctuation marks",
        )
        parser.add_argument(
            f"--{min_num_sentences_cli_param}",
            type=int,
            required=False,
            default=min_num_sentences_default,
            help="Minimum number of sentences (after line filtering) in a valid document. Set to -1 to disable",
        )
        parser.add_argument(
            f"--{min_words_per_line_cli_param}",
            type=int,
            required=False,
            default=min_words_per_line_default,
            help="Minimum number of words in a valid line. Set to -1 to disable",
        )
        parser.add_argument(
            f"--{max_word_length_cli_param}",
            type=int,
            required=False,
            default=max_word_length_default,
            help="Maximum length of a word; drop lines with longer words. Set to -1 to disable",
        )
        parser.add_argument(
            f"--{filter_lorem_ipsum_cli_param}",
            type=bool,
            required=False,
            default=filter_lorem_ipsum_default,
            help="If True, mark for deletion the documents that contain 'lorem ipsum'",
        )
        parser.add_argument(
            f"--{filter_javascript_cli_param}",
            type=bool,
            required=False,
            default=filter_javascript_default,
            help="If True, drop lines mentioning 'javascript'",
        )
        parser.add_argument(
            f"--{filter_curly_bracket_cli_param}",
            type=bool,
            required=False,
            default=filter_curly_bracket_default,
            help="If True, drop documents containing '{' or '}'",
        )
        parser.add_argument(
            f"--{filter_policy_cli_param}",
            type=bool,
            required=False,
            default=filter_policy_default,
            help="If True, drop lines containing any of the phrases in POLICY_SUBSTRINGS",
        )
        parser.add_argument(
            f"--{min_paragraphs_cli_param}",
            type=int,
            required=False,
            default=min_paragraphs_default,
            help="Minimum number of valid paragraphs in a valid document. Set to -1 to disable",
        )
        parser.add_argument(
            f"--{min_paragraph_len_cli_param}",
            type=int,
            required=False,
            default=min_paragraph_len_default,
            help="Minimum length of a valid paragraph. Set to -1 to disable",
        )
        parser.add_argument(
            f"--{paragraph_delimiter_cli_param}",
            type=str,
            required=False,
            default=paragraph_delimiter_default,
            help="The character used to delimit paragraphs",
        )
        parser.add_argument(
            f"--{ldnoobw_url_cli_param}",
            type=str,
            required=False,
            default=ldnoobw_url_default,
            help="The URL from which the LDNOOBW list will be retrieved",
        )
        parser.add_argument(
            f"--{filter_badwords_cli_param}",
            type=bool,
            required=False,
            default=filter_badwords_default,
            help="If True, mark for deletion documents containing bad words",
        )
        parser.add_argument(
            f"--{badwords_keep_fraction_cli_param}",
            type=float,
            required=False,
            default=badwords_keep_fraction_default,
            help="Percentage of pages containing bad words that should be kept",
        )
        parser.add_argument(
            f"--{badwords_seed_cli_param}",
            type=str,
            required=False,
            default=badwords_seed_default,
            help="The seed used for the uniform distribution generator for use with keep_fraction",
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
        self.params[c4a_data_access_key] = self.daf
        # Validate and populate the transform's DataAccessFactory
        return self.daf.apply_input_params(args)
