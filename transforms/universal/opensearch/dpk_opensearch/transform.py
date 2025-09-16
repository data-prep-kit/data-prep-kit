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

import pyarrow as pa
from typing import Any
import warnings
import os
from urllib3.exceptions import InsecureRequestWarning
from argparse import ArgumentParser, Namespace
from datetime import datetime, timezone

from opensearchpy import OpenSearch, helpers

from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider
from data_processing.utils import UnrecoverableException, get_logger

# Suppress SSL warnings for self-signed certificates
warnings.simplefilter('ignore', InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Connecting to .* using SSL with verify_certs=False is insecure')

hostname = "host"
indx = "index"
docid_column_name_key = "document_id_column_name"
dimension_size = "dimension_size"
content_column_name_key = "content_column_name"
embeddings_column_name_key = "embeddings_column_name"
filename_column_name_key = "filename"
delete_index = "delete_index"

short_name = "os"
cli_prefix = f"{short_name}_"
host_cli_param = f"{cli_prefix}{hostname}"
indx_cli_param = f"{cli_prefix}{indx}"
docid_cli_param = f"{cli_prefix}{docid_column_name_key}"
embeddings_cli_param = f"{cli_prefix}{embeddings_column_name_key}"
dimension_size_cli_param = f"{cli_prefix}{dimension_size}"
content_column_name_cli_param = f"{cli_prefix}{content_column_name_key}"
delete_index_cli_param = f"{cli_prefix}{delete_index}"

default_host = "localhost:9200"
default_username = "admin"
default_port = "9200"
default_docid_column_name = "document_id"
default_embeddings_column_name = "embeddings"
default_content_column_name = "contents"
default_filename = "filename"
default_delete_index = False
user = os.environ.get("OPENSEARH_USERID", "admin")


class OpenSearchTransform(AbstractTableTransform):

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger(__name__)

        x = config.get(hostname, default_host).split(':')
        self.host = x[0]
        self.port = x[1] if len(x) > 1 else default_port
        self.doc_id_column = config.get(docid_column_name_key, default_docid_column_name)

        self.index_name = config.get(indx, f"dpk_{datetime.now().strftime('%y%m%d%H%M%S')}")
        self.embeddings_column = config.get(embeddings_column_name_key, default_embeddings_column_name)
        self.content_column = config.get(content_column_name_key, default_content_column_name)
        self.dimension_size = config.get(dimension_size)
        self.delete_index = config.get(delete_index, default_delete_index)

        self.uid = user
        try:
            self.pwd = os.environ["OPENSEARCH_PASSWORD"]
        except KeyError as e:
            self.logger.error(f"Environment variable OPENSEARCH_PASSWORD must be define. Raising Exception: {e}")
            raise UnrecoverableException("Missing credentials")
        try:
            self.client = OpenSearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_compress=True,  # enables gzip compression for request bodies
                http_auth=(self.uid, self.pwd),
                use_ssl=True,
                verify_certs=False,  # Set to True for production environments and provide appropriate CA certificates
                ssl_assert_hostname=False,
                ssl_show_warn=False
            )
        except Exception as e:
            self.logger.error(f"Failed to create OpenSearch client due to {e}")
            raise UnrecoverableException(f"Failed to create OpenSearch client due to {e}")

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Insert data into an OpenSearch k-NN vector index. Create the index if it does not exist.
        It assumes that embeddings are generated externally and stored as raw vectors in the table,
        following the process described in the
        https://docs.opensearch.org/latest/vector-search/creating-vector-index/#storing-raw-vectors-or-embeddings-generated-outside-of-opensearch.
.
        :param table: input table
        """
        self.logger.info(f"Transforming one table with {len(table)} rows")
        if self.delete_index:
            self.logger.info("Drop index initiated as the delete index option is specified")
            self.drop_index()

        if self.embeddings_column not in table.schema.names:
            self.logger.error(f"Column {self.embeddings_column} does not exist!")
            raise UnrecoverableException(f"Column {self.embeddings_column} does not exist!")

        if not self.dimension_size:
            self.dimension_size = len(table[self.embeddings_column][0].as_py())

        ts = datetime.now(timezone.utc)
        ts_col = pa.array([ts] * len(table), type=pa.timestamp('ns', tz='UTC'))
        table = table.append_column('transformtimestamp', ts_col)
        docs = table.to_pylist()

        success, failed = self.write_index(docs)

        metadata = {"rows_processed": table.num_rows,
                    "rows_inserted": success,
                    "rows_failed": len(failed),
                    }
        return [table], metadata

    def create_index(self) -> None:
        """
        Creates a vector index.
        Through an exception if error occurs.
        """
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
            self.client.indices.create(index=self.index_name, body=index_body)
            self.logger.info(f"index {self.index_name} created")
        except Exception as e:
            self.logger.error(f"Failed to create index {self.index_name} due to {e}")
            raise e

    def write_index(self, docs: list[dict]) -> tuple[int, int]:
        """
        Creates a vector index and write the data.
        Through an exception if error occurs.
        """
        index_exists = self.check_index()
        if index_exists:
            self.logger.info(f"index {self.index_name} exists")
        else:
            self.logger.debug(f"index {self.index_name} does not exist, creating it")
            self.create_index()

        documents = [
            {
                "_index": self.index_name,
                **({"_id": doc[self.doc_id_column]} if self.doc_id_column in doc else {}),
                "_source": {
                    **({self.doc_id_column: doc[self.doc_id_column]} if self.doc_id_column in doc else {}),
                    self.content_column: doc[self.content_column],
                    self.embeddings_column: doc[self.embeddings_column],
                    **({filename_column_name_key: doc[
                        filename_column_name_key]} if filename_column_name_key in doc else {}),
                }
            }
            for doc in docs
        ]
        try:
            success, failed = helpers.bulk(self.client, documents, refresh="wait_for")
        except Exception as e:
            self.logger.error(f"Failed to index documents into index {self.index_name} due to {e}")
            raise UnrecoverableException(f"Failed to index documents into index {self.index_name} due to {e}")

        self.logger.info(f"Successfully indexed {success} documents into index {self.index_name} ")
        if len(failed) > 0:
            self.logger.error(f"Failed to index {len(failed)} documents into index {self.index_name} ")

        return success, failed

    def check_index(self) -> bool:
        """
        Returns true if index exists. Otherwise, returns false.
        Through an exception if error occurs.
        """
        try:
            return self.client.indices.exists(index=self.index_name)
        except Exception as e:
            self.logger.error(f"An error occurred while checing the index: {e}")
            raise e

    def drop_index(self) -> None:
        """
        Drop the index if it exists
        Through an exception if error occurs.
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

    def delete_docs_by_field_value(self, field_name, value) -> None:
        """
        Delete all docs where the field field_name matches the given value param.

        :param field_name The name of the field in the document to match on.
        :param value The value to compare against field_name. Documents where field_name equals this value will be deleted.
        :return the number of docs deleted
        """
        if not field_name or not value:
            raise UnrecoverableException("Missing params to delete")
        self.logger.info(f"Delete all docs where the {field_name} field is {value}")
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
                f"Successfully deleted all {response['deleted']} docs from {field_name} file in {self.index_name} index")
            return response['deleted']
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
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

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the OpenSearchTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        """
        parser.add_argument(
            f"--{host_cli_param}",
            type=str,
            required=False,
            default=default_host,
            help="Specify the OpenSearch host:port. Defaults to localhost:9200"
        )
        parser.add_argument(
            f"--{indx_cli_param}",
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
            help="If true, delete the index before applying the transform",
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
