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

import argparse
import html
import re
import sys
from typing import Optional

from data_processing.utils import get_logger
from resiliparse.extract.html2text import extract_plain_text
from resiliparse.parse.html import HTMLTree

__all__ = [
    "extract_and_clean_html",
]

logger = get_logger(__name__)

RECOMMENDED_RESILIPARSE_CONFIG = dict(
    # main_content=True,
    alt_texts=True,  # need to keep Math repr
    comments=False,
    skip_elements=["mrow"],  # need to keep Math repr
)


def get_args_parser(description: Optional[str] = None):
    parser = argparse.ArgumentParser(
        description=description,
    )

    parser.add_argument(
        "--in_html",
        type=str,
        help="input HTML file.",
    )
    parser.add_argument(
        "--out_txt",
        type=str,
        help="output text file.",
    )
    parser.add_argument(
        "--disable_table_structure",
        action="store_true",
        help="disable to add table structure.",
    )
    return parser


def modify_cell(cell, i, max_cols):
    txt = html.escape(
        extract_plain_text(cell.html, main_content=False, **RECOMMENDED_RESILIPARSE_CONFIG)
    )
    txt = txt.replace("|", r"\|")  # escape '|' inside table cells not to indicate table columns
    if "</pre>" in cell.html or "\n" in txt:
        # When text being extracted, newline characters are inserted before and after <pre>.
        # Thus, to remove such newlines, mark them with :::NL:::
        # However, we don't want to remove newlines at the end of row.
        # So, we use xxxNLxxx instead.
        txt = ":::NL:::<pre>" + txt + "</pre>" + (":::NL:::" if i != (max_cols-1) else "xxxNLxxx")
    cell.html = ("| " if i == 0 else "") + txt  # add '|' at the beginning of every table row
    return cell


def extract_and_clean_by_default(html_text: str) -> str:
    """Extract and clean text from HTML string by default Resiliparse functionalities.

    Parameters
    ----------
    html_text : str
        raw HTML string

    Returns
    -------
    str
        cleaned text
    """
    text = extract_plain_text(
        html_text,
        main_content=True,
        **RECOMMENDED_RESILIPARSE_CONFIG
    )
    return text


def extract_and_clean_by_extended(html_text: str) -> str:
    """Extract and clean text from HTML string by extending Resiliparse
    to bettern handle table and list structures.

    Parameters
    ----------
    html_text : str
        raw HTML string

    Returns
    -------
    str
        cleaned text
    """
    tree = HTMLTree.parse(html_text)

    # remove all but <pre> child tags in table rows
    for table in tree.body.get_elements_by_tag_name("table"):
        # Ref: https://github.com/adbar/trafilatura/blob/535e70a470104b5ba129fc590b215420465cbb17/trafilatura/main_extractor.py#L358-L361
        # calculate maximum number of columns per row, including colspan
        max_cols = 0
        for tr in table.get_elements_by_tag_name('tr'):
            th_cols = sum(
                int(td.getattr("colspan", "1")) for td in tr.get_elements_by_tag_name("th")
            )
            td_cols = sum(
                int(td.getattr("colspan", "1")) for td in tr.get_elements_by_tag_name("td")
            )
            max_cols = max(max_cols, th_cols, td_cols)

        for i, th in enumerate(table.get_elements_by_tag_name("th")):  # table header
            th = modify_cell(th, i, max_cols)
        for j, tr in enumerate(table.get_elements_by_tag_name("tr")):  # row
            for i, td in enumerate(tr.get_elements_by_tag_name("td")):  # cell
                td = modify_cell(td, i, max_cols)

    # add vertical lines at the end of each table cell to indicate table columns
    modified_html = (
        tree.body.html
        .replace("</th>", " |</th>")
        .replace("</td>", " |</td>")
    )

    # main extraction by resiliparse
    text = extract_plain_text(
        modified_html,
        main_content=True,
        **RECOMMENDED_RESILIPARSE_CONFIG
    )

    # remove unnecessary newlines around <pre>
    text = text.replace(":::NL:::\n", "").replace("\n:::NL::: |\n", " | ").replace("\nxxxNLxxx", "")
    # remove unnecessary newlines before list items
    text = re.sub(r"\n\n( +• )", r"\n\1", text, flags=re.S)
    text = re.sub(r"\n\n( +\d+\. )", r"\n\1", text, flags=re.S)

    return text


def extract_and_clean_html(html_text: str, disable_table_structure: bool = False) -> str:
    """Extract and clean text from HTML string.

    Parameters
    ----------
    html_text : str
        raw HTML string
    disable_table_structure : bool, optional
        if True, do not preserve table structure, by default False

    Returns
    -------
    str
        cleaned text
    """
    try:
        if disable_table_structure:
            text = extract_and_clean_by_default(html_text)
        else:
            text = extract_and_clean_by_extended(html_text)
    except Exception as e:
        logger.warning(e)
        text = ""
    return text


def extract_and_clean_html_from_file(in_file: str, disable_table_structure: bool = False) -> str:
    """Extract and clean text from HTML file.

    Parameters
    ----------
    in_file : str
        HTML file
    disable_table_structure : bool, optional
        if True, do not preserve table structure, by default False

    Returns
    -------
    str
        cleaned text
    """
    with open(in_file) as fi:
        html_text = fi.read()

    text = extract_and_clean_html(html_text, disable_table_structure)

    return text


def parse_html(args):
    text = extract_and_clean_html_from_file(args.in_html)
    with open(args.out_txt, "w") as fo:
        print(text, file=fo)
    return


def main(args):
    parse_html(args)
    return


if __name__ == "__main__":
    description = "Extract clean text from HTML with modified Resiliparse"
    args_parser = get_args_parser(description=description)
    args = args_parser.parse_args()
    sys.exit(main(args))
