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

import json, argparse, pyarrow

from typing import Any
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, UnrecoverableException

from dpk_enrichment.analyzers import text_enrichers
from dpk_enrichment.features import DEFAULT_TEXT_ENRICHER_DICT
from dpk_enrichment.info import short_name, description, get_transform_params, get_transform_param_defaults
from datatrove.utils.word_tokenizers import WordTokenizer, load_word_tokenizer

def text_enrichment(text: str, word_tokenizer: WordTokenizer, columns_map: dict[str, str], normalized_text: str, logger: Any) -> dict[str, Any]:
    r = text_enrichers(text, word_tokenizer, normalized_text)
    return {v: r[k] for k, v in columns_map.items() if v}

# read a param value from the config, with the appropriate defaults
def get_config(config: dict[str, Any], param: str):
    return config.get(param, get_transform_param_defaults().get(param, ""))

class EnrichmentTransform(AbstractTableTransform):
    """
    Implements schema modification of a pyarrow Table.
    """
    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        super().__init__(config)

        self.doc_column = get_config(config, "content_column_name")
        self.lang_column = get_config(config, "lang_column_name")
        self.output_column_prefix = get_config(config, "output_column_prefix")
        self.newline_normalized_column_name = get_config(config, "newline_normalized_column_name")
        self.error_column_name = get_config(config, "error_column_name")

        self.output_columns = { k: self.output_column_prefix + config.get(f"{k}_column_name", k) for k in DEFAULT_TEXT_ENRICHER_DICT.keys() if config.get(f"{k}_column_name", k) }
        if self.error_column_name:
            self.output_columns["error"] = self.error_column_name
        if self.newline_normalized_column_name:
            self.output_columns["newline_normalized"] = self.newline_normalized_column_name

        if len([k for k, v in self.output_columns.items() if v]) == 0:
            raise UnrecoverableException("At least one output colum must be given")
        self.tok_api_ver = 0
        try:
            if self.tok_api_ver == 0:
                self.word_tokenizers = {"en": load_word_tokenizer(language_or_tok="en")}
                self.tok_api_ver = 40
        except Exception as e:
            self.logger.info(f"{e}, when loading en tokenizer (datatrove version > 0.3.0)")
        try:
            if self.tok_api_ver == 0:
                self.word_tokenizers = {"en": load_word_tokenizer(language="en")}
                self.tok_api_ver = 30
        except Exception as e:
            self.logger.info(f"{e}, when loading en tokenizer (datatrove version = 0.3.0)")
        if self.tok_api_ver == 0:
            raise UnrecoverableException("Can't load tokenizer")
        self.de_json = True

        ## External resources needed 
        import nltk
        nltk.download('punkt_tab')
        
    def get_tokenizer(self, lang: str)->WordTokenizer: 
        try: 
            wt = self.word_tokenizers.get(lang, None)
            if not wt:
                if self.tok_api_ver == 40:
                    wt = load_word_tokenizer(language_or_tok=lang)
                else:
                    wt = load_word_tokenizer(language=lang)

                self.word_tokenizers[lang] = wt
            return wt

        except ValueError as e:
            self.logger.warning(f"{e}, using 'en' tokenizer")
            self.word_tokenizers[lang] = self.word_tokenizers["en"]
            return self.word_tokenizers[lang]

        return None

    def enrich_text(self, table: pyarrow.Table, content_column: str, lang_column: str, output_columns: dict[str, str]) -> tuple[pyarrow.table, Any]:
        enrichment = pyarrow.Table.from_pylist(list(
            map(lambda x: text_enrichment(x[0], self.get_tokenizer(x[1]), output_columns, "newline_normalized" if self.newline_normalized_column_name else None, self.logger), 
                zip(table[content_column].to_pylist(), table[lang_column].to_pylist()))
        ))

        result = table
        for ec, rc in output_columns.items():
            if not rc:
                continue
            result = TransformUtils.add_column(table=result, name=rc, content=enrichment[rc])

        return result, {}

    def transform(self, table: pyarrow.Table, file_name: str = None) -> tuple[list[pyarrow.Table], dict[str, Any]]:
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary
        This implementation makes no modifications so effectively implements a copy of the
        input parquet to the output folder, without modification.
        """
        TransformUtils.validate_columns(table=table, required=[self.doc_column, self.lang_column])
        already_exist = [ v for k, v in self.output_columns.items() if v in table.schema.names ]
        if len(already_exist) > 0:
            raise Exception(f"output columns {', '.join(already_exist)} already exist")

        self.logger.debug(f"Enriching one table with {len(table)} rows")
        table, stats = self.enrich_text(table, self.doc_column, self.lang_column, self.output_columns)
        self.logger.debug(f"Enriched one table with {len(table)} rows")

        return [table], stats

