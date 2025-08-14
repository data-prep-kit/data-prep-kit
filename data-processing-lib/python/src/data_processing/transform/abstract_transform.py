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

from abc import ABC, abstractmethod

class AbstractTransform(ABC):
    """
    Base class for all transform types
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_metadata(self) -> dict:
        """
        Return the transform matadata
        """
        pass

    @abstractmethod
    def validate(self, **kwargs) -> None:
        """
        Preform parameters validation.
        """
        pass

    @staticmethod
    def is_available() -> bool:
        """
        Disable the transform using this function.
        """
        return True
