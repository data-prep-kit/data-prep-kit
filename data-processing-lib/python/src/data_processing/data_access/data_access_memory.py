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

from typing import Any
import pyarrow as pa
from data_processing.data_access import DataAccess
from data_processing.utils import get_logger


class DataAccessMemory(DataAccess):
    """
    Implementation of the Base Data access class for in memory data access.
    """

    def __init__(
            self,
            checkpoint: bool = False,
    ):
        """
        Create data access class for folder based configuration
        :param path_config: dictionary of path info
        """
        self.tables = {}
        self.checkpoint = checkpoint
        self.logger = get_logger(__name__)

        self.logger.debug(f"Local checkpoint: {self.checkpoint}")

    def get_table(self, path: str) -> tuple[pa.table, int]:
        """
        Get pyArrow table for a given path
        :param path - file path
        :return: pyArrow table or None, if the table read failed and number of operation retries.
                 Retries are performed on operation failures and are typically due to the resource overload.
        """
        return self.tables.get(path, None), 0

    def save_table(self, path: str, table: pa.Table) -> tuple[int, dict[str, Any], int]:
        """
        Saves a pyarrow table into a member variable

        Args:
            table (pyarrow.Table): The pyarrow table to save.
            path (str): The path is ignored

        Returns:
            tuple: A tuple containing:
                - size_in_memory (int): The size of the table in memory (bytes).
                - file_info (dict or None): An empty dictionary.
        """
        self.tables[path] = table
        # Get table size in memory
        size_in_memory = table.nbytes
        return size_in_memory, {}, 0

    def get_output_folder(self) -> str | None:
        """
        Get output folder as a string
        :return: output_folder
        """
        return None

    def table_to_buffer(table: pa.Table) -> Any:
        """
        Serialize a table into a buffer
        :param table pyarrow table to be seraialized
        :return byte buffer with the table content
        """
        return table.to_pydict()

    def table_from_buffer(buffer: Any) -> pa.Table:
        """
        Deserialize a table from the given buffer
        :param buffer byte buffer with the table content
        :return pyarrow table to be seraialized
        """
        return pa.Table.from_pydict(buffer)
