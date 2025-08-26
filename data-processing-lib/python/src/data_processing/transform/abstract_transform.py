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
from pydantic import BaseModel
from typing import Any, ClassVar


class AbstractTransform(BaseModel, ABC):
    """
    Base class for all transform types
    """

    NAME: ClassVar[str] = "name"
    ID: ClassVar[str] = "id"
    DESCRIPTION: ClassVar[str] = "description"
    JOB_ID: ClassVar[str] = "job_id"
    JOB_RUN_ID: ClassVar[str] = "job_run_id"
    CONTEXT_ID: ClassVar[str] = "context_id"

    config: dict[str, Any]  # type hint for clarity and IDE support

    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        This simply stores the given instance in this instance for later use.
        """
        if config is None:
            raise ValueError("config cannot be None")

        self.config = config.copy()  # optional: copy to avoid mutating external dict
        self.config.setdefault(self.NAME, self.__class__.__name__)

    # Shared properties
    @property
    def name(self):
        return  self.config[self.NAME]

    @property
    def description(self):
        return self.config[self.DESCRIPTION]

    @property
    def id(self):
        return self.config[self.ID]

    @property
    def job_id(self):
        return self.config[self.JOB_ID]

    @property
    def job_run_id(self):
        return self.config[self.JOB_RUN_ID]

    @property
    def context_id(self):
        return self.config[self.CONTEXT_ID]


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

    def get_required_features(self):
        # The concrete subclasses will retrieve the required features.
        return []

    def get_feature(self, name, description, type, available_for_filter=False, available_for_vector_db=False, mandatory_for_vector_db=False):
        return {
            self.NAME: name,
            self.DESCRIPTION: description,
            self.TYPE: type,
            #OperatorConstants.AVAILABLE_FOR_FILTER: available_for_filter,
            #OperatorConstants.AVAILABLE_FOR_VECTOR_DB: available_for_vector_db,
            #OperatorConstants.MANDATORY_FOR_VECTOR_DB: mandatory_for_vector_db
        }
    def get_metadata_fields_to_accumulate(self) -> list[str]:
        """
        Return the metadata field names that needs to be accumulated.
        Subclasses should provide real implementation

        Returns:
            list[str]: List of field to be accumulated.
        """
        return []