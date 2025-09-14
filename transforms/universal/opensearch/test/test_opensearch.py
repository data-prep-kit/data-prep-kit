from dpk_opensearch.transform import OpenSearchTransform
from opensearchpy.exceptions import ConnectionError
from data_processing.utils import UnrecoverableException
import pyarrow.parquet as pq
import os
import pytest

from data_processing.utils import get_logger

logger = get_logger(__name__)

from dpk_opensearch.transform import (
    hostname, default_embeddings_column_name
)

input_test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test-data", "input"))
test_file = os.path.join(input_test_dir, 'test1.parquet')

class TestOpenSearch:
    def setup_method(self, method):
        # do not run as part of a git action for now
        if os.environ.get('GITHUB_REPOSITORY', None):
            pytest.skip("Skipping all tests running from github action")

        logger.info("Testing connection to OpenSearch")
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
