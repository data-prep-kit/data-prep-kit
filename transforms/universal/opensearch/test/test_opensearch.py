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
from dpk_opensearch.transform import OpenSearchTransform
from opensearchpy.exceptions import ConnectionError
import pyarrow.parquet as pq
import os
import pytest

from data_processing.utils import get_logger

logger = get_logger(__name__)

from dpk_opensearch.transform import (
    endpoint_cli_param, default_embeddings_column_name, index_cli_param, filename_column_name_key
)

input_test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
test_file = os.path.join(input_test_dir, 'test1.parquet')

class TestOpenSearch:
    def setup_method(self, method):
        # do not run as part of a git action for now
#        if os.environ.get('GITHUB_REPOSITORY', None):
#            pytest.skip("Skipping all tests running from github action")

        logger.info("Testing connection to OpenSearch")
        if method.__name__ == "test_index_name":
            from datetime import datetime
            index_name = f"dpk_test_{datetime.now().strftime('%y%m%d%H%M%S')}"
            self.x = OpenSearchTransform(config={index_cli_param: index_name})
        else:
            self.x = OpenSearchTransform(config={endpoint_cli_param: 'localhost:9200'})
        try:
            self.x.check_index()
        except ConnectionError:
            assert False, "Failed to establish connection"

    def teardown_method(self):
        logger.info("Cleanup")
        self.x.drop_index()
        assert self.x.check_index() is False

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

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_docs(self, deletion_func, caplog):
        tbl = pq.read_table(test_file)
        tbls, metadata = self.x.transform(tbl, test_file)
        assert len(tbls) == 0 

        filename = tbl[filename_column_name_key][0].as_py()
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
        _, metadata = self.x.transform(tbl, test_file)
        assert metadata['rows_inserted'] == tbl.num_rows
        assert (0 == self.x.delete_docs_by_field_value(field_name="nonexistent_column", value="nonexistent_file"))
        assert f"Successfully deleted all 0 rows" in caplog.text

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_nonexistentent_index(self, deletion_func, caplog):
        tbl = pq.read_table(test_file)
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

