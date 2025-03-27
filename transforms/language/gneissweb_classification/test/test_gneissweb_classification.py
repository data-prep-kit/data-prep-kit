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

import os
import pyarrow as pa
from data_processing.test_support.transform.table_transform_test import (
    AbstractTableTransformTest,
)
from dpk_gneissweb_classification.transform import ClassificationTransform


class TestLangIdentificationTransform(AbstractTableTransformTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def get_test_transform_fixtures(self) -> list[tuple]:
        config = {
            "gcls_model_credential": os.environ.get('HF_READ_ACCESS_TOKEN', "PUT YOUR OWN HUGGINGFACE CREDENTIAL"),
            "gcls_model_file_name": ["['fasttext_medical.bin']"],
            "gcls_model_url": ["['ibm-granite/GneissWeb.Med_classifier']"],
            "gcls_content_column_name": "contents",
            "gcls_output_label_column_name": ["['l']"],
            "gcls_output_score_column_name": ["['s']"],
        }

        table = pa.Table.from_arrays(
            [
                pa.array(
                    [
                        "Der Tell Sabi Abyad („Hügel des weißen Jungen“) ist eine historische "
                        "Siedlungsstätte im Belich-Tal in Nordsyrien nahe bei dem modernen Dorf Hammam et-Turkman, ",
                        "Mu2 Gruis (36 Gruis) é uma estrela na direção da constelação de Grus. Possui uma ascensão "
                        "reta de 22h 16m 26.57s e uma declinação de −41° 37′ 37.9″. Sua magnitude aparente é igual a 5.11. ",
                        "タッチダウンオフィスは、LANと電源を用意して他のオフィスからやってきた利用者が作業できる環境を整えた場所。 " "生産性の向上を目的に通常オフィスの内部に設けられる。",
                        "Raneem El Weleily, née le à Alexandrie, est une joueuse professionnelle de squash représentant l'Égypte. "
                        "Elle atteint, en septembre 2015, la première place mondiale sur le circuit international, ",
                        "En la mitología griega, Amarinceo (en griego Ἀμαρυγκεύς) era un caudillo de los eleos. "
                        "Su padre es llamado Aléctor o Acetor o bien un tal Onesímaco,nombre dudoso. Su madre era Diogenía, "
                        "hija de Forbante y nieta de Lápites. ",
                    ]
                )
            ],
            names=["contents"],
        )
        expected_table = pa.Table.from_arrays(
            [
                pa.array(
                    [
                        "Der Tell Sabi Abyad („Hügel des weißen Jungen“) ist eine historische "
                        "Siedlungsstätte im Belich-Tal in Nordsyrien nahe bei dem modernen Dorf Hammam et-Turkman, ",
                        "Mu2 Gruis (36 Gruis) é uma estrela na direção da constelação de Grus. Possui uma ascensão "
                        "reta de 22h 16m 26.57s e uma declinação de −41° 37′ 37.9″. Sua magnitude aparente é igual a 5.11. ",
                        "タッチダウンオフィスは、LANと電源を用意して他のオフィスからやってきた利用者が作業できる環境を整えた場所。 " "生産性の向上を目的に通常オフィスの内部に設けられる。",
                        "Raneem El Weleily, née le à Alexandrie, est une joueuse professionnelle de squash représentant l'Égypte. "
                        "Elle atteint, en septembre 2015, la première place mondiale sur le circuit international, ",
                        "En la mitología griega, Amarinceo (en griego Ἀμαρυγκεύς) era un caudillo de los eleos. "
                        "Su padre es llamado Aléctor o Acetor o bien un tal Onesímaco,nombre dudoso. Su madre era Diogenía, "
                        "hija de Forbante y nieta de Lápites. ",
                    ]
                ),
                pa.array(["cc", "cc", "cc", "cc", "cc"]),
                pa.array(
                    [
                        0.966,
                        0.988,
                        1,
                        0.996,
                        0.892,
                    ]
                ),
            ],
            names=["contents", "l", "s"],
        )
        
        invalid_content_column_name_table = pa.Table.from_arrays(
            [
                pa.array(
                    [
                        "This text won't be processed",
                    ]
                )
            ],
            names=["text"],
        )
        invalid_output_lang_column_name_table = pa.Table.from_arrays(
            [
                pa.array(
                    [
                        "This content for lang column test won't be processed",
                    ]
                ),
                pa.array(
                    [
                        "cc",
                    ]
                ),
                pa.array([1.000]),
            ],
            names=["contents", "lang", "s"],
        )
        invalid_output_score_column_name_table = pa.Table.from_arrays(
            [
                pa.array(
                    [
                        "This content for score column test won't be processed",
                    ]
                ),
                pa.array(
                    [
                        "cc",
                    ]
                ),
                pa.array([1.000]),
            ],
            names=["contents", "l", "score"],
        )
        
        return [
            (
                ClassificationTransform(config),
                [
                    table,
                    invalid_content_column_name_table,
                    invalid_output_lang_column_name_table,
                    invalid_output_score_column_name_table,
                ],
                [expected_table],
                [{"cc": 5}, {}],
            )
        ]
        
