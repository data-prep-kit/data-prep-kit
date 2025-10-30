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
import subprocess
from contextlib import contextmanager
import time

from dpk_opensearch.transform import OpenSearchTransform
from opensearchpy.exceptions import ConnectionError
import pyarrow
import pyarrow.parquet as pq
import os
import pytest
import requests
from requests.auth import HTTPBasicAuth

from data_processing.utils import get_dpk_logger

logger = get_dpk_logger()

from dpk_opensearch.transform import (
    endpoint_cli_param, default_embeddings_column_name, index_cli_param, filename_column_name_key,
    vector_method_cli_param, disable_security_cli_param
)

input_test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
test_file = os.path.join(input_test_dir, 'test1.parquet')

# The configuration order is critical — the default configuration is expected to run first,
# because the jVector setup depends on the plugin being deployed on the server,
# which is handled in the _configure_opensearch method below.
OPENSEARCH_CONFIGS = [
    {"name": "default", "vector_method": '{}'},
    {"name": "jvector", "vector_method": '{"name": "disk_ann", "engine": "jvector", "space_type": "l2", "parameters": {"m": 32, "ef_construction": 200}}'},
]


@contextmanager
def _configure_opensearch(cfg):
    """
    Configures Opensearch server based on the vector name.
    """
    def run_subprocess(cmd_args):
        proc = None
        try:
            proc = subprocess.run(cmd_args,
                check=True, input="y\n", capture_output=True, text=True, stderr=subprocess.STDOUT
            )
            return proc
        except Exception as e:
            logger.error(f"Running subprocess failed with error: {e}")
            logger.error(proc.stdout)


    def is_green_status():
        """
        Checks the status of the opensearch container.
        Returns if status is green and False otherwise.
        """


        try:
            pwd = os.getenv("OPENSEARCH_PASSWORD")
        except KeyError as e:
            logger.error(
                f"Environment variable OPENSEARCH_PASSWORD must be define. Raising Exception: {e}")

        url = "https://localhost:9200/_cluster/health"
        params = {
            "wait_for_status": "green",
            "timeout": "60s"
        }
        auth = HTTPBasicAuth("admin", pwd)
        try:
            response = requests.get(url, params=params, auth=auth,
                                    verify=False)
            if response.status_code == 200:
                data = response.json()
                if "status" not in data:
                    return False
                return (data["status"] == "green")
            return False
        except Exception:
            return False

    def wait_for_healthy(timeout: float = 120.0, interval: float = 10.0) -> bool:
        """
        Polls until docker reports the container state is green.
        Returns True on success, False on timeout.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            is_green = is_green_status()
            if is_green:
                return True
            time.sleep(interval)
        return False

    def get_opensearch_containers() -> list:
        try:
            pwd = os.getenv("OPENSEARCH_PASSWORD")
        except KeyError as e:
            logger.error(
                f"Environment variable OPENSEARCH_PASSWORD must be define. Raising Exception: {e}")

        auth = HTTPBasicAuth("admin", pwd)
        params = {"h": "name"}  # Only return node names
        url = "https://localhost:9200/_cat/nodes"

        response = requests.get(url, params=params, auth=auth, verify=False)
        response.raise_for_status()
        # Split lines into a list of node names
        return [name.strip() for name in response.text.splitlines() if name.strip()]



    if cfg["name"] == "jvector":
        containers = get_opensearch_containers()
        for container in containers:
            logger.info(f"starting jVector plugin configuration in {containers} container")
            cmd = ("cd /usr/share/opensearch &&"
                   "./bin/opensearch-plugin remove opensearch-neural-search && "
                   "./bin/opensearch-plugin remove opensearch-knn && "
                   "./bin/opensearch-plugin install --batch org.opensearch.plugin:opensearch-jvector-plugin:3.2.0.0")
            proc = run_subprocess(["docker", "exec", container, "bash", "-c", cmd])
            if proc.returncode != 0:
                logger.error("Error in jVector plugin configuration")
                raise RuntimeError

            proc = run_subprocess(["docker", "restart", container])
            if proc.returncode != 0:
                logger.error("Error in restarting opensearch")
                raise RuntimeError

        wait_for_healthy(timeout=180, interval=5)

    yield


@pytest.fixture(scope="class", params=OPENSEARCH_CONFIGS, ids=lambda c: c["name"])
def setup_env(request):
    cfg = request.param
    os.environ["VECTOR_METHOD"] = cfg["vector_method"]

    with _configure_opensearch(cfg):
        yield cfg  # make cfg available to tests

    os.environ.pop("VECTOR_METHOD", None)



@pytest.mark.usefixtures("setup_env")
class TestOpenSearch:
    def setup_method(self, method):
        # do not run as part of a git action for now
#        if os.environ.get('GITHUB_REPOSITORY', None):
#            pytest.skip("Skipping all tests running from github action")

        logger.info("Testing connection to OpenSearch")
        config = {endpoint_cli_param: 'localhost:9200'}
        vector_method = os.getenv("VECTOR_METHOD")
        if vector_method != '{}':
            config[vector_method_cli_param] = vector_method
        if method.__name__ == "test_index_name":
            from datetime import datetime
            index_name = f"dpk_test_{datetime.now().strftime('%y%m%d%H%M%S')}"
            config[index_cli_param] = index_name
        self.x = OpenSearchTransform(config=config)
        try:
            self.x.check_index()
        except ConnectionError:
            assert False, "Failed to establish connection"

    def teardown_method(self):
        logger.info("Cleanup")
        self.x.drop_index()
        assert self.x.check_index() is False

    @pytest.fixture(autouse=True)
    def setup_logger(self, caplog):
        logger.addHandler(caplog.handler)
        yield
        logger.removeHandler(caplog.handler)

    @pytest.mark.parametrize("apply_knn", [True, False])
    def test_upload(self, apply_knn, caplog):
        """
        Testing table read/write
        :return: None
        """
        logger.info("Checking index does NOT existence")
        assert self.x.check_index() is False

        logger.info("Create index and confirm all rows are inserted")
        tbl = pq.read_table(test_file)
        if not apply_knn:
            logger.info("apply_knn is True")
            tbl = tbl.drop(["embeddings"])
        _, metadata = self.x.transform(tbl, test_file)
        assert (metadata["rows_processed"] == tbl.num_rows)
        assert (metadata["rows_inserted"] == tbl.num_rows)
        assert "Drop index initiated as the delete index option is specified" not in caplog.text
        assert f"Successfully indexed {tbl.num_rows} documents" in caplog.text

    @pytest.mark.parametrize("apply_knn", [True, False])
    def test_transform_with_index_delete(self, apply_knn, caplog):
        tbl = pq.read_table(test_file)
        if apply_knn:
            self.x.dimension_size = len(tbl[self.x.embeddings_column][0].as_py())
        else:
            tbl = tbl.drop(["embeddings"])
        # First create the index
        self.x.create_index()
        assert self.x.check_index() is True
        self.x.delete_index = True
        _, metadata = self.x.transform(tbl, test_file)
        assert metadata['rows_inserted'] == tbl.num_rows
        text = caplog.text
        assert 'Drop index initiated as the delete index option is specified' in text
        assert "Deleted index" in text
        assert f"Successfully indexed {tbl.num_rows} documents" in text
        assert text.index("Deleted index") < text.index(f"Successfully indexed {tbl.num_rows} documents")

    @pytest.mark.parametrize("apply_knn", [True, False])
    def test_index_name(self, apply_knn, caplog):
        tbl = pq.read_table(test_file)
        if not apply_knn:
            tbl = tbl.drop(["embeddings"])
        _, _ = self.x.transform(tbl, test_file)
        text = caplog.text
        assert f"{self.x.index_name} created" in text
        assert f"Successfully indexed {tbl.num_rows} documents" in text

    def add_filename_column(self, tbl: pyarrow.Table, filename: str) -> pyarrow.Table:
        if filename_column_name_key not in tbl.schema.names:
            # Add filename column to the schema
            new_column = pyarrow.array([filename] * tbl.num_rows)
            return tbl.append_column(filename_column_name_key, new_column)
        return tbl

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_docs(self, deletion_func, caplog):
        tbl = pq.read_table(test_file)
        filename = os.path.basename(test_file)
        tbl = self.add_filename_column(tbl, filename)
        tbls, metadata = self.x.transform(tbl, test_file)
        assert len(tbls) == 0
        assert metadata['rows_inserted'] == tbl.num_rows

        if deletion_func == "delete_documents":
            del_metadata = self.x.delete_documents([filename])
            assert del_metadata['deleted_count'] == 1
            assert len(del_metadata['failed']) == 0
            assert len(del_metadata['not_found']) == 0
            assert del_metadata['success'] == True
        else:
            assert (tbl.num_rows == self.x.delete_docs_by_field_value(field_name=filename_column_name_key,
                                                                      value=filename))

        assert f"Successfully deleted all {tbl.num_rows} rows" in caplog.text

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_nonexistent_docs(self, deletion_func, caplog):
        tbl = pq.read_table(test_file)
        filename = os.path.basename(test_file)
        tbl = self.add_filename_column(tbl, filename)
        _, metadata = self.x.transform(tbl, test_file)
        assert metadata['rows_inserted'] == tbl.num_rows
        if deletion_func == "delete_documents":
            del_metadata = self.x.delete_documents(["nonexistent_file"])
            assert del_metadata['deleted_count'] == 0
            assert len(del_metadata['failed']) == 0
            assert len(del_metadata['not_found']) == 1
            assert del_metadata['success'] == True
        else:
            assert (0 == self.x.delete_docs_by_field_value(field_name=filename_column_name_key,
                                                           value="nonexistent_file"))
        assert f"Successfully deleted all 0 rows" in caplog.text

    def test_delete_nonexistent_column(self, caplog):
        tbl = pq.read_table(test_file)
        filename = os.path.basename(test_file)
        tbl = self.add_filename_column(tbl, filename)
        _, metadata = self.x.transform(tbl, test_file)
        assert metadata['rows_inserted'] == tbl.num_rows
        assert (0 == self.x.delete_docs_by_field_value(field_name="nonexistent_column", value="nonexistent_file"))
        assert f"Successfully deleted all 0 rows" in caplog.text

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_nonexistentent_index(self, deletion_func, caplog):
        tbl = pq.read_table(test_file)
        filename = os.path.basename(test_file)
        tbl = self.add_filename_column(tbl, filename)
        tbls, metadata = self.x.transform(tbl, test_file)
        assert len (tbls) == 0
        assert metadata['rows_inserted'] == tbl.num_rows
        self.x.index_name = "nonexistentent"
        filename = tbl[filename_column_name_key][0].as_py()
        if deletion_func == "delete_docs_by_field_value":
            with pytest.raises(Exception):
                _ = self.x.delete_docs_by_field_value(field_name=filename_column_name_key,
                                                      value=filename)
        else:
            del_metadata = self.x.delete_documents([filename])
            assert del_metadata['deleted_count'] == 0
            assert len(del_metadata['failed']) == 1
            assert len(del_metadata['not_found']) == 0
            assert del_metadata['success'] == False

        if deletion_func == "delete_docs_by_field_value":
            assert f"index_not_found_exception" in caplog.text

    @pytest.mark.parametrize("apply_knn", [True, False])
    def test_create_index_already_exists(self, apply_knn, caplog):
        tbl = pq.read_table(test_file)
        if not apply_knn:
            tbl = tbl.drop(["embeddings"])
        _, _ = self.x.transform(tbl, test_file)
        config = None
        if apply_knn:
            config = self.x.get_knn_configuration()
        with pytest.raises(Exception):
            self.x.create_index(config)
        assert "resource_already_exists_exception" in caplog.text