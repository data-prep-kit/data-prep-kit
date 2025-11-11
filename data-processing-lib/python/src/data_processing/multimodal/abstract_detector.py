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

import abc
from abc import abstractmethod
from typing import Union

import numpy as np


class Coordinate(abc.ABC):

    def __init__(self, x:int, y:int):
        self.x = x
        self.y = y

class BoundingBox(abc.ABC):

    def __init__(self, lower_left:Coordinate, upper_right:Coordinate):
        self.lower_left = lower_left
        self.upper_right = upper_right

class ObjectDetection(abc.ABC):

    def __init__(self, label:str, confidence:float, bbox:BoundingBox, percent_area:float):
        self.label = label
        self.bbox = bbox
        self.confidence = confidence
        self.percent_area = percent_area

class AbstractObjectDetector(abc.ABC):

    @abstractmethod
    def detect_objects(self,images:list[np.array], **kwargs) -> list[list[ObjectDetection]]:
        """
        Process the list of images to produce a list of the same size in 1:1 correspondence, containing
        lists of detected objects from associated images.

        Parameters:
        -----------
            images - list of 2-dimensional numpy arrays decoded from a stored images.
                MORE HERE: what about the depth of the image?
            kwargs - implementation-specific arguments, for example to set thresholds on confidence.

        Return
        ------
            A list, in 1:1 correspondence with the input list, of lists.  Each contained list is a
            list of object detections found within the corresponding image.  The list of object detections must
            be sorted from first to last by confidence.
        """
        raise NotImplementedError