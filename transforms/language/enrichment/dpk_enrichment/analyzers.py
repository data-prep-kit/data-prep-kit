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
import os, sys, re, yaml, json, traceback
import string, unicodedata

from collections import Counter
from typing import Dict, Tuple, Any
import dpk_enrichment.features as fs
import fasttext
import ftfy
import requests
import unicategories
import unicodedataplus as udp
from datatrove.pipeline.filters.gopher_repetition_filter import (
    find_all_duplicate,
    find_duplicates,
    find_top_duplicate,
    get_n_grams,
)
from datatrove.utils.word_tokenizers import WordTokenizer, load_word_tokenizer

# https://en.wikipedia.org/wiki/Newline#Unicode
# \n newline, \v line tab, \f form feed, \r carriage return, \u0085 next line, \u2028 line sep, \u2029 paragraph sep
NEWLINE_SPLIT_PATTERN = re.compile("[\n\v\f\r\u0085\u2028\u2029]+")
# ellipsis followed by any 15 chars at the end of the line, e.g. "bla bla bla ... more info here"
ELLIPSIS_PATTERN = re.compile("\.\.\.(.){0,15}$|\. \. \.(.){0,15}$|\u2026(.){0,15}$")
BULLET_POINT_SET = {'●', '•', '*', '-'}

ar_ranges = [
  {"from": ord(u"\u0600"), "to": ord(u"\u06FF")},                 # Arabic (256 characters)
  {"from": ord(u"\u0750"), "to": ord(u"\u077F")},                 # Arabic Supplement (48 characters))
  {"from": ord(u"\u0870"), "to": ord(u"\u089F")},                 # Arabic Extended-B (41 characters)
  {"from": ord(u"\u08A0"), "to": ord(u"\u08FF")},                 # Arabic Extended-A (96 characters)
  {"from": ord(u"\uFB50"), "to": ord(u"\uFDFF")},                 # Arabic Presentation Forms-A (631 characters)
  {"from": ord(u"\uFE70"), "to": ord(u"\uFEFF")},                 # Arabic Presentation Forms-B (141 characters)
  {"from": ord(u"\U00010E60"), "to": ord(u"\U00010E7F")},         # Rumi Numeral Symbols (31 characters)
  {"from": ord(u"\U00010EC0"), "to": ord(u"\U00010EFF")},         # Arabic Extended-C (3 characters)
  {"from": ord(u"\U0001EC70"), "to": ord(u"\U0001ECBF")},         # Indic Siyaq Numbers (68 characters)
  {"from": ord(u"\U0001ED00"), "to": ord(u"\U0001ED4F")},         # Ottoman Siyaq Numbers (61 characters)
  {"from": ord(u"\U0001EE00"), "to": ord(u"\U0001EEFF")},         # Arabic Mathematical Alphabetic Symbols (143 characters)
]

CJK_PUNCT_SYMBOLS = "".join(map(chr, range(ord("\u3000"), ord("\u303F") + 1)))
PUNCT_TRANS_TABLE = str.maketrans('', '', string.punctuation+CJK_PUNCT_SYMBOLS)

cjk_ranges = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Katakana
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0
]

cjk_scripts = {
    "Han", "Hangul", "Hiragana", "Katakana"
}

### PARALLEL DATA ENRICHERS

def is_cjk_script(char) -> bool:
    return udp.script(char) in cjk_scripts

    # return any([range["from"] <= ord(char) <= range["to"] for range in cjk_ranges])

def cjk_ratio(text: str, ignore_whitespace: bool = True, ignore_punctuation: bool = True, ignore_digits: bool = True) -> float:
    if ignore_whitespace:
        text = text.translate(str.maketrans('', '', string.whitespace))
    if ignore_punctuation:
        text = text.translate(PUNCT_TRANS_TABLE)    
    if ignore_digits:
        text = text.translate(str.maketrans('', '', string.digits))

    if len(text) == 0:
        return 0
    
    num_cjk = 0
    for c in text:
        if is_cjk_script(c):
            num_cjk += 1
    return num_cjk / len(text)


def longest_cjk_ws_seg(text: str, ignore_punctuation: bool = True, ignore_digits: bool = True) -> int:
    if ignore_punctuation:
        text = text.translate(PUNCT_TRANS_TABLE)    
    if ignore_digits:
        text = text.translate(str.maketrans('', '', string.digits))

    # split into paragraphs
    paragraphs = list(filter(None, re.split(NEWLINE_SPLIT_PATTERN, text)))
    
    cjk_seg_lengths = []
    for paragraph in paragraphs:
        segments = paragraph.split()
        for segment in segments:
            if len(segment) == 0:
                cjk_seg_lengths.append(0)
                continue
    
            num_cjk = 0
            for c in segment:
                if is_cjk_script(c):
                    num_cjk += 1
            cjk_seg_lengths.append(num_cjk)
                
    if(len(cjk_seg_lengths) == 0):
        return 0
    
    max_cjk_seg_length = sorted(cjk_seg_lengths, key=int, reverse=True)
    return max_cjk_seg_length[0]


def cjk_features_over_partition(row_it):
    for row in row_it:
        if not row.text.strip():
            yield Row(**row.asDict(), cjk_ratio=0.0, longest_cjk_seg=0.0)

        ratio = cjk_ratio(row.text)
        longest = longest_cjk_ws_seg(row.text)
        yield Row(**row.asDict(), cjk_ratio=ratio, longest_cjk_seg=longest)
        
        
def is_ar_script(char) -> bool:
    return any([range["from"] <= ord(char) <= range["to"] for range in ar_ranges])


def ar_ratio(text: str, ignore_whitespace: bool = True, ignore_punctuation: bool = True, ignore_digits: bool = True) -> float:
    if ignore_whitespace:
        text = text.translate(str.maketrans('', '', string.whitespace))
    if ignore_punctuation:
        text = text.translate(PUNCT_TRANS_TABLE)    
    if ignore_digits:
        text = text.translate(str.maketrans('', '', string.digits))

    if len(text) == 0:
        return 0
    
    num_ar = 0
    for c in text:
        if is_ar_script(c):
            num_ar += 1
    
    return num_ar / len(text)

def jaccard_index(src_line, trg_line, src_lang, trg_lang, ignore_punctuation: bool = True, ignore_case: bool = True, ignore_numbers: bool = True):
    if ignore_punctuation:
        src_line = src_line.translate(PUNCT_TRANS_TABLE)
        trg_line = trg_line.translate(PUNCT_TRANS_TABLE)
    if ignore_numbers:
        src_line = src_line.translate(str.maketrans('', '', string.digits))
        trg_line = trg_line.translate(str.maketrans('', '', string.digits))
    if ignore_case:
        src_line = src_line.lower()
        trg_line = trg_line.lower()

    # load_word_tokenizer caches singleton of each word tokenizer, so loaded only once per language
    src_tokens_list = load_word_tokenizer(language=src_lang).word_tokenize(src_line)
    trg_tokens_list = load_word_tokenizer(language=trg_lang).word_tokenize(trg_line)

    src_tokens = set(src_tokens_list)
    trg_tokens = set(trg_tokens_list)

    num_src_tokens = len(src_tokens)
    num_trg_tokens = len(trg_tokens)

    # should not really happen, but protect against zero division, and we want to remove empty lines anyways
    # if both strings empty we define jaccard index as 1.0
    if (num_src_tokens + num_trg_tokens) == 0:
        return 1.0, len(src_tokens_list), len(trg_tokens_list)

    # https://en.wikipedia.org/wiki/Jaccard_index
    jaccard_index = len(src_tokens & trg_tokens) / len(src_tokens | trg_tokens)

    return jaccard_index, len(src_tokens_list), len(trg_tokens_list)

def most_common_token(src_line, trg_line, min_tokens: int = 5):
    def most_common_token_line(line):
        tokens = line.split()
        num_tokens = len(tokens)
        if num_tokens < min_tokens:
            return '', 0.0
        most_common_token, count = Counter(tokens).most_common(1)[0]
        return most_common_token, (count / num_tokens)

    src_most_common_char, src_most_common_ratio = most_common_token_line(src_line)
    trg_most_common_char, trg_most_common_ratio = most_common_token_line(trg_line)

    return src_most_common_char, src_most_common_ratio, trg_most_common_char, trg_most_common_ratio

### OTHER DATA ENRICHERS

def punctuation_ratio(text):
    num_punc = 0
    num_non_whitespace = 0
    for c in text:
        unicode_category = unicodedata.category(c)
        if unicode_category.startswith('P'):
            num_punc += 1
        elif not c.isspace():
            num_non_whitespace += 1

    if num_non_whitespace == 0:
        return 1.0

    return num_punc/num_non_whitespace

# faster implementation, not using groupby
def character_repetition(line, consider_whitespace: bool = False, ignore_numbers: bool = True) -> int:
    current_char = None
    current_char_count = 0
    max_repetition = 0
    if ignore_numbers:
        line = line.translate(str.maketrans('', '', string.digits))
    for c in line:
        if c == current_char:
            current_char_count += 1
        else:
            if current_char_count > max_repetition and (not current_char.isspace() or consider_whitespace):
                max_repetition = current_char_count
            current_char = c
            current_char_count = 1
    if current_char_count > max_repetition and (not c.isspace() or consider_whitespace):
        max_repetition = current_char_count
    return max_repetition


CONTROL_CHAR_TRANSLATE = str.maketrans({c: "" for c in list(unicategories.categories["Cc"].characters()) + ["\ufffd"] if c not in ['\t', '\n']})

def clean_and_normalize_line(text: str):
    # replace control chars with empty string and normalize all whitespace to single whitespace and trim/strip
    fixed = " ".join(text.translate(CONTROL_CHAR_TRANSLATE).split())
    # fix encoding issues and other common problems
    fixed = ftfy.fix_text(fixed)

    return fixed, fixed != text

PUNCTUATION_CHAR_TRANSLATE = str.maketrans({c: "" for c in list(unicategories.categories["P"].characters())})

def text_enrichers(text: str, word_tokenizer: WordTokenizer, newlines_normalized: str = None, logger: Any = None) -> Dict:
    # split into paragraphs
    paragraphs = list(filter(None, re.split(NEWLINE_SPLIT_PATTERN, text)))
    if not paragraphs:
        return fn.DEFAULT_TEXT_ENRICHER_DICT
    try:
        text_enrichments = {}
        num_words = 0
        num_ellipsis_lines = 0
        num_bulletpoint_lines = 0
        num_hashes = 0
        num_tabs = 0
        total_word_chars = 0
        unicode_main_categories_counter = Counter()

        # loop over paragraphs
        tokenized_paragraphs = []
        for paragraph in paragraphs:
            stripped_paragraph = paragraph.strip()
            if re.search(ELLIPSIS_PATTERN, stripped_paragraph):
                num_ellipsis_lines += 1

            if stripped_paragraph and stripped_paragraph[0] in BULLET_POINT_SET:
                num_bulletpoint_lines += 1

            # word tokenize each paragraph
            tokenized_paragraph = word_tokenizer.word_tokenize(stripped_paragraph)
            tokenized_paragraphs.append(tokenized_paragraph)
            num_words += len(tokenized_paragraph)
            total_word_chars += sum(map(len, tokenized_paragraph))

            # loop over each char in paragraph
            for char in paragraph:
                if char == '\t':
                    # count tabs separately, do not want to mix them up with control chars
                    # newlines and other line breaking controls chars are not counted here anyways since we are going over the paragraphs
                    num_tabs += 1
                    continue

                unicode_cat = unicodedata.category(char)
                unicode_main_categories_counter.update({unicode_cat[0]: 1})
                if char == "#":
                    num_hashes += 1

        # normalize for duplicate stats
        normalized_paragraphs = []
        normalized_words = []
        all_words = []
        for tp in tokenized_paragraphs:
            all_words.extend(tp)
            # strip and lowercase, replace all punctuation with empty string, remove empty words
            words = list(filter(None, [w.strip().lower().translate(PUNCTUATION_CHAR_TRANSLATE) for w in tp]))
            if words:
                normalized_words.extend(words)
                normalized_paragraphs.append(" ".join(words))

        total_chars_paragraphs_normalized = sum(map(len, normalized_paragraphs))
        total_chars_words_normalized = sum(map(len, normalized_words))

        # get duplicate statistics
        # paragraphs dup stats
        paragraphs_duplicates, char_duplicates_paragraphs = find_duplicates(normalized_paragraphs)
        text_enrichments["dup_paragraphs_ratio"] = paragraphs_duplicates / len(normalized_paragraphs) if len(normalized_paragraphs) > 0 else 0.0
        text_enrichments["dup_paragraphs_char_ratio"] = char_duplicates_paragraphs / total_chars_paragraphs_normalized if total_chars_paragraphs_normalized > 0 else 0.0

        # top n gram stats
        for n in fs.RANGE_TOP_NGRAMS:
            n_grams_normalized = get_n_grams(normalized_words, n)
            top_char_length_normalized = find_top_duplicate(n_grams_normalized) if n_grams_normalized else 0
            text_enrichments[f"top_{n}_gram_char_ratio"] = top_char_length_normalized / total_chars_words_normalized  if total_chars_words_normalized > 0 else 0.0

        for n in fs.RANGE_DUP_NGRAMS:
            n_duplicates_char = find_all_duplicate(normalized_words, n)
            text_enrichments[f"dup_{n}_gram_char_ratio"] = n_duplicates_char / total_chars_words_normalized if total_chars_words_normalized > 0 else 0.0

        total_non_newline_chars = unicode_main_categories_counter.total()
        alphanumeric_char_ratio = (unicode_main_categories_counter.get("L", 0) + unicode_main_categories_counter.get("N", 0)) / total_non_newline_chars
        control_char_ratio = unicode_main_categories_counter.get("C", 0) / total_non_newline_chars
        punctuation_char_ratio = unicode_main_categories_counter.get("P", 0) / total_non_newline_chars
        other_symbol_char_ratio = unicode_main_categories_counter.get("S", 0) / total_non_newline_chars
        num_newlines = len(text) - total_non_newline_chars
        
        text_enrichments.update(dict(
            num_newlines = num_newlines,
            num_paragraphs=len(paragraphs),
            num_words = num_words,
            num_chars = len(text),
            total_non_newline_chars = total_non_newline_chars,

            avg_word_length = total_word_chars / num_words,
            avg_paragraph_length_chars = total_non_newline_chars / len(paragraphs),
            avg_paragraph_length_words = num_words / len(paragraphs),

            alphanumeric_char_ratio = alphanumeric_char_ratio,
            control_char_ratio = control_char_ratio,
            punctuation_char_ratio = punctuation_char_ratio,
            other_symbol_char_ratio = other_symbol_char_ratio,

            tabs_word_ratio = num_tabs / num_words,
            hashes_word_ratio = num_hashes / num_words,
            ellipsis_ratio = num_ellipsis_lines / len(paragraphs),
            bulletpoint_ratio = num_bulletpoint_lines / len(paragraphs),
        ))

        if newlines_normalized:
            text_enrichments[newlines_normalized] = "\n".join(filter(lambda p: len(p.strip()) > 0, paragraphs))
        text_enrichments['error'] = ""
        return text_enrichments
    except Exception as e:
        text_enrichments = {}
        text_enrichments.update(fs.DEFAULT_TEXT_ENRICHER_DICT)
        # indicate error
        text_enrichments['avg_word_length'] = -1.0
        t = traceback.format_exc()
        text_enrichments['error'] = f"{e}\n{t}";
        if newlines_normalized:
            text_enrichments[newlines_normalized] = ""
        if logger:
            logger.warning(f"exception during enrichment: {e}")
        return text_enrichments

def enrich_text(text: str, normalize_newlines: bool = False) -> Dict:
    word_tokenizer = load_word_tokenizer(language_or_tok="en")
    r = text_enrichers(text, word_tokenizer, normalize_newlines)
    return r

if __name__ == "__main__":
    print(json.dumps(enrich_text("this is only a test\nkeep going...\n")))
