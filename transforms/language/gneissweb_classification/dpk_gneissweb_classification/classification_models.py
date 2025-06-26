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

import math
from abc import ABCMeta, abstractmethod

import fasttext
import numpy as np
from huggingface_hub import hf_hub_download
import os
from langcodes import standardize_tag


class ClassificationModel(metaclass=ABCMeta):
    @abstractmethod
    def detect_label(self, text: str) -> tuple[str, float]:
        pass


class NoopModel(ClassificationModel):
    def detect_label(self, text: str) -> tuple[str, float]:  # pylint: disable=unused-argument
        return "en", 0.0


class FastTextModel(ClassificationModel):
    def __init__(self, model, url):
        self.nlp = model
        self.url = url

    def detect_label(self, text: str) -> tuple[str, float]:
        if self.url == "facebook/fasttext-language-identification":
            label, score = self.nlp.predict(
            text.replace("\n", " "), 1
            )  # replace newline to avoid ERROR: predict processes one line at a time (remove '\n') skipping the file
            return standardize_tag(label[0].replace("__label__", "")), math.floor(score[0] * 1000) / 1000
        elif self.url == "mlfoundations/fasttext-oh-eli5":
            label, score = self.nlp.predict(" ".join(text.strip().splitlines()))
            score = score[0]
            if label == "__label__cc":
                score = 1 - score
            return label[0].replace("__label__", ""), score

        else:
            label, score = self.nlp.predict(
            text.replace("\n", " "), 1
            )  # replace newline to avoid ERROR: predict processes one line at a time (remove '\n') skipping the file
            return label[0].replace("__label__", ""), math.floor(score[0] * 1000) / 1000

