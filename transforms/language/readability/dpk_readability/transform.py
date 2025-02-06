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

from typing import Any

import pyarrow as pa
import textstat
from data_processing.transform import AbstractTableTransform
from data_processing.utils import get_logger
from dpk_readability.common import (
    automated_readability_index_textstat,
    avg_grade_level,
    coleman_liau_index_textstat,
    contents_column_name_cli_param,
    contents_column_name_default,
    curriculum_cli_param,
    curriculum_default,
    dale_chall_readability_score_textstat,
    difficult_words_textstat,
    flesch_ease_textstat,
    flesch_kincaid_textstat,
    gunning_fog_textstat,
    linsear_write_formula_textstat,
    mcalpine_eflaw_textstat,
    reading_time_textstat,
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
        self.curriculum = config.get(curriculum_cli_param, curriculum_default)

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """transform function for readability_scores"""

        pq_df_new = table.to_pandas()

        if self.curriculum:
            ######## This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
            pq_df_new[flesch_kincaid_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.flesch_kincaid_grade(x)
            )

            ######## This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
            pq_df_new[gunning_fog_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.gunning_fog(x)
            )

            ######## Returns the ARI (Automated Readability Index) which outputs a number that approximates the grade level needed to comprehend the text. For example if the ARI is 6.5, then the grade level to comprehend the text is 6th to 7th grade.
            pq_df_new[automated_readability_index_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.automated_readability_index(x)
            )

            ######## Average of all grade_level metrics
            # pq_df_new['avg_grade_level'] = pq_df_new[['flesch_kincaid_textstat', 'gunning_fog_textstat', 'coleman_liau_index_textstat', 'automated_readability_index_textstat', 'dale_chall_readability_score_textstat', 'linsear_write_formula_textstat']].mean(axis=1)
            ######## R83_avg_GradeL
            pq_df_new[avg_grade_level] = pq_df_new[
                [flesch_kincaid_textstat, gunning_fog_textstat, automated_readability_index_textstat]
            ].mean(axis=1)

            ######## Returns a score for the readability of an english text for a foreign learner or English, focusing on the number of miniwords and length of sentences. It is recommended to aim for a score equal to or lower than 25. Further reading on blog https://strainindex.wordpress.com/2009/04/30/mcalpine-eflaw-readability-score/
            pq_df_new[mcalpine_eflaw_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.mcalpine_eflaw(x)
            )
        else:
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
            pq_df_new[flesch_ease_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.flesch_reading_ease(x)
            )

            ######## This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
            pq_df_new[flesch_kincaid_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.flesch_kincaid_grade(x)
            )

            ######## This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
            pq_df_new[gunning_fog_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.gunning_fog(x)
            )

            ######## Returns the SMOG index of the given text. This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document. Texts of fewer than 30 sentences are statistically invalid, because the SMOG formula was normed on 30-sentence samples. textstat requires at least 3 sentences for a result.
            pq_df_new[smog_index_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.smog_index(x)
            )

            ######## Returns the grade level of the text using the Coleman-Liau Formula. This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document.
            pq_df_new[coleman_liau_index_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.coleman_liau_index(x)
            )

            ######## Returns the ARI (Automated Readability Index) which outputs a number that approximates the grade level needed to comprehend the text. For example if the ARI is 6.5, then the grade level to comprehend the text is 6th to 7th grade.
            pq_df_new[automated_readability_index_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.automated_readability_index(x)
            )

            ######## Different from other tests, since it uses a lookup table of the most commonly used 3000 English words. Thus it returns the grade level using the New Dale-Chall Formula. Further reading on https://en.wikipedia.org/wiki/Dale–Chall_readability_formula
            ######### Score	        Understood by
            ######### 4.9 or lower	average 4th-grade student or lower
            ######### 5.0–5.9	    average 5th or 6th-grade student
            ######### 6.0–6.9	    average 7th or 8th-grade student
            ######### 7.0–7.9	    average 9th or 10th-grade student
            ######### 8.0–8.9	    average 11th or 12th-grade student
            ######### 9.0–9.9	    average 13th to 15th-grade (college) student
            pq_df_new[dale_chall_readability_score_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.dale_chall_readability_score(x)
            )

            ######## No explanation
            pq_df_new[difficult_words_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.difficult_words(x)
            )

            ######## Returns the grade level using the Linsear Write Formula. This is a grade formula in that a score of 9.3 means that a ninth grader would be able to read the document. Further reading on Wikipedia https://en.wikipedia.org/wiki/Linsear_Write
            pq_df_new[linsear_write_formula_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.linsear_write_formula(x)
            )

            ######## Based upon all the above tests, returns the estimated school grade level required to understand the text. Optional float_output allows the score to be returned as a float. Defaults to False.
            pq_df_new[text_standard_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.text_standard(x, float_output=True)
            )

            ######## Returns grade level of english text. Intended for text written for children up to grade four.
            ######## Further reading on https://en.wikipedia.org/wiki/Spache_readability_formula
            pq_df_new[spache_readability_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.spache_readability(x)
            )

            ######## Returns a score for the readability of an english text for a foreign learner or English, focusing on the number of miniwords and length of sentences. It is recommended to aim for a score equal to or lower than 25. Further reading on blog https://strainindex.wordpress.com/2009/04/30/mcalpine-eflaw-readability-score/
            pq_df_new[mcalpine_eflaw_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.mcalpine_eflaw(x)
            )

            ######## Returns the reading time of the given text. Assumes 14.69ms per character.
            ######## Further reading in Thttps://homepages.inf.ed.ac.uk/keller/papers/cognition08a.pdf
            pq_df_new[reading_time_textstat] = pq_df_new[self.contents_column_name].apply(
                lambda x: textstat.reading_time(x)
            )

            ######## Average of all grade_level metrics
            # pq_df_new['avg_grade_level'] = pq_df_new[['flesch_kincaid_textstat', 'gunning_fog_textstat', 'coleman_liau_index_textstat', 'automated_readability_index_textstat', 'dale_chall_readability_score_textstat', 'linsear_write_formula_textstat']].mean(axis=1)
            ######## R83_avg_GradeL
            pq_df_new[avg_grade_level] = pq_df_new[
                [flesch_kincaid_textstat, gunning_fog_textstat, automated_readability_index_textstat]
            ].mean(axis=1)

        output_table = pa.Table.from_pandas(pq_df_new)
        metadata = {"nrows": len(output_table)}

        logger.debug(f"Transformed one table with {len(output_table)} rows")
        return [output_table], metadata
