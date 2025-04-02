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

import json
from typing import Any

import pyarrow
from data_processing.data_access import DataAccess, DataAccessS3
from data_processing.utils import TransformUtils, get_logger
logger = get_logger(__name__)

try:
    from lakehouse import (
        ColumnFilter,
        CosCredentials,
        Datasource,
        JobDetails,
        JobStats,
        LakehouseForProcessingTask,
        SourceCodeDetails,
    )
except ModuleNotFoundError:
    logger.error("When building the environment with a dependency on an exteral library, the EXTRA_INDEX_URL must be defined.")
    logger.error("example: export EXTRA_INDEX_URL=https://${ARTIFACTORY_USER}:${ARTIFACTORY_API_KEY}@na.artifactory.swg-devops.com/artifactory/api/pypi/res-data-engineering-team-pypi-local/simple")
    raise
    
from lakehouse.utils import convert_pyarrow_to_iceberg
from pyiceberg.io.pyarrow import schema_to_pyarrow

from data_processing.utils import DPKConfig




class DPKConfigLH(DPKConfig):

    S3_ACCESS_KEY = DPKConfig._get_first_env_var(["DPL_S3_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "COS_ACCESS_KEY"])
    """ Set from DPL_S3_ACCESS_KEY, AWS_ACCESS_KEY_ID or COS_ACCESS_KEY env vars """
    S3_SECRET = DPKConfig._get_first_env_var(["DPL_S3_SECRET_KEY", "AWS_SECRET_ACCESS_KEY", "COS_SECRET_KEY"])
    """ Set from DPL_S3_SECRET_KEY, AWS_SECRET_ACCESS_KEY or COS_SECRET_KEY env vars """
    S3_ENDPOINT = DPKConfig._get_first_env_var(["DPL_S3_ENDPOINT", "S3_ENDPOINT"])
    """ Set from DPL_LAKEHOUSE_TOKEN or LAKEHOUSE_TOKEN env vars """
    LAKEHOUSE_TOKEN = DPKConfig._get_first_env_var(["DPL_LAKEHOUSE_TOKEN"])
    """ Set from DPL_LAKEHOUSE_TOKEN or LAKEHOUSE_TOKEN env vars """



class DataAccessLakeHouse(DataAccess):
    """
    Implementation of the Base Data access class for lakehouse-based data access
    """

    @classmethod
    def validate_config(cls, config: dict[str, str], prefix: str='data_') -> bool:
        """
        Validate that
        :param lh_config: dictionary of local config
        :return: True if s3l config is valid, False otherwise
        """
        valid_config = True
        if config.get("input_table", "") == "":
            valid_config = False
            logger.error(f"prefix '{prefix}': Could not find input table in lh config")
        if config.get("input_dataset", None) is None:
            # Note data set can be an empty string
            valid_config = False
            logger.error(f"prefix '{prefix}': Could not find input_dataset in lh config")
        if config.get("input_version", "") == "":
            valid_config = False
            logger.error(f"prefix '{prefix}': Could not find input_version in lh config")
        if config.get("output_table", "") == "":
            valid_config = False
            logger.error(f"prefix '{prefix}': Could not find output_table in lh config")
        if config.get("output_path", "") == "":
            valid_config = False
            logger.error(f"prefix '{prefix}': Could not find output_path in lh config")
        if config.get("lh_environment", "") == "":
            valid_config = False
            logger.error(f"prefix '{prefix}': Could not find lh_environment in lh config")
        return valid_config


#    def __init__(
#        self,
#        config: dict[str, str] = None,
#        d_sets: list[str] = None,
#        checkpoint: bool = False,
#        m_files: int = -1,
#        n_samples: int = 1,
#        files_to_use: list[str] = [".parquet"],
#    ):

    def __init__(self, **kwargs):
        """
        Create data access class for lake house based configuration
        :param s3_credentials: dictionary of cos credentials
        :param lakehouse_config: dictionary of lakehouse info
        :param d_sets list of the data sets to use
        :param checkpoint: flag to return only files that do not exist in the output directory
        :param m_files: max amount of files to return
        :param n_samples: amount of files to randomly sample
        :param files_to_use: files extensions of files to include
        """
        config=kwargs.get('config', None)
        d_sets=kwargs.get('d_sets', None)
        checkpoint=kwargs.get('checkpoint', False)
        m_files=kwargs.get('m_files', -1)
        n_samples=kwargs.get('n_samples', 1)
        files_to_use=kwargs.get('files_to_use', [".parquet"])

        self.logger = get_logger(__name__)
        if config is None:
            self.output_folder = None
        else:
            cos_cred = CosCredentials(
                key=DPKConfigLH.S3_ACCESS_KEY,
                secret=DPKConfigLH.S3_SECRET,
                region="us-east",
                endpoint=DPKConfigLH.S3_ENDPOINT,
            )
            # API reference
            # https://pages.github.ibm.com/arc/dmf-library/code_reference/pythonic_access/usage/lakehouse_support_for_ray_processing_jobs/#lakehouse-for-pre-processing-tasks
            self.lh = LakehouseForProcessingTask(
                input_table_name=config["input_table"],
                version=config["input_version"],
                output_table_name=config["output_table"],
                output_path=config["output_path"],
                token=config.get("token", DPKConfigLH.LAKEHOUSE_TOKEN),
                environment=config["lh_environment"],
                cos_credentials=cos_cred,
            )
            self.partition_filter = []
            if len(config["input_dataset"]) > 2:
                # input_dataset is not empty, split the text string for partition_filter
                for pair in config["input_dataset"].split(","):
                    partition_name = pair.split(":")[0]
                    partition_value = pair.split(":")[1]
                    self.partition_filter.append(ColumnFilter(name=partition_name, value=partition_value))
                self.lh = LakehouseForProcessingTask(
                    input_table_name=config["input_table"],
                    partition_filter=self.partition_filter,
                    # dataset=lakehouse_config["input_dataset"],
                    version=config["input_version"],
                    output_table_name=config["output_table"],
                    output_path=config["output_path"],
                    token=config.get("token", DPKConfigLH.LAKEHOUSE_TOKEN),
                    environment=config["lh_environment"],
                    cos_credentials=cos_cred,
                )
            self.output_folder = self.lh.get_output_data_path()
        self.S3 = DataAccessS3(
            config={
                "input_folder": self.lh.get_input_data_path(),
                "output_folder": self.output_folder,
                "access_key": DPKConfigLH.S3_ACCESS_KEY,
                "secret_key": DPKConfigLH.S3_SECRET,
                "url": DPKConfigLH.S3_ENDPOINT,
            },
            d_sets=d_sets,
            checkpoint=checkpoint,
            m_files=m_files,
            n_samples=n_samples,
            files_to_use=files_to_use,
        )
        self.checkpoint = checkpoint
        self.n_samples = n_samples
        self.m_files = m_files

    def get_num_samples(self) -> int:
        """
        Get number of samples for input
        :return: Number of samples
        """
        return self.n_samples

    def get_output_folder(self) -> str:
        """
        Get output folder as a string
        :return: output_folder
        """
        return self.output_folder

    def _get_files_to_process_internal(self) -> tuple[list[str], dict[str, float], int]:
        """
        Get files to process
        :return: list of files and a dictionary of the files profile:
            "max_file_size_MB",
            "min_file_size_MB",
            "avg_file_size_MB",
            "total_file_size_MB"
        """
        if len(self.partition_filter) > 0:
            if self.checkpoint:
                import os
                input_folder_path = self.lh.get_input_data_path()
                filelist = [os.path.join(input_folder_path, f) for f in self.lh.diff_parquet_input_output()]
                # filelist = self.lh.diff_parquet_input_output()
            else:
                filelist = self.lh.get_input_file_paths()
            profile = {
                "max_file_size_MB": 150,
                "min_file_size_MB": 150,
                "avg_file_size_MB": 150,
                "total_file_size_MB": 150 * len(filelist),
            }
            if self.m_files == -1:
                return filelist, profile, 0
            else:
                return filelist[: self.m_files], profile, 0
        else:
            return self.S3.get_files_to_process()

    def get_table(self, path: str) -> tuple[pyarrow.table, int]:
        """
        Get pyArrow table for a given path
        :param path - file path
        :return: pyArrow table or None, if the table read failed
        """
        return self.S3.get_table(path=path)

    def get_output_location(self, path: str) -> str:
        """
        Get output location based on input
        :param path: input file location
        :return: output file location
        """
        if self.output_folder is None:
            logger.error("Getting output location. Lake house is not configured, returning None")
            return None
        return self.lh.get_output_file_path_from(file_path=path)

    @staticmethod
    def _add_table_metadata(table: pyarrow.Table) -> pyarrow.Table:
        """
        Save table to a given location fixing schema, required for lakehouse
        :param table: table
        :return: size of table in memory and a dictionary as
        defined https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
        in the case of failure dict is None
        """
        # update schema to ensure part ids to be there
        # fields = []
        # columns = table.column_names
        # tbl_metadata = table.schema.metadata
        # if tbl_metadata is None:
        # If the table does not have metadata, create the empty one
        #    tbl_metadata = {}
        # Add column Ids to the metadata
        # for index in range(len(table.column_names)):
        #    field = table.field(index)
        #    fields.append(field.with_metadata({"PARQUET:field_id": f"{index + 1}"}))
        #    tbl_metadata[columns[index]] = json.dumps({"PARQUET:field_id": f"{index + 1}"}).encode()
        # Rebuild schema and table
        # schema = pyarrow.schema(fields, metadata=tbl_metadata)
        # return pyarrow.Table.from_arrays(arrays=list(table.itercolumns()), schema=schema)

        iceberg_schema = convert_pyarrow_to_iceberg(table.schema)
        arrow_schema = schema_to_pyarrow(iceberg_schema)
        return pyarrow.Table.from_arrays(arrays=list(table.itercolumns()), schema=arrow_schema)

    def save_table(self, path: str, table: pyarrow.Table) -> tuple[int, dict[str, Any]]:
        """
        Save table to a given location
        :param path: location to save table
        :param table: table
        :return: size of table in memory and a dictionary as
        defined https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
        in the case of failure dict is None
        """
        if self.output_folder is None:
            logger.error("Saving table. Lake house is not configured, operation skipped")
            return 0, None
        # Add metadata to the table
        table_with_metadata = self._add_table_metadata(table=table)
        # Save table to S3
        l, res, retries = self.S3.save_table(path=path, table=table_with_metadata)
        # logger.info(f"{path}, {l}, {res}, {retries}")
        # if repl is None:
        #    return l, {}

        # check if table exists and create output table using schema from pyarrow table
        self.lh.check_and_create_output_table_from_pyarrow(table)
        # update output Iceberg table
        status = self.lh.update_table(path)
        # logger.info(f"{status}")
        return l, retries

    def save_job_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Save metadata
        :param metadata: a dictionary, containing the following keys
        (see https://github.ibm.com/arc/dmf-library/issues/158):
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
            logger.error("Lake house is not configured, save job metadata operation skipped")
            return None
        metadata["source"] = {
            "name": self.lh.input_table_name,
            "type": "table",
            "snapshot_id": str(self.lh.get_input_table_metadata().snapshot_id),
            "dataset": self.lh.dataset,
            "version": self.lh.version,
            "path": self.S3.input_folder,
            "extra": {"partition_filter": json.dumps([ob.__dict__ for ob in self.partition_filter])},
        }
        metadata["target"] = {
            "name": self.lh.output_table_name,
            "type": "table",
            "snapshot_id": str(self.lh.get_output_table_metadata().snapshot_id),
            "dataset": self.lh.dataset,
            "version": self.lh.version,
            "path": self.lh.output_path,
        }
        l, repl = self.S3.save_file(
            path=f"{self.S3.output_folder.rstrip('/')}/metadata.json", data=json.dumps(metadata, indent=2).encode()
        )
        if repl is None:
            return repl
        # Save metadata to LH
        source_name = self.lh.dataset
        target_name = self.lh.dataset
        if self.lh.dataset == "":
            source_name = self.lh.input_table_name.split(".")[-1]
            target_name = self.lh.output_table_name.split(".")[-1]

        stats = JobStats(
            release_id=metadata["pipeline"],
            job_details=JobDetails(
                id=metadata["job details"]["job id"],
                name=metadata["job details"]["job name"],
                type=metadata["job details"]["job type"],
                category=metadata["job details"]["job category"],
                status=metadata["job details"]["status"],
                started_at=metadata["job details"]["start_time"],
                completed_at=metadata["job details"]["end_time"],
            ),
            source_code_details=SourceCodeDetails(
                url=metadata["code"]["github"],
                commit_hash=metadata["code"]["commit_hash"],
                path=metadata["code"]["path"],
            ),
            # updated to support DMF-Lib=1.5
            sources=[
                Datasource(
                    name=self.lh.input_table_name,
                    table=self.lh.input_table_name,
                    # type="dataset",
                    type="table",
                    snapshot_id=metadata["source"]["snapshot_id"],
                    # name=source_name,
                    version=self.lh.version,
                    path=[metadata["source"]["path"]],
                    extra={"partition_filter": json.dumps([ob.__dict__ for ob in self.partition_filter])},
                )
            ],
            targets=[
                Datasource(
                    name=self.lh.output_table_name,
                    table=self.lh.output_table_name,
                    # type="dataset",
                    type="table",
                    snapshot_id=metadata["target"]["snapshot_id"],
                    # name=target_name,
                    version=self.lh.version,
                    path=[metadata["target"]["path"]],
                )
            ],
            job_input_params=metadata["job_input_params"],
            execution_stats=metadata["execution_stats"],
            job_output_stats=metadata["job_output_stats"],
        )
        self.lh.save_stats(stats)

    def get_file(self, path: str) -> bytes:
        """
        Get file as a byte array
        :param path: file path
        :return: bytes array of file content
        """
        return self.S3.get_file(path)

    def save_file(self, path: str, data: bytes) -> dict[str, Any]:
        """
        Save byte array to the file
        :param path: file path
        :param data: byte array
        :return: a dictionary as
        defined https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
        in the case of failure dict is None
        """
        # return self.S3.save_file(path=path, data=data)
        table = TransformUtils.convert_binary_to_arrow(data=data)
        if self.output_folder is None:
            logger.error("Saving table. Lake house is not configured, operation skipped")
            return None

        return self.save_table(path, table)

        """
        # Add metadata to the table
        table_with_metadata = self._add_table_metadata(table=table)
        # Save table to S3
        _, repl = self.S3.save_table(path=path, table=table_with_metadata)
        if repl is None:
            return {}

        # check if table exists and create output table using schema from pyarrow table
        self.lh.check_and_create_output_table_from_pyarrow(table)
        # update output Iceberg table
        self.lh.update_table(path)
        # logger.debug(f"saved file: {path}")
        return l, repl
        """

    def get_folder_files(self, path: str, extensions: list[str] = None, return_data: bool = True) -> dict[str, bytes]:
        """
        Get a list of byte content of files. The path here is an absolute path and can be anywhere.
        The current limitation for S3 and Lakehouse is that it has to be in the same bucket
        :param path: file path
        :param extensions: a list of file extensions to include. If None, then all files from this and
                           child ones will be returned
        :param return_data: flag specifying whether the actual content of files is returned (True), or just
                            directory is returned (False)
        :return: A dictionary of file names/binary content will be returned
        """
        return self.S3.get_folder_files(path=path, extensions=extensions, return_data=return_data)
