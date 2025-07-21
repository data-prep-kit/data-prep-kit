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
from argparse import ArgumentParser, Namespace
import json
import os
from typing import Any

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils

import requests
from requests.auth import HTTPBasicAuth 

short_name = "similarity"
cli_prefix = f"{short_name}_"

ES_ENDPOINT_KEY = "es_endpoint"
ES_ENDPOINT_CLI_PARAM = f"{cli_prefix}{ES_ENDPOINT_KEY}"
ES_ENDPOINT_DEFAULT = None

ES_USERID_KEY = "es_userid"
ES_USERID_CLI_PARAM = f"{cli_prefix}{ES_USERID_KEY}"
ES_USERID_DEFAULT = "elastic"

ES_PWD_KEY = "es_pwd"
ES_PWD_CLI_PARAM = f"{cli_prefix}{ES_PWD_KEY}"
ES_PWD_DEFAULT = "elastic"

ES_INDEX_KEY = "es_index"
ES_INDEX_CLI_PARAM = f"{cli_prefix}{ES_INDEX_KEY}"
ES_INDEX_DEFAULT = "mydata"

SHINGLE_SIZE_KEY = "shingle_size"
SHINGLE_SIZE_CLI_PARAM = f"{cli_prefix}{SHINGLE_SIZE_KEY}"
SHINGLE_SIZE_DEFAULT = 8

RESULT_SIZE_KEY = "result_size"
RESULT_SIZE_CLI_PARAM = f"{cli_prefix}{RESULT_SIZE_KEY}"
RESULT_SIZE_DEFAULT = 1

ANNOTATION_COLUMN_KEY = "annotation_column"
ANNOTATION_COLUMN_CLI_PARAM = f"{cli_prefix}{ANNOTATION_COLUMN_KEY}"
ANNOTATION_COLUMN_DEFAULT = "similarity_score"

DOC_TEXT_COLUMN_KEY = "doc_text_column"
DOC_TEXT_COLUMN_CLI_PARAM = f"{cli_prefix}{DOC_TEXT_COLUMN_KEY}"
DOC_TEXT_COLUMN_DEFAULT = "contents"


PARAMS = [
    {
        "key": ES_ENDPOINT_KEY,
        "cli_param": ES_ENDPOINT_CLI_PARAM,
        "default": ES_ENDPOINT_DEFAULT,
        "type": str,
        # "required": True,
        "required": False,
        "help": "The URL for Elasticsearch",
    },
    {
        "key": ES_USERID_KEY,
        "cli_param": ES_USERID_CLI_PARAM,
        "default": ES_USERID_DEFAULT,
        "type": str,
        "required": False,
        "help": "Elasticsearch user ID",
    },
    {
        "key": ES_PWD_KEY,
        "cli_param": ES_PWD_CLI_PARAM,
        "default": ES_PWD_DEFAULT,
        "type": str,
        "required": False,
        "help": "Elasticsearch password",
    },
    {
        "key": ES_INDEX_KEY,
        "cli_param": ES_INDEX_CLI_PARAM,
        "default": ES_INDEX_DEFAULT,
        "type": str,
        # "required": True,
        "required": False,
        "help": "The Elasticsearch index to query",
    },
    {
        "key": SHINGLE_SIZE_KEY,
        "cli_param": SHINGLE_SIZE_CLI_PARAM,
        "default": SHINGLE_SIZE_DEFAULT,
        "type": int,
        "required": False,
        "help": "Shingle size for query construction (default is 8)",
    },
        {
        "key": RESULT_SIZE_KEY,
        "cli_param": RESULT_SIZE_CLI_PARAM,
        "default": RESULT_SIZE_DEFAULT,
        "type": int,
        "required": False,
        "help": "result size for matched sentences (default is 1)",
    },
    {
        "key": ANNOTATION_COLUMN_KEY,
        "cli_param": ANNOTATION_COLUMN_CLI_PARAM,
        "default": ANNOTATION_COLUMN_DEFAULT,
        "type": str,
        "required": False,
        "help": "The column name that will contain the similarity score",
    },
    {
        "key": DOC_TEXT_COLUMN_KEY,
        "cli_param": DOC_TEXT_COLUMN_CLI_PARAM,
        "default": DOC_TEXT_COLUMN_DEFAULT,
        "type": str,
        "required": False,
        "help": "The column name that contains the document text",
    }
]



class SimilarityTransform(AbstractTableTransform):
    """
    Implements a simple copy of a pyarrow Table.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        This is generally called with configuration parsed from the CLI arguments defined
        by the companion runtime, SimilarityTransformRuntime.  If running inside the RayMutatingDriver,
        these will be provided by that class with help from the RayMutatingDriver.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        # of SimilarityTransformConfiguration class
        super().__init__(config)
        self.es_endpoint = config.get(ES_ENDPOINT_KEY, ES_ENDPOINT_DEFAULT)
        self.es_userid = config.get(ES_USERID_KEY, ES_USERID_DEFAULT)
        self.es_pwd = config.get(ES_PWD_KEY, ES_PWD_DEFAULT)
        self.es_index = config.get(ES_INDEX_KEY, ES_INDEX_DEFAULT)
        self.shingle_size = config.get(SHINGLE_SIZE_KEY, SHINGLE_SIZE_DEFAULT)
        self.result_size = config.get(RESULT_SIZE_KEY, RESULT_SIZE_DEFAULT)
        self.annotation_column = config.get(ANNOTATION_COLUMN_KEY, ANNOTATION_COLUMN_DEFAULT)
        self.doc_text_column = config.get(DOC_TEXT_COLUMN_KEY, DOC_TEXT_COLUMN_DEFAULT)


    def _testElasticFuncioning(self):   
        url=self.es_endpoint 
        headers = {'Content-Type': 'application/json'}
        res = requests.get(url=url, headers=headers, auth = HTTPBasicAuth(self.es_userid, self.es_pwd), verify=False)

        if res.status_code != 200:
            print(f"ERROR: {res.text}")
            return False
        return True


    def _excecuteQuery(self, query):
        if self._testElasticFuncioning():
            r = requests.post(url=f"{self.es_endpoint.rstrip('/')}/_search", json=query, auth = HTTPBasicAuth(self.es_userid, self.es_pwd), verify=False)
            q = r.json()
            res = []
            # try:
            for d in q["hits"]["hits"]:
                ddd = {"id":d["fields"]["_id"][0],"index":d["fields"]["_index"][0], "score" :d["_score"]}
                ddd["contents"] = d["highlight"]["contents"]
                res.append(ddd)
            # except Exception as ex:
            #     print(ex)
            return res
        return None


    def _getNgramQuery(self, text):
        slop = 2
        context = self.shingle_size
        document = text

        # generate all possible shingles
        s = []
        spaces = [i for i,j in enumerate(document) if j==' ']
        spaces.insert(0,0)
        end = len(spaces) - context
        if end > 0:
            for c in range(0, end):
                s.append( document[spaces[c]:spaces[c+context]].strip())
            s.append( document[spaces[end]:len (document)].strip())
        else:
            s.append(document.strip())

        # format them in elastic grammar
        shingles = []
        for ss in s:

            shingles.append (
                            {
                                "match_phrase": {
                                    "contents": {
                                        "query": ss,
                                        "slop": slop
                                    }
                                }
                            })

        # construct elastic query
        query = {    
        "size": self.result_size,
        # "_source": "false",
        "fields":["_id", "_index", "_score"],
        "query": {
            "bool": {
                "filter": {
                    "exists": {
                        "field": "contents"
                    }
                },
                "must": [
                    {
                        "bool": {
                            "should": shingles,
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        },
        "highlight": {
                    "pre_tags": [
                ""
            ],
            "post_tags": [
                ""
            ],
            "fields": {
                "contents": {
                                "order": "score",
            "fragment_size": 0,
            "number_of_fragments": 1}
            }
        }
    }
        return query
    

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Put Transform-specific to convert one Table to 0 or more tables. It also returns
        a dictionary of execution statistics - arbitrary dictionary
        """
        self.logger.debug(f"Transforming one table with {len(table)} rows")

        # make sure that the table contains doc_text_column column
        TransformUtils.validate_columns(table=table, required=[self.doc_text_column])
        self.df = table.to_pandas()
        result_list = []

        if self.es_endpoint is not None:
            for i in range(len(self.df)):
                q = self._getNgramQuery(self.df.iloc[i][self.doc_text_column])
                r = self._excecuteQuery(q)
                result_list.append(r)
        else:
            # local-only processing, so load response from file instead of hitting Elasticsearch
            json_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "result_list.json")
            with open(json_file_path, "r") as f:
                result_list = json.load(f)


        assert len(self.df) == len(result_list), "The number of rows in the dataframe does not match the number of elements in result_list."

        
        
        
        self.df[self.annotation_column] = result_list
        print(self.df)
        
        table = pa.Table.from_pandas(self.df)

        self.logger.debug(f"Transformed one table with {len(table)} rows")
        metadata = {"nrows": len(table)}
        return [table], metadata


class SimilarityTransformConfiguration(TransformConfiguration):

    """
    Provides support for configuring and using the associated Transform class include
    configuration with CLI args.
    """

    def __init__(self):
        super().__init__(
            name=short_name,
            transform_class=SimilarityTransform,
            remove_from_metadata=[ES_PWD_KEY],
        )
        from data_processing.utils import get_logger

        self.logger = get_logger(__name__)


    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given parser.
        This will be included in a dictionary used to initialize the SimilarityTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, similarity_, pii_, etc.)
        """
        for param in PARAMS:
            parser.add_argument(
                f"--{param['cli_param']}",
                type=param["type"],
                required=param["required"],
                default=param["default"],
                help=param["help"]
            )


    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)

        # Validate the shingle_size parameter
        shingle_size_value = captured.get(SHINGLE_SIZE_KEY, SHINGLE_SIZE_DEFAULT)
        try:
            shingle_size_int = int(shingle_size_value)
            if shingle_size_int <= 0:
                print(f"Parameter '--{SHINGLE_SIZE_CLI_PARAM}' should be greater than 0. You specified '{shingle_size_value}'.")
                return False
        except (ValueError, TypeError):
            print(f"Parameter '--{SHINGLE_SIZE_CLI_PARAM}' should be an integer greater than 0. You specified '{shingle_size_value}'.")
            return False

        # Set endpoint to None if the input is empty or "None" (as a string)
        if captured.get('es_endpoint') == "None" or (isinstance(captured.get('es_endpoint'), str) and len(captured.get('es_endpoint')) == 0):
            captured['es_endpoint'] = None

        self.params = self.params | captured
        params_to_print = {k:v for k,v in self.params.items() if k != 'es_pwd'}
        self.logger.info(f"{short_name} parameters are : {params_to_print}")
        return True
