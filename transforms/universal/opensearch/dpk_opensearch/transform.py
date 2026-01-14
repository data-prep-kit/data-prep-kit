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

import pyarrow as pa
from typing import Any, Dict
import warnings
import os
import json
from urllib3.exceptions import InsecureRequestWarning
from argparse import ArgumentParser, Namespace
from datetime import datetime, timezone

from opensearchpy import OpenSearch, helpers

from data_processing.transform import AbstractTableTransform, TransformConfiguration, SinkHandler
from data_processing.utils import CLIArgumentProvider
from data_processing.utils import UnrecoverableException, get_dpk_logger

# Suppress SSL warnings for self-signed certificates
warnings.simplefilter('ignore', InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Connecting to .* using SSL with verify_certs=False is insecure')

endpoint = "endpoint"
indx = "index"
docid_column_name_key = "document_id_column_name"
dimension_size = "dimension_size"
content_column_name_key = "content_column_name"
embeddings_column_name_key = "embeddings_column_name"
filename_column_name_key = "filename"
delete_index = "delete_index"
disable_security = "disable_security"
verify_certs = "verify_certs"
vector_method = "vector_method"

short_name = "os"
cli_prefix = f"{short_name}_"

endpoint_cli_param = f"{cli_prefix}{endpoint}"
index_cli_param = f"{cli_prefix}{indx}"
docid_cli_param = f"{cli_prefix}{docid_column_name_key}"
embeddings_cli_param = f"{cli_prefix}{embeddings_column_name_key}"
dimension_size_cli_param = f"{cli_prefix}{dimension_size}"
content_column_name_cli_param = f"{cli_prefix}{content_column_name_key}"
delete_index_cli_param = f"{cli_prefix}{delete_index}"
disable_security_cli_param = f"{cli_prefix}{disable_security}"
verify_certs_cli_param = f"{cli_prefix}{verify_certs}"
vector_method_cli_param = f"{cli_prefix}{vector_method}"

default_endpoint = "localhost:9200"
default_port = "9200"
default_docid_column_name = "document_id"
default_embeddings_column_name = "embeddings"
default_content_column_name = "contents"
default_filename = "filename"
default_delete_index = False
default_disable_security = False
default_verify_certs = False
default_username = "admin"

user = os.environ.get("OPENSEARCH_USERID", default_username)

class OpenSearchTransform(AbstractTableTransform, SinkHandler):

    def __init__(self, config: dict[str, Any]):
        def set_client() -> None:
            """
            Set OpenSearch client. Through exception if an error occurs.
            """
            try:
                if self.disable_security is True:
                    self.logger.info("OpenSearch security is disabled")
                    self.client = OpenSearch(
                        hosts=[{'host': self.host, 'port': self.port}],
                        http_compress=True,  # enables gzip compression for request bodies
                    )
                else:
                    self.logger.info("OpenSearch security is enabled")
                    try:
                        pwd = os.getenv("OPENSEARCH_PASSWORD")
                    except KeyError as e:
                        self.logger.error(
                            f"Environment variable OPENSEARCH_PASSWORD must be define. Raising Exception: {e}")
                        raise UnrecoverableException("Missing credentials")
                    user_name = os.environ.get("OPENSEARCH_USERID", "admin")
                    self.client = OpenSearch(
                        hosts=[{'host': self.host, 'port': self.port}],
                        http_compress=True,  # enables gzip compression for request bodies
                        http_auth=(user_name, pwd),
                        use_ssl=True,
                        # Set to True for production environments and provide appropriate CA certificates
                        verify_certs=self.verify_certs,
                        sl_assert_hostname=False,
                        ssl_show_warn=False
                    )
            except Exception as e:
                self.logger.error(f"Failed to create OpenSearch client due to {e}")
                raise UnrecoverableException(f"Failed to create OpenSearch client due to {e}")

        super().__init__(config)
        self.logger = get_dpk_logger()
        x = config.get(endpoint_cli_param, default_endpoint).split(':')

        self.doc_id_column = config.get(docid_column_name_key, default_docid_column_name)
        self.index_name = config.get(indx, f"dpk_{datetime.now().strftime('%y%m%d%H%M%S')}")
        self.embeddings_column = config.get(embeddings_column_name_key, default_embeddings_column_name)
        self.content_column = config.get(content_column_name_key , default_content_column_name)
        self.dimension_size = config.get(dimension_size)
        self.delete_index = config.get(delete_index, default_delete_index)
        self.verify_certs = config.get(verify_certs, False)
        self.disable_security = config.get(disable_security, False)
        self.vector_method = config.get(vector_method, None)
        self.apply_knn = False

        self.host = x[0]
        self.port = x[1] if len(x) > 1 else default_port
        set_client()

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Insert data into an OpenSearch vector index. Create the index if it does not exist.
        If an embeddings column is present, a k-NN vector index is created; otherwise, a regular index is used.

        :param table: input table
        """
        self.logger.info(f"Transforming one table with {len(table)} rows")
        if self.delete_index:
            self.logger.info("Drop index initiated as the delete index option is specified")
            self.drop_index()

        if self.embeddings_column in table.schema.names:
            self.logger.info(f"Column {self.embeddings_column} exists, apply k-NN index")
            if not self.dimension_size:
                self.dimension_size = len(table[self.embeddings_column][0].as_py())
            self.apply_knn = True
        else:
            self.logger.info(f"Column {self.embeddings_column} does not exist, creating a regular index")

        if filename_column_name_key not in table.schema.names:
            filename = os.path.basename(file_name)
            self.logger.info(f"{filename_column_name_key} column is missing, add it with the value {filename}")
            new_col = pa.array([filename] * len(table))
            table = table.append_column(filename_column_name_key, new_col)

        ts = datetime.now(timezone.utc)
        ts_col = pa.array([ts] * len(table), type=pa.timestamp('ns', tz='UTC'))
        table = table.append_column('transformtimestamp', ts_col)
        docs = table.to_pylist()

        success, failed = self.store_data(docs)

        metadata = {"rows_processed": table.num_rows,
                    "rows_inserted": success,
                    "rows_failed": len(failed),
                    }
        return [], metadata

    def create_index(self, body: Any = None) -> None:
        """
        Create an index. Through exception if the index already exists or an error occurs.
        :param body: The configuration for the index (`settings` and mappings`)
        """
        try:
            self.client.indices.create(index=self.index_name, body=body)
            self.logger.info(f"index {self.index_name} created")
        except Exception as e:
            self.logger.error(f"Failed to create index {self.index_name} due to {e}")
            raise e

    def get_knn_configuration(self) -> Any:
        """
        Get knn configuration
        :return: The configuration for the index (`settings` and `mappings`)
        """
        if not self.dimension_size:
            self.logger.error("dimension_size is missing")
            raise UnrecoverableException

        try:
            # Create a new index
            index_body = {
                "settings": {
                    "index.knn": True
                },
                "mappings": {
                    "properties": {
                        self.embeddings_column: {
                            "type": "knn_vector",
                            "dimension": self.dimension_size
                        }
                    }
                }
            }
            if self.vector_method:
                index_body["mappings"]["properties"][self.embeddings_column]["method"] = json.loads(self.vector_method)
            return  index_body
        except Exception as e:
            self.logger.error(f"Failed to create knn index {self.index_name} configuration due to {e}")
            raise e

    def get_actions(self, docs: list[dict]) -> list:
        """
        Get the actions to be executed.

        :param docs: The documents to index
        :return: Iterable containing the actions to be executed
        """
        try:
            actions = [
                {
                    '_op_type': 'index',
                    '_index': self.index_name,
                    **({"_id": doc[self.doc_id_column]} if self.doc_id_column in doc else {}),
                    '_source': doc
                }
                for doc in docs
            ]
            return actions
        except Exception as e:
            self.logger.error(f"Failed to get actions due to {e}")
            raise UnrecoverableException(f"Failed to get actions due to {e}")

    def store_data(self, docs: list[dict]) -> tuple[int, int]:
        """
        Creates an index (k-NN vector index or regular index) and writes the data.
        The index is created only if it does not already exist.
        Throw an exception if error occurs.
        :param docs: the documents to index
        :return: A tuple containing the number of success and failed docs.
        """
        index_exists = self.check_index()
        if index_exists:
            self.logger.info(f"index {self.index_name} exists")
        else:
            config = None
            self.logger.debug(f"index {self.index_name} does not exist, creating it")
            if self.apply_knn:
                config = self.get_knn_configuration()
            self.create_index(body=config)

        actions = self.get_actions(docs)
        try:
            success, failed = helpers.bulk(client=self.client, actions=actions, stats_only=False, refresh="wait_for")
        except Exception as e:
            self.logger.error(f"Failed to index documents into index {self.index_name} due to {e}")
            raise UnrecoverableException(f"Failed to index documents into index {self.index_name} due to {e}")

        self.logger.info(f"Successfully indexed {success} documents into index {self.index_name} ")
        if len(failed) > 0:
            self.logger.error(f"Failed to index {len(failed)} documents into index {self.index_name} ")

        return success, failed

    def check_index(self) -> bool:
        """
        Checks whether the index exists.
        Through an exception if error occurs.
        :return: True if index exists. Otherwise, returns false.
        """
        try:
            return self.client.indices.exists(index=self.index_name)
        except Exception as e:
            self.logger.error(f"An error occurred while checing the index: {e}")
            raise e

    def drop_index(self) -> None:
        """
        Drop the index if it exists. If the index does not exist, no action is taken.
        An exception is raised if an error occurs.
        """
        index_exists = self.check_index()
        if index_exists:
            try:
                self.client.indices.delete(index=self.index_name)
                self.logger.info(f"Deleted index {self.index_name}")
            except Exception as e:
                self.logger.error(f"An error occurred while deleting the index: {e}")
                raise e
        else:
            self.logger.info(f"Index {self.index_name} does not exist. Nothing to delete.")

    def delete_documents(self, docs_to_delete: list[str]) -> Dict[str, Any]:
        """
        Delete documents from OpenSearch index. If the documents do not exist, no action is taken.
        An exception is raised if an error occurs.

        :param: docs_to_delete: list of filenames to delete.
        :return: Dictionary of statistics about the deletion.
        """
        deleted_count = 0
        failed_files = []
        not_found_files = []
        try:
            for doc in docs_to_delete:
                try:
                    filename = os.path.basename(doc)
                    result = self.delete_docs_by_field_value(field_name=filename_column_name_key, value=filename)
                    if result > 0:
                        deleted_count += 1
                    else:
                        not_found_files.append(filename)
                except Exception as e:
                    failed_files.append(filename)
                    print(f"Failed to delete {filename}: {e}")

            return {
                "success": len(failed_files) == 0,
                "deleted_count": deleted_count,
                "failed": failed_files,
                "not_found": not_found_files,
                "details": {"index": self.config.get("index", "unknown")}
            }
        except Exception as e:
            return {
                "success": False,
                "deleted_count": 0,
                "failed": doc,
                "details": {"error": str(e)}
            }

    def delete_docs_by_field_value(self, field_name: str, value: Any) -> int:
        """
        Delete all docs where the field field_name matches the given value param.

        :param field_name: The name of the field in the document to match on.
        :param value: The value to compare against field_name. Documents where field_name equals this value will be deleted.
        :return: the number of docs deleted.
        """
        if not field_name or not value:
            raise UnrecoverableException("Missing params to delete")
        self.logger.info(f"Delete all docs where the {field_name} field value is {value}")
        field_name_key = f"{field_name}.keyword"
        try:
            response = self.client.delete_by_query(
                index=self.index_name,
                refresh=True,
                body={
                    "query": {
                        "term": {
                            field_name_key: {
                                "value": value
                            }
                        }
                    }
                }
            )

            self.logger.info(
                f"Successfully deleted all {response['deleted']} rows from {field_name} "
                f"column with value '{value}' in {self.index_name} index")
            return response['deleted']
        except Exception as e:
            self.logger.error(f"An error occurred while deleting all rows from {field_name}"
                              f" column with value '{value}' in {self.index_name} index: {e}")
            raise e


class OpenSearchTransformConfiguration(TransformConfiguration):
    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=OpenSearchTransform,
            remove_from_metadata=[],
        )

        self.logger = get_dpk_logger()

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the OpenSearchTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        """
        parser.add_argument(
            f"--{endpoint_cli_param}",
            type=str,
            required=False,
            default=default_endpoint,
            help="Specify the OpenSearch host:port. Defaults to localhost:9200"
        )
        parser.add_argument(
            f"--{index_cli_param}",
            type=str,
            required=False,
            help="Specify the name of the OpenSearch Index to write. If the index does not already exist, it will be automatically created.",
        )
        parser.add_argument(
            f"--{docid_cli_param}",
            type=str,
            required=False,
            default=default_docid_column_name,
            help="Name of the table column that identy a unique document ID",
        )
        parser.add_argument(
            f"--{embeddings_cli_param}",
            type=str,
            required=False,
            default=default_embeddings_column_name,
            help="Embeddings Column name",
        )
        parser.add_argument(
            f"--{dimension_size_cli_param}",
            type=str,
            required=False,
            help="Embeddings length",
        )
        parser.add_argument(
            f"--{content_column_name_cli_param}",
            default=default_content_column_name,
            help="Column name to get content",
        )
        parser.add_argument(
            f"--{delete_index_cli_param}",
            default=default_delete_index,
            help="If set to true, the index will be deleted before the transform is applied. "
                 "If the index does not exist, no action is taken."
        )
        parser.add_argument(
            f"--{disable_security_cli_param}",
            default=False,
            help="If True, the OpenSearch server works without security checks and the client should use http, "
                 "without username and password. If False, OPENSEARH_USERID and OPENSEARCH_PASSWORD "
                 "environment variables must be defined.",
        )
        parser.add_argument(
            f"--{verify_certs_cli_param}",
            default=False,
            required=False,
            help="If True, the OpenSearch client and server should use correct SSL certificates.",
        )
        parser.add_argument(
            f"--{vector_method_cli_param}",
            type=str,
            required=False,
            help=('Vector index method parameters. For knn vector, it can be missed, '
                  'or see https://docs.opensearch.org/latest/mappings/supported-field-types/knn-methods-engines/'
                  ' for jVector,we use {"name": "disk_ann", "engine": "jvector", "space_type": "l2", "parameters": {"m": 32, "ef_construction": 200}}'),
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)

        self.params = self.params | captured
        self.logger.info(f"OpenSearch parameters are : {self.params}")
        return True
