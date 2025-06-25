# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2025.
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

from typing import Any, Callable

import polars as pl
import pyarrow as pa
import textstat
from data_processing.transform import AbstractTableTransform
from data_processing.utils import get_logger
from dpk_readability.common import (
    automated_readability_index_textstat,
    coleman_liau_index_textstat,
    contents_column_name_cli_param,
    contents_column_name_default,
    dale_chall_readability_score_textstat,
    difficult_words_textstat,
    flesch_ease_textstat,
    flesch_kincaid_textstat,
    gunning_fog_textstat,
    linsear_write_formula_textstat,
    mcalpine_eflaw_textstat,
    reading_time_textstat,
    score_list_cli_param,
    score_list_default,
    smog_index_textstat,
    spache_readability_textstat,
    text_standard_textstat,
)


logger = get_logger(__name__)


class ReadabilityTransform(AbstractTableTransform):
    """
    Transform class that implements readability score
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.contents_column_name = config.get(contents_column_name_cli_param, contents_column_name_default)
        self.score_list = config.get(score_list_cli_param, score_list_default)
        if isinstance(self.score_list, str):
            self.score_list = [self.score_list]

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """transform function for readability_scores"""

        df = pl.from_arrow(table)

        ######### textstat Readability Scores
        ######### Score	School level (US)	Notes
        ######### 100.00–90.00	5th grade	Very easy to read. Easily understood by an average 11-year-old student.
        ######### 90.0–80.0	6th grade	Easy to read. Conversational English for consumers.
        ######### 80.0–70.0	7th grade	Fairly easy to read.
        ######### 70.0–60.0	8th & 9th grade	Plain English. Easily understood by 13- to 15-year-old students.
        ######### 60.0–50.0	10th to 12th grade	Fairly difficult to read.
        ######### 50.0–30.0	College	Difficult to read.
        ######### 30.0–10.0	College graduate	Very difficult to read. Best understood by university graduates.
        ######### 10.0–0.0	Professional	Extremely difficult to read. Best understood by university graduates.
        ######## While the maximum score is 121.22, there is no limit on how low the score can be. A negative score is valid.

        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.flesch_reading_ease, flesch_ease_textstat
        )

        ######## This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.flesch_kincaid_grade, flesch_kincaid_textstat
        )

        ######## This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
        df = self._add_textstat_column(df, self.contents_column_name, textstat.gunning_fog, gunning_fog_textstat)

        ######## Returns the SMOG index of the given text. This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document. Texts of fewer than 30 sentences are statistically invalid, because the SMOG formula was normed on 30-sentence samples. textstat requires at least 3 sentences for a result.
        df = self._add_textstat_column(df, self.contents_column_name, textstat.smog_index, smog_index_textstat)

        ######## Returns the grade level of the text using the Coleman-Liau Formula. This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.coleman_liau_index, coleman_liau_index_textstat
        )

        ######## Returns the ARI (Automated Readability Index) which outputs a number that approximates the grade level needed to comprehend the text. For example if the ARI is 6.5, then the grade level to comprehend the text is 6th to 7th grade.
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.automated_readability_index, automated_readability_index_textstat
        )

        ######## Different from other tests, since it uses a lookup table of the most commonly used 3000 English words. Thus it returns the grade level using the New Dale-Chall Formula. Further reading on https://en.wikipedia.org/wiki/Dale–Chall_readability_formula
        ######### Score	        Understood by
        ######### 4.9 or lower	average 4th-grade student or lower
        ######### 5.0–5.9	    average 5th or 6th-grade student
        ######### 6.0–6.9	    average 7th or 8th-grade student
        ######### 7.0–7.9	    average 9th or 10th-grade student
        ######### 8.0–8.9	    average 11th or 12th-grade student
        ######### 9.0–9.9	    average 13th to 15th-grade (college) student
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.dale_chall_readability_score, dale_chall_readability_score_textstat
        )

        ######## No explanation
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.difficult_words, difficult_words_textstat
        )

        ######## Returns the grade level using the Linsear Write Formula. This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document. Further reading on Wikipedia https://en.wikipedia.org/wiki/Linsear_Write
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.linsear_write_formula, linsear_write_formula_textstat
        )

        ######## Based upon all the above tests, returns the estimated school grade level required to understand the text. Optional float_output allows the score to be returned as a float. Defaults to False.
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.text_standard, text_standard_textstat, float_output=True
        )

        ######## Returns grade level of english text. Intended for text written for children up to grade four.
        ######## Further reading on https://en.wikipedia.org/wiki/Spache_readability_formula
        df = self._add_textstat_column(
            df, self.contents_column_name, textstat.spache_readability, spache_readability_textstat
        )

        ######## Returns a score for the readability of an english text for a foreign learner or English, focusing on the number of miniwords and length of sentences. It is recommended to aim for a score equal to or lower than 25. Further reading on blog https://strainindex.wordpress.com/2009/04/30/mcalpine-eflaw-readability-score/
        df = self._add_textstat_column(df, self.contents_column_name, textstat.mcalpine_eflaw, mcalpine_eflaw_textstat)

        ######## Returns the reading time of the given text. Assumes 14.69ms per character.
        ######## Further reading in Thttps://homepages.inf.ed.ac.uk/keller/papers/cognition08a.pdf
        df = self._add_textstat_column(df, self.contents_column_name, textstat.reading_time, reading_time_textstat)

        # output_table = pa.Table.from_pandas(pq_df_new)
        output_table = df.to_arrow()
        metadata = {"nrows": len(output_table)}

        logger.debug(f"Transformed one table with {len(output_table)} rows")
        return [output_table], metadata

    def _add_textstat_column(
        self,
        df: pl.DataFrame,
        text_column: str,
        stat_func: Callable,
        new_column_name: str,
        **kwargs: Any,
    ) -> pl.DataFrame:
        """
        Adds a new column to the Polars DataFrame by applying a textstat function to a text column.
        The function executes only if the textstat score identified in the new_column_name exists
        in the self.score_list variable

        :param df: The input Polars DataFrame
        :param text_column: The name of the text column
        :param stat_func: A textstat function to apply
        :param new_column_name: The name of the new column
        :return: A new DataFrame with the additional computed column
        """
        if new_column_name in self.score_list:
            return df.with_columns(
                df[text_column]
                .map_elements(lambda x: stat_func(x, **kwargs), return_dtype=pl.Float64)
                .alias(new_column_name)
            )
        else:
            return df
