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

from abc import ABC, abstractmethod
from typing import Any
class SinkHandler(ABC):
    """
    Abstract base class for handling document deletions.
    """

    @abstractmethod
    def delete_documents(self, docs_to_delete: list[str]) -> dict[str, Any]:
        """
        Delete documents.

        :param docs_to_delete: A list of filenames to delete
        :return: Returns dictionary of statistics about the deletion.
        """
        pass