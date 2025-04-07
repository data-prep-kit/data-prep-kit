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

import pyarrow as pa
from dpk_gneissweb_classification.classification_models import ClassificationModelFactory
from dpk_gneissweb_classification.nlp import get_label_ds_pa


def test_classification():
    nlp_langid = ClassificationModelFactory.create_model(
      "ibm-granite/GneissWeb.Med_classifier", "fasttext_medical.bin","HF_READ_ACCESS_TOKEN"
    )

    documents = pa.array(
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
    table = pa.Table.from_arrays([documents], names=["contents"])
    table, stats = get_label_ds_pa(table, nlp_langid, "contents", "label", "score")
    assert table["label"].to_pylist() == ["cc", "cc", "cc", "cc", "cc"]
    assert len(table["score"].to_pylist()) == len(table["label"].to_pylist())
    assert "ft_label" not in table.column_names
    assert "ft_score" not in table.column_names
