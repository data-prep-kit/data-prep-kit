# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
#
# YARA compile and scan logic adapted from OmniScan
# (https://github.ibm.com/AI-Code-Security/omniscan) by Dhilung Kirat,
# IBM Research. Used under Apache-2.0 with attribution.

import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Optional

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration
from data_processing.utils import CLIArgumentProvider, get_dpk_logger
from data_processing.utils.transform_utils import TransformUtils


logger = get_dpk_logger()

shortname = "yara"
cli_prefix = f"{shortname}_"

INPUT_COLUMN_KEY = "yara_input_column"
RULES_DIR_KEY = "yara_rules_dir"
CATEGORY_KEY = "yara_category"
MATCHED_COLUMN_KEY = "yara_matched_column"
RULES_COLUMN_KEY = "yara_rules_column"
TAGS_COLUMN_KEY = "yara_tags_column"
CATEGORIES_COLUMN_KEY = "yara_categories_column"
FAIL_ON_COMPILE_KEY = "yara_fail_on_compile_error"

DEFAULT_INPUT_COLUMN = "binary_contents"
DEFAULT_MATCHED_COLUMN = "yara_matched"
DEFAULT_RULES_COLUMN = "yara_rules"
DEFAULT_TAGS_COLUMN = "yara_tags"
DEFAULT_CATEGORIES_COLUMN = "yara_categories"
DEFAULT_FAIL_ON_COMPILE = False


def _is_hidden(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def resolve_rules_dir(explicit: Optional[str]) -> Path:
    """Resolve rules directory in order: CLI arg, env var, baked image path, source-tree default."""
    if explicit:
        return Path(explicit)
    env = os.environ.get("DPK_YARA_RULES_DIR")
    if env:
        return Path(env)
    baked = Path("/app/rules")
    if baked.exists():
        return baked
    return Path(__file__).resolve().parent.parent / "rules"


class YaraTransform(AbstractTableTransform):
    """Scan a bytes/string column with YARA rules and annotate matches."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        import yara  # noqa: F401  (surface ImportError early)

        self.input_column = config.get(INPUT_COLUMN_KEY, DEFAULT_INPUT_COLUMN)
        self.rules_dir = resolve_rules_dir(config.get(RULES_DIR_KEY))
        self.category = config.get(CATEGORY_KEY)
        self.matched_column = config.get(MATCHED_COLUMN_KEY, DEFAULT_MATCHED_COLUMN)
        self.rules_column = config.get(RULES_COLUMN_KEY, DEFAULT_RULES_COLUMN)
        self.tags_column = config.get(TAGS_COLUMN_KEY, DEFAULT_TAGS_COLUMN)
        self.categories_column = config.get(CATEGORIES_COLUMN_KEY, DEFAULT_CATEGORIES_COLUMN)
        self.fail_on_compile = bool(config.get(FAIL_ON_COMPILE_KEY, DEFAULT_FAIL_ON_COMPILE))

        self._compiled = self._compile_rules()
        if not self._compiled:
            msg = f"No YARA rules compiled from {self.rules_dir}"
            if self.fail_on_compile:
                raise RuntimeError(msg)
            logger.warning(msg)

    def _compile_rules(self) -> dict:
        """Compile rules per source subdirectory under rules_dir.

        Adapted from OmniScan's YaraScanner.prepare().
        """
        import yara

        compiled: dict = {}
        if not self.rules_dir.exists():
            logger.warning(f"YARA rules directory not found: {self.rules_dir}")
            return compiled

        source_dirs = (
            [self.rules_dir / self.category]
            if self.category
            else [d for d in self.rules_dir.iterdir() if d.is_dir()]
        )

        for source_dir in source_dirs:
            if not source_dir.exists():
                logger.warning(f"Rule directory not found: {source_dir}")
                continue
            rule_files = [
                f
                for f in source_dir.rglob("*.yar*")
                if not _is_hidden(f.relative_to(source_dir))
            ]
            if not rule_files:
                continue
            logger.info(f"Compiling {len(rule_files)} YARA rules from {source_dir.name}")
            try:
                compiled[source_dir.name] = yara.compile(
                    filepaths={str(i): str(f) for i, f in enumerate(rule_files)}
                )
            except yara.Error as e:
                msg = f"YARA compile error in {source_dir.name}: {e}"
                if self.fail_on_compile:
                    raise RuntimeError(msg) from e
                logger.error(msg)

        return compiled

    @staticmethod
    def _to_bytes(value: Any) -> bytes:
        if value is None:
            return b""
        if isinstance(value, (bytes, bytearray, memoryview)):
            return bytes(value)
        return str(value).encode("utf-8", errors="replace")

    def transform(self, table: pa.Table, file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
        if self.input_column not in table.column_names:
            raise ValueError(
                f"Input column '{self.input_column}' not found in table. "
                f"Available: {table.column_names}"
            )

        values = table[self.input_column].to_pylist()
        matched, rules_out, tags_out, cats_out = [], [], [], []

        for value in values:
            data = self._to_bytes(value)
            hit_rules: list[str] = []
            hit_tags: set = set()
            hit_cats: list[str] = []
            if data:
                for category, compiled in self._compiled.items():
                    for m in compiled.match(data=data):
                        hit_rules.append(m.rule)
                        hit_tags.update(m.tags)
                        hit_cats.append(category)
            matched.append(bool(hit_rules))
            rules_out.append(hit_rules)
            tags_out.append(sorted(hit_tags))
            cats_out.append(sorted(set(hit_cats)))

        table = TransformUtils.add_column(
            table, self.matched_column, pa.array(matched, type=pa.bool_())
        )
        table = TransformUtils.add_column(
            table, self.rules_column, pa.array(rules_out, type=pa.list_(pa.string()))
        )
        table = TransformUtils.add_column(
            table, self.tags_column, pa.array(tags_out, type=pa.list_(pa.string()))
        )
        table = TransformUtils.add_column(
            table, self.categories_column, pa.array(cats_out, type=pa.list_(pa.string()))
        )

        nrows = table.num_rows
        infected = sum(matched)
        metadata = {"clean": nrows - infected, "infected": infected}
        logger.debug(f"YARA: {infected}/{nrows} rows matched")
        return [table], metadata


class YaraTransformConfiguration(TransformConfiguration):
    """CLI + configuration binding for YaraTransform."""

    def __init__(self):
        super().__init__(name=shortname, transform_class=YaraTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            f"--{INPUT_COLUMN_KEY}",
            type=str,
            default=DEFAULT_INPUT_COLUMN,
            help="name of the column to scan (bytes or string)",
        )
        parser.add_argument(
            f"--{RULES_DIR_KEY}",
            type=str,
            default=None,
            help="root directory containing per-source subdirs of .yar/.yara files "
                 "(defaults to $DPK_YARA_RULES_DIR, then /app/rules, then <pkg>/../rules)",
        )
        parser.add_argument(
            f"--{CATEGORY_KEY}",
            type=str,
            default=None,
            help="restrict scanning to a single source subdirectory by name",
        )
        parser.add_argument(
            f"--{MATCHED_COLUMN_KEY}",
            type=str,
            default=DEFAULT_MATCHED_COLUMN,
            help="output bool column name",
        )
        parser.add_argument(
            f"--{RULES_COLUMN_KEY}",
            type=str,
            default=DEFAULT_RULES_COLUMN,
            help="output list<string> column name for matched rule names",
        )
        parser.add_argument(
            f"--{TAGS_COLUMN_KEY}",
            type=str,
            default=DEFAULT_TAGS_COLUMN,
            help="output list<string> column name for matched rule tags",
        )
        parser.add_argument(
            f"--{CATEGORIES_COLUMN_KEY}",
            type=str,
            default=DEFAULT_CATEGORIES_COLUMN,
            help="output list<string> column name for source categories that matched",
        )
        parser.add_argument(
            f"--{FAIL_ON_COMPILE_KEY}",
            type=lambda v: str(v).lower() in ("true", "1", "yes", "on"),
            default=DEFAULT_FAIL_ON_COMPILE,
            help="raise on rule compile error instead of logging and continuing",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, True)
        self.params = self.params | captured
        logger.info(f"yara parameters are : {self.params}")
        return True
