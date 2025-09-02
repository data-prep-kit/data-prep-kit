from dpk_opensearch import OpenSearchTransform
from opensearchpy.exceptions import ConnectionError
import pyarrow.parquet as pq
import os

from data_processing.utils import get_logger
logger = get_logger(__name__)


from dpk_opensearch.transform import (
    host_cli_param,
    ndx_cli_param
    )

def test_upload():
    """
    Testing table read/write
    :return: None
    """

    # do not run as part of a git action for now
    if os.environ.get('GITHUB_REPOSITORY', None):
        return


    x=OpenSearchTransform()

    logger.info("Testing connection to OpenSearch")
    try:
        x.check_index()
    except ConnectionError:
        assert False, "Failed to establish connection"

    
    logger.info("Checking index does NOT existence")
    assert x.check_index() == False         

    logger.info("Create index and confirm all rows are inserted")                                                             
    tbl=pq.read_table('../test-data/input/sample1.parquet')
    _,metadata=x.transform(tbl,'test-data/input/sample1.parquet')
    assert(metadata["rows_processed"] == tbl.num_rows)
    assert(metadata["rows_inserted"] == tbl.num_rows)


    logger.info("Drop index and confirm non-existence")                                                             
    assert x.check_index() == True
    x.drop_index()
    assert x.check_index() == False


def test_upload_with_params():
    """
    Testing table read/write with parameters
    return: None
    """
    x=OpenSearchTransform(config={host_cli_param:'localhost:9200',  ndx_cli_param:'dpk_test' })
    try:
        x.check_index()
    except ConnectionError:
        assert False, "Failed to establish connection"

    tbl=pq.read_table('../test-data/input/sample1.parquet')
    _,metadata=x.transform(tbl,'test-data/input/sample1.parquet')
    assert(metadata["rows_processed"] == tbl.num_rows)
    assert(metadata["rows_inserted"] == tbl.num_rows)
    assert x.check_index() == True
