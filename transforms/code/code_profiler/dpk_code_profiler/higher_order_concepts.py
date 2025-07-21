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

from dpk_code_profiler.UAST import *


def extract_ccr(uast):
    """
    Calculates the code to comment ratio given an UAST object as input
    """
    if uast is not None:
        total_comment_loc = 0
        for node_idx in uast.nodes:
            node = uast.get_node(node_idx)
            if node.node_type == "uast_comment":
                total_comment_loc += node.metadata.get("loc_original_code", 0)
            elif node.node_type == "uast_root":
                loc_snippet = node.metadata.get("loc_snippet", 0)
        if loc_snippet > 0:
            if total_comment_loc > 0:
                return str(round(float(loc_snippet) / float(total_comment_loc), 1))
            else:
                return str(0)
        else:
            return str(-1)
    return str(0)


def extract_code_snippet_length(uast):
    if uast is not None:
        for node_idx in uast.nodes:
            node = uast.get_node(node_idx)
            if node.node_type == "uast_root":
                loc_snippet = node.metadata.get("loc_snippet", 0)
                if loc_snippet > 0:
                    return str(loc_snippet)
                else:
                    return str(0)


def extract_code_avg_fn_len_in_snippet(uast):
    if uast is not None:
        total_fn_loc = 0
        fn_node_count = 0
        for node_idx in uast.nodes:
            node = uast.get_node(node_idx)
            if node.node_type == "uast_function":
                total_fn_loc += node.metadata.get("loc_original_code", 0)
                fn_node_count += 1

        if fn_node_count > 0:
            return str(round(float(total_fn_loc) / float(fn_node_count), 1))
        else:
            return str(0)
