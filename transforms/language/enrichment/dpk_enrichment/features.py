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

DEFAULT_TEXT_ENRICHER_DICT = {
    "num_newlines": 0,
    "num_paragraphs": 0,
    "num_words": 0,
    "num_chars": 0,
    "total_non_newline_chars": 0,

    "avg_word_length": 0.0,
    "avg_paragraph_length_chars": 0.0,
    "avg_paragraph_length_words": 0.0,

    "alphanumeric_char_ratio": 0.0,
    "control_char_ratio": 0.0,
    "punctuation_char_ratio": 0.0,
    "other_symbol_char_ratio": 0.0,

    "tabs_word_ratio": 0.0,
    "hashes_word_ratio": 0.0,
    "ellipsis_ratio": 0.0,
    "bulletpoint_ratio": 0.0,

    'dup_paragraphs_ratio': 0.0,
    'dup_paragraphs_char_ratio': 0.0,

    'top_2_gram_char_ratio': 0.0,
    'top_3_gram_char_ratio': 0.0,
    'top_4_gram_char_ratio': 0.0,

    'dup_5_gram_char_ratio': 0.0,
    'dup_6_gram_char_ratio': 0.0,
    'dup_7_gram_char_ratio': 0.0,
    'dup_8_gram_char_ratio': 0.0,
    'dup_9_gram_char_ratio': 0.0,
    'dup_10_gram_char_ratio': 0.0,
}

RANGE_TOP_NGRAMS = range(2,5)
RANGE_DUP_NGRAMS = range(5,11)

for n in RANGE_TOP_NGRAMS:
    DEFAULT_TEXT_ENRICHER_DICT[f"top_{n}_gram_char_ratio"] = 0.0

for n in RANGE_DUP_NGRAMS:
    DEFAULT_TEXT_ENRICHER_DICT[f"dup_{n}_gram_char_ratio"] = 0.0

