
from dpk_fineweb_quality_annotator import FineWebQualityAnnotatorTransform
from typing import NoReturn
import pytest
import pyarrow as pa


def test_mytest():

    contents = pa.array(["Flamingo", "Horse", "Brittle stars", "", "Centipede"])
    urls = pa.array(['a.in', "abc.com", "test.org", "empty.com", "content.com"])


    table = pa.Table.from_arrays([contents, urls], names=["contents","url"])
    fwq_transform = FineWebQualityAnnotatorTransform(config={'contents_column_name': 'contents'})
    res_tables, metadata = fwq_transform.transform(table=table)
    assert res_tables[0]['frac_line_punct'][0].as_py() == 0.0
    assert res_tables[0]['frac_line_punct'][1].as_py() == 0.0
    assert res_tables[0]['frac_line_punct'][2].as_py() == 0.0
    assert res_tables[0]['frac_line_punct'][3].as_py() == -1.0
    assert res_tables[0]['frac_line_punct'][4].as_py() == 0
    assert metadata['total_docs'] == 5
