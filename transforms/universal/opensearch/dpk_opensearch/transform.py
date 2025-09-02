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

import time
from datetime import datetime, timezone
from argparse import ArgumentParser, Namespace
from typing import Any
import os
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk


import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider
from data_processing.utils import UnrecoverableException, get_logger

logger = get_logger(__name__)

short_name = "os"
cli_prefix = f"{short_name}_"
host_cli_param = f"{cli_prefix}host"
ndx_cli_param = f"{cli_prefix}index"
docid_cli_param = f"{cli_prefix}document_id_column_name"

doc_id_default = "document_id"
port_default = "9200"
host_default = f"localhost"



class OpenSearchTransform(AbstractTableTransform):
    """
    Implements a simple copy of a pyarrow Table.
    """

    def __init__(self, config: dict[str, Any]={}):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, NOOPTransformRuntime.  If running inside the RayMutatingDriver,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        # of NOOPTransformConfiguration class
        super().__init__(config)
        x=config.get(host_cli_param, host_default).split(':')
        self.host = x[0]
        self.port = x[1] if len(x) > 1 else port_default
        self.docId = config.get(docid_cli_param, doc_id_default)
        self.ndx= config.get(ndx_cli_param, 
                               f"dpk_{datetime.now().strftime('%y%m%d%H%M%S')}")

        self.uid=os.environ.get("OPENSEARH_USERID", "admin")
        try:
            self.pwd=os.environ["OPENSEARCH_PASSWORD"]
        except KeyError as e:
            logger.error(f"Environment variable OPENSEARCH_PASSWORD must be define. Raising Exception: {e}")
            raise UnrecoverableException("Missing credentials")


    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary
        This implementation makes no modifications so effectively implements a copy of the
        input parquet to the output folder, without modification.
        """
        filename_col=pa.array([file_name or 'missing'] * len(table), type=pa.string())
        table = table.append_column('transformfilepath', filename_col)
        ts = datetime.now(timezone.utc)
        ts_col = pa.array([ts] * len(table), type=pa.timestamp('ns', tz='UTC'))
        table = table.append_column('transformtimestamp', ts_col)
    
        docs = table.to_pylist()

        success, failed = self.write_index(docs)

        metadata = {"rows_processed": table.num_rows ,
                    "rows_inserted": success,
                    "rows_failed": len(failed),
                    "index": self.ndx,
                    "transform": short_name
        }
        return [], metadata

    def write_index(self, docs: list[dict]) -> tuple[int,int]:
        try:
            client = OpenSearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_compress=True, # enables gzip compression for request bodies
                http_auth = (self.uid, self.pwd),
                use_ssl=True,
                verify_certs=False,   # Set to True for production environments and provide appropriate CA certificates
                ssl_assert_hostname=False,
                ssl_show_warn=False
            )
        except Exception as e:
            logger.error(f"Failed to create OpenSearch client due to {e}")
            raise UnrecoverableException(f"Failed to create OpenSearch client due to {e}")
        
        if not client.indices.exists(index=self.ndx):
            # Create a new index
            client.indices.create(index=self.ndx)

        actions = [
        {
            '_op_type': 'index',
            '_index': self.ndx,
            '_id': doc.get(self.docId, None),
            '_source': doc
        }
        for doc in docs
        ]
        try:
            success,failed = bulk(client, actions)
        except Exception as e:
            logger.error(f"Failed to index documents into index {self.ndx} due to {e}")
            raise UnrecoverableException(f"Failed to index documents into index {self.ndx} due to {e}") 
        
        logger.debug(f"Successfully indexed {success} documents into index {self.ndx} ")
        if len(failed) > 0:
            logger.error(f"Failed to index {len(failed)} documents into index {self.ndx} ")

        return success, failed
    

    def read_index(self):
        """
        Drop the index if it exists
        Primarily used to clean up after testing 
        """
        client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_compress=True, # enables gzip compression for request bodies
            http_auth = (self.uid, self.pwd),
            use_ssl=True,
            verify_certs=False,   # Set to True for production environments and provide appropriate CA certificates
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        search_body = {
            'query': {
                'match_all': {}
            }
        }
        try:
            response = client.search(index=self.ndx,body=search_body)
            logger.debug(f"Total hits: {response['hits']['total']['value']}")
            return pa.Table.from_pylist(response['hits']['hits'])

        except Exception  as e:
                logger.error(f"Exception reding index  {self.ndx} : {e}")
                raise UnrecoverableException(f"Exception reding index  {self.ndx} : {e}")

    
    def drop_index(self):
        """
        Drop the index if it exists
        Primarily used to clean up after testing 
        """
        client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_compress=True, # enables gzip compression for request bodies
            http_auth = (self.uid, self.pwd),
            use_ssl=True,
            verify_certs=False,   # Set to True for production environments and provide appropriate CA certificates
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        if client.indices.exists(index=self.ndx):
            client.indices.delete(index=self.ndx)
            logger.info(f"Deleted index {self.ndx}")
        else:
            logger.info(f"Index {self.ndx} does not exist. Nothing to delete.")

    def check_index(self):
        """
        Drop the index if it exists
        Primarily used to clean up after testing 
        """
        client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_compress=True, # enables gzip compression for request bodies
            http_auth = (self.uid, self.pwd),
            use_ssl=True,
            verify_certs=False,   # Set to True for production environments and provide appropriate CA certificates
            ssl_assert_hostname=False,
            ssl_show_warn=False
        )
        return  client.indices.exists(index=self.ndx)

    

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
        This will be included in a dictionary used to initialize the NOOPTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{host_cli_param}",
            type=str,
            required=False,
            default=host_default,
            help="Specify the OpenSearch host:port"
            )
        parser.add_argument(
            f"--{ndx_cli_param}",
            type=str,
            required=False,
            help="Specify the name of the OpenSearch Index to write",
        )
        parser.add_argument(
            f"--{docid_cli_param}",
            type=str,
            required=False,
            default=doc_id_default,
            help="Name of the table column that identy a unique document ID",
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
