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
from typing import Any

import pyarrow as pa
from data_processing.data_access import DataAccessLocal
from data_processing.transform import AbstractTableTransform
from data_processing.utils import get_logger
from dpk_connector import crawl
from dpk_web2parquet.utils import *



user_agent = "Mozilla/5.0 (X11; Linux i686; rv:125.0) Gecko/20100101 Firefox/125.0"

logger = get_logger(__name__)

class Web2ParquetTransform(AbstractTableTransform):
    """
    Crawl the web and load content to pyarrow Table.
    """


    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        example: 
            kwargs = {'urls': ['https://thealliance.ai/'],'depth':  1,'downloads': 1}
            Web2ParquetTransform(**kwargs)
        or
            Web2ParquetTransform(urls=['https://thealliance.ai/'], depth=1, downloads=1)
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        # of NOOPTransformConfiguration class
        logger.debug(f"Received configuration: {config}")
        super().__init__(config)
        self.seed_urls = config.get("urls", [])
        self.depth = config.get("depth", 1)
        self.downloads = config.get("downloads", 10)
        self.allow_mime_types = config.get("mime_types", ["application/pdf","text/html","text/markdown","text/plain"])
        self.folder=config.get('folder', None)
        assert self.seed_urls, "Must specify a list of URLs to crawl. Url cannot be None"

        ## users may be tempted to provide a single URLs, we still need to put it in a list of 1
        if type(self.seed_urls) is not list:
            self.seed_urls=[self.seed_urls]

        self.count = 0
        self.docs = []

    def on_download(self, url: str, body: bytes, headers: dict) -> None:
        """
        Callback function called when a page has been downloaded.
        You have access to the request URL, response body and headers.
        """
        doc=get_file_info(url, headers)
        doc['url'] = url
        doc['contents'] = body
        
        logger.debug(f"url: {doc['url']}, filename: {doc['filename']}, content_type: {doc['content_type']}")

        ## Enforce download limits
        if len(self.docs) < self.downloads:
            self.docs.append(doc)


    def transform(self, table: pa.Table=None, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary
        This implementation makes no modifications so effectively implements a copy of the
        input parquet to the output folder, without modification.
        """
        start_time = time.time()
        crawl(
            self.seed_urls,
            self.on_download,
            user_agent=user_agent,
            depth_limit=self.depth,
            download_limit=self.downloads,
            allow_mime_types=self.allow_mime_types
        )  # blocking call


        end_time = time.time()      
        table = pa.Table.from_pylist(self.docs)
        metadata = {
            "count": len(self.docs),
            "requested_seeds": len(self.seed_urls),
            "requested_depth": self.depth,
            "requested_downloads": self. downloads,
            }
        logger.info(f"Crawling is completed in {end_time - start_time:.2f} seconds") 
        logger.info(f"{metadata = }")

        #############################################################################
        ## The same transform can also be used to store crawled files to local folder
        if self.folder:
            dao=DataAccessLocal(local_config={'output_folder':self.folder,'input_folder':'.'})
            for x in self.docs:
                dao.save_file(self.folder+'/'+x['filename'], x['contents'])
            
        return [table], metadata
    
    


class Web2Parquet(Web2ParquetTransform):
    """
    Crawl the web and load content to pyarrow Table.
    """

    def __init__(self, **kwargs):
        super().__init__(dict(kwargs))

