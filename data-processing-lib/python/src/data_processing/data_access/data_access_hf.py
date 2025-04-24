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

import gzip
import json
import os
from pathlib import Path
from typing import Any

import pyarrow as pa
from huggingface_hub import HfFileSystem, RepoCard
from huggingface_hub.errors import EntryNotFoundError
from data_processing.data_access import DataAccess
from data_processing.utils import TransformUtils, get_logger


logger = get_logger(__name__)


class DataAccessHF(DataAccess):
    """
    Implementation of the Base Data access class for local folder data access.
    """

    def __init__(
        self,
        hf_config: dict[str, str] = None,
        d_sets: list[str] = None,
        checkpoint: bool = False,
        m_files: int = -1,
        n_samples: int = -1,
        files_to_use: list[str] = [".parquet"],
        files_to_checkpoint: list[str] = [".parquet"],
    ):
        """
        Create data access class for folder based configuration
        :param hf_config: dictionary of path info
        :param d_sets list of the data sets to use
        :param checkpoint: flag to return only files that do not exist in the output directory
        :param m_files: max amount of files to return
        :param n_samples: amount of files to randomly sample
        :param files_to_use: files extensions of files to include
        :param files_to_checkpoint: files extensions of files to use for checkpointing
        """
        super().__init__(d_sets=d_sets, checkpoint=checkpoint, m_files=m_files, n_samples=n_samples,
                         files_to_use=files_to_use, files_to_checkpoint=files_to_checkpoint)
        if hf_config is None:
            self.input_folder = None
            self.output_folder = None
        else:
            self.input_folder = hf_config["input_folder"]
            if self.input_folder[-1] == "/":
                self.input_folder = self.input_folder[:-1]
            self.output_folder = hf_config["output_folder"]
            if self.output_folder[-1] == "/":
                self.output_folder = self.output_folder[:-1]
        self.hf_config = hf_config
        self.fs = HfFileSystem(token=hf_config["hf_token"])

        logger.debug(f"hf input folder: {self.input_folder}")
        logger.debug(f"hf output folder: {self.output_folder}")
        logger.debug(f"hf data sets: {self.d_sets}")
        logger.debug(f"hf checkpoint: {self.checkpoint}")
        logger.debug(f"hf m_files: {self.m_files}")
        logger.debug(f"hf n_samples: {self.n_samples}")
        logger.debug(f"hf files_to_use: {self.files_to_use}")
        logger.debug(f"hf files_to_checkpoint: {self.files_to_checkpoint}")

    def get_output_folder(self) -> str:
        """
        Get output folder as a string
        :return: output_folder
        """
        return self.output_folder

    def get_input_folder(self) -> str:
        """
        Get input folder as a string
        :return: input_folder
        """
        return self.input_folder

    def _get_file_size(self, path: str) -> int:
        """
        Get file size in bytes
        :param path: file path
        :return: file size in bytes
        """
        return self.fs.info(path=path)['size']

    def _list_files_folder(self, path: str) -> tuple[list[dict[str, Any]], int]:
        """
        Get files for a given folder and all sub folders
        :param path: path
        :return: List of files
        """
        files = sorted(self.fs.glob(path=f"{path}/**/*.*"))
        res = [{"name": file, "size": self._get_file_size(file)} for file in files]
        return res, 0

    def _get_folders_to_use(self) -> tuple[list[str], int]:
        """
        convert data sets to a list of folders to use
        :return: list of folders and retries
        """
        folders_to_use = []
        files = self.fs.ls(path=self.input_folder)
        dirs = [f['name'] for f in files if f['type'] == 'directory']

        for file in dirs:
            for s_name in self.d_sets:
                if file.endswith(s_name):
                    folders_to_use.append(file)
                    break
        return folders_to_use, 0

    def get_table(self, path: str) -> tuple[pa.table, int]:
        """
        Attempts to read a PyArrow table from the given path.

        Args:
            path (str): Path to the file containing the table.

        Returns:
            pyarrow.Table: PyArrow table if read successfully, None otherwise.
        """

        try:
            data, retries = self.get_file(path=path)
            return TransformUtils.convert_binary_to_arrow(data=data), retries
        except Exception as e:
            logger.error(f"Error reading table from {path}: {e}")
            return None, 0

    def save_table(self, path: str, table: pa.Table) -> tuple[int, dict[str, Any], int]:
        """
        Saves a pyarrow table to a file and returns information about the operation.

        Args:
            table (pyarrow.Table): The pyarrow table to save.
            path (str): The path to the output file.

        Returns:
            tuple: A tuple containing:
                - size_in_memory (int): The size of the table in memory (bytes).
                - file_info (dict or None): A dictionary containing:
                    - name (str): The name of the file.
                    - size (int): The size of the file (bytes).
                If saving fails, file_info will be None.
        """
        # Get table size in memory
        try:
            # Write the table to parquet format
            data = TransformUtils.convert_arrow_to_binary(table=table)
            finfo, retries = self.save_file(path=path, data=data)
            return len(data), finfo, retries

        except Exception as e:
            logger.error(f"Error saving table to {path}: {e}")
            return -1, None, 0

    def save_job_metadata(self, metadata: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """
        Save metadata
        :param metadata: a dictionary, containing the following keys:
            "pipeline",
            "job details",
            "code",
            "job_input_params",
            "execution_stats",
            "job_output_stats"
        two additional elements:
            "source"
            "target"
        are filled bu implementation
        :return: a dictionary as
        defined https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
        in the case of failure dict is None
        """
        if self.output_folder is None:
            logger.error("hf configuration is not defined, can't save metadata")
            return None, 0
        metadata["source"] = {"name": self.input_folder, "type": "path"}
        metadata["target"] = {"name": self.output_folder, "type": "path"}
        return self.save_file(
            path=f"{self.output_folder}/metadata.json",
            data=json.dumps(metadata, indent=2).encode(),
        )

    def get_file(self, path: str) -> tuple[bytes, int]:
        """
        Gets the contents of a file as a byte array, decompressing gz files if needed.

        Args:
            path (str): The path to the file.

        Returns:
            bytes: The contents of the file as a byte array, or None if an error occurs.
        """

        try:
            with self.fs.open(path=path, mode="rb") as f:
                return f.read(), 0
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise e

    def save_file(self, path: str, data: bytes) -> tuple[dict[str, Any], int]:
        """
        Saves bytes to a file and returns a dictionary with file information.

        Args:
            data (bytes): The bytes data to save.
            path (str): The full name of the file to save.

        Returns:
            dict or None: A dictionary with "name" and "size" keys if successful,
                        or None if saving fails.
        """
        # make sure that token is defined
        if self.hf_config["hf_token"] is None:
            logger.warning("Writing file is only supported when HF_TOKEN is defined")
            return None, 0
        try:
            with self.fs.open(path=path, mode="wb") as f:
                f.write(data)
            file_info = {"name": path, "size": self.fs.info(path=path)['size']}
            return file_info, 0
        except Exception as e:
            logger.error(f"Error saving bytes to file {path}: {e}")
            return None, 0

    def get_dataset_card(self, ds_name: str) -> RepoCard:
        """
        Get the Repo card for the data set
        :param ds_name: data set name in the format owner/ds_name
        :return: DS card object
        """
        # get file location
        if ds_name[-1] == "/":
            path = f"datasets/{ds_name[:-1]}/README.md"
        else:
            path = f"datasets/{ds_name}/README.md"
        # read README file
        try:
            with self.fs.open(path=path, mode="r", newline="", encoding="utf-8") as f:
                data = f.read()
        except Exception as e:
            logger.warning(f"Failted to read README file {e}")
            return None
        # convert README to Repo card
        return RepoCard(content=data)

    def update_data_set_card(self, ds_name: str, content: str) -> None:
        """
        Update Repo card
        :param ds_name: data set name in the format owner/ds_name
        :param content: new readme content
        :return: None
        """
        # make sure that token is defined
        if self.hf_config["hf_token"] is None:
            raise Exception("Update data set card is only supported when HF_TOKEN is defined")
        # get file location
        if ds_name[-1] == "/":
            path = f"datasets/{ds_name[:-1]}/README.md"
        else:
            path = f"datasets/{ds_name}/README.md"
        # delete current Readme file
        try:
            self.fs.rm(path=path)
        except EntryNotFoundError:
            # If the README file does not exist, ignore
            logger.warning(f"Data set {ds_name} does not have README file")
        except Exception as e:
            logger.warning(f"Failted to delete README file {e}")
            raise e
        # write new Readme file
        try:
            with self.fs.open(path=path, mode="w", newline="", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.warning(f"Failted to save README file {e}")
            raise e

