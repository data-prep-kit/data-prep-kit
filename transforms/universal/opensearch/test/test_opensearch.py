from dpk_opensearch.transform import OpenSearchTransform
from opensearchpy.exceptions import ConnectionError
from data_processing.utils import UnrecoverableException
import pyarrow.parquet as pq
import os
import pytest
import pyarrow as pa

from data_processing.utils import get_logger

logger = get_logger(__name__)

from dpk_opensearch.transform import (
    hostname, default_embeddings_column_name, indx
)

input_test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
test_file = os.path.join(input_test_dir, 'test1.parquet')

class TestOpenSearch:
    def setup_method(self, method):
        # do not run as part of a git action for now
        if os.environ.get('GITHUB_REPOSITORY', None):
            pytest.skip("Skipping all tests running from github action")

        logger.info("Testing connection to OpenSearch")
        if method.__name__ == "test_index_name":
            from datetime import datetime
            index_name = f"dpk_test_{datetime.now().strftime('%y%m%d%H%M%S')}"
            self.x = OpenSearchTransform(config={indx: index_name})
        else:
            self.x = OpenSearchTransform(config={hostname: 'localhost:9200'})
        try:
            self.x.check_index()
        except ConnectionError:
            assert False, "Failed to establish connection"

    def teardown_method(self):
        logger.info("Cleanup")
        self.x.drop_index()
        assert self.x.check_index() is False

    def test_upload(self, caplog):
        """
        Testing table read/write
        :return: None
        """
        logger.info("Checking index does NOT existence")
        assert self.x.check_index() is False

        logger.info("Create index and confirm all rows are inserted")
        tbl = pq.read_table(test_file)
        _, metadata = self.x.transform(tbl, test_file)
        assert (metadata["rows_processed"] == tbl.num_rows)
        assert (metadata["rows_inserted"] == tbl.num_rows)
        assert "Drop index initiated as the delete index option is specified" not in caplog.text
        assert f"Successfully indexed {tbl.num_rows} documents" in caplog.text

    def test_transform_with_index_delete(self, caplog):
        tbl = pq.read_table(test_file)
        self.x.dimension_size = len(tbl[self.x.embeddings_column][0].as_py())
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

    def test_no_embeddings_column(self, caplog):
        tbl = pq.read_table(test_file)
        tbl = tbl.drop(default_embeddings_column_name)
        with pytest.raises(UnrecoverableException):
            _, _ = self.x.transform(tbl, test_file)

    def test_index_name(self, caplog):
        tbl = pq.read_table(test_file)
        _, _ = self.x.transform(tbl, test_file)
        text = caplog.text
        assert f"{self.x.index_name} created" in text
        assert f"Successfully indexed {tbl.num_rows} documents" in text

    def test_delete_docs(self, caplog):
        tbl = pq.read_table(test_file)
        text = str(tbl["contents"][0])
        _, metadata = self.x.transform(tbl, test_file)
        assert metadata['rows_inserted'] == tbl.num_rows
        assert (1 == self.x.delete_docs_by_field_value(field_name="contents", value=text))
        assert f"Successfully deleted all 1 rows" in caplog.text

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_docs(self, deletion_func, caplog):
        tbl = pq.read_table(test_file)
        dummy_filename = "dummy"
        new_col = pa.array([dummy_filename] * tbl.num_rows)
        new_tbl = tbl.append_column("filename", new_col)
        _, metadata = self.x.transform(new_tbl, test_file)
        assert metadata['rows_inserted'] == new_tbl.num_rows
        if deletion_func == "delete_documents":
            del_metadata = self.x.delete_documents([dummy_filename])
            assert del_metadata['deleted_count'] == 1
            assert len(del_metadata['failed']) == 0
            assert len(del_metadata['not_found']) == 0
            assert del_metadata['success'] == True
        else:
            assert (tbl.num_rows == self.x.delete_docs_by_field_value(field_name="filename", value=dummy_filename))

        assert f"Successfully deleted all {tbl.num_rows} rows" in caplog.text

    @pytest.mark.parametrize("deletion_func", ["delete_docs_by_field_value", "delete_documents"])
    def test_delete_nonexist_docs(self, deletion_func, caplog):
        dummy_filename = "dummy"
        tbl = pq.read_table(test_file)
        new_col = pa.array([dummy_filename] * tbl.num_rows)
        new_tbl = tbl.append_column("filename", new_col)
        _, metadata = self.x.transform(new_tbl, test_file)
        assert metadata['rows_inserted'] == new_tbl.num_rows
        if deletion_func == "delete_documents":
            del_metadata = self.x.delete_documents(["notexist_files"])
            assert del_metadata['deleted_count'] == 0
            assert len(del_metadata['failed']) == 0
            assert len(del_metadata['not_found']) == 1
            assert del_metadata['success'] == True
        else:
            assert (0 == self.x.delete_docs_by_field_value(field_name="filename", value="notexist_files"))
        assert f"Successfully deleted all 0 rows" in caplog.text

    def test_delete_nonexist_column(self, caplog):
        tbl = pq.read_table(test_file)
        _, metadata = self.x.transform(tbl, test_file)
        assert metadata['rows_inserted'] == tbl.num_rows
        assert (0 == self.x.delete_docs_by_field_value(field_name="dummy", value="dummy"))
        assert f"Successfully deleted all 0 rows" in caplog.text

