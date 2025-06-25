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

import json, argparse, pyarrow, yaml, os
import pyarrow.compute as pc
from typing import Any
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, TransformUtils, UnrecoverableException

short_name = "ml_filter"
description = "filter using a per-language table of conditions"

# parameter table: name, type, default_value, description
param_table = [
        ("column_prefix", str, "", "Prefix for to all columns referenced in the conditions table"),
        ("lang_column_name", str, "lang", "Name of the column with the language identifier"),
        ("config", str, os.path.expanduser("~/cleansing-config.yaml"), "File name for the condition table (yaml)"),
        ("ignore_missing_columns", bool, False, "Ignore conditions that reference fields not present in the data"),
    ]

def get_transform_params():
    return param_table

def get_transform_param_defaults():
    return {k: d for k, t, d, h  in get_transform_params()}

def get_config(config: dict[str, Any], param: str):
    return config.get(param, get_transform_param_defaults().get(param, None))

class MLFilterTransform(AbstractTableTransform):
    """
    Implements Language Dependent Filtering
    """
    def __init__(self, config: dict[str, Any]):
        """
        Initialize based on the dictionary of configuration information.
        """
        # Make sure that the param name corresponds to the name used in apply_input_params method
        super().__init__(config)
        self.column_prefix = get_config(config, "column_prefix")
        self.lang_column = get_config(config, "lang_column_name")
        with open(get_config(config, "config"), 'r', encoding='utf-8') as y:
            conds = yaml.safe_load(y);
        if len(conds) == 0:
            raise UnrecoverableException("There are no conditions in the config yaml")
        self.conds = {}
        #{"default": { f"{self.column_prefix}{k}": v for k, v in conds.get("default", {}).items() }}
        self.default_conds = { f"{self.column_prefix}{k}": v for k, v in conds.get("default", {}).items() }
        for k, v in conds.items():
            if k == "default":
                continue
            self.conds[k] = {j: u for j, u in self.default_conds.items()}
            if v:
                self.conds[k].update({ f"{self.column_prefix}{j}": u for j, u in v.items() })
        column_names = list(set([ k for x, w in self.conds.items() for k in w.keys() ]))
        self.required_column_names = list(set([ c[:-4] if c.endswith("_min") or c.endswith("_max") or c.endswith("_not") else c for c in column_names ]))
        self.required_column_names.sort()
        self.ignore_missing_columns = get_config(config, "ignore_missing_columns")

    def apply_filter(self, table: pyarrow.Table, conditions: dict[str, dict[str, Any]]) -> tuple[pyarrow.table, Any]:
        result = table

        cc = None
        for lala, lacos in conditions.items():
            if lala == "other":
                laco = None
                for lang in [la for la in conditions.keys() if la != "other"]:
                    lc = pc.not_equal(table[self.lang_column], lang)
                    laco = pc.and_(laco, lc) if laco else lc
            else:
                laco = pc.equal(table[self.lang_column], lala)
            for fico, va in lacos.items():
                if fico.endswith("_max"):
                    co = pc.less_equal(table[fico[:-4]], va)
                elif fico.endswith("_min"):
                    co = pc.greater_equal(table[fico[:-4]], va)
                elif fico.endswith("_not"):
                    co = pc.greater_equal(table[fico[:-4]], va)
                else:
                    co = pc.greater_equal(table[fico], va)
                laco = pc.and_(laco, co) if laco else co
            if laco:
                cc = pc.or_(laco, cc) if cc else laco
        if cc:
            result = result.filter(cc)
       
        return result, {}

    def transform(self, table: pyarrow.Table, file_name: str = None) -> tuple[list[pyarrow.Table], dict[str, Any]]:
        """
        """
        missing = sorted(list(set(self.required_column_names) - set(table.schema.names)))
        if missing:
            if len(set(self.required_column_names)) == len(missing):
                self.logger.error(f"All columns are missing: {', '.join(missing)}")
                raise UnrecoverableException(f"None of the columns referenced in the filter are present: {', '.join(missing)}")
            if not self.ignore_missing_columns:    
                self.logger.error(f"Missing columns: {', '.join(missing)}")
                raise UnrecoverableException(f"Not all required columns are present, missing {', '.join(missing)}")
        
        self.logger.debug(f"Filtering one table with {len(table)} rows")
        ## filtering...
        table, stats = self.apply_filter(table, self.conds)
        return [table], stats

