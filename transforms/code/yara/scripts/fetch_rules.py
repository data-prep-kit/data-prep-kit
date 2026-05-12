#!/usr/bin/env python3
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
# Fetch YARA rules defined in sources.json. Tracks upstream HEAD (no commit
# pinning). Writes rules into <rules-dir>/<sanitized_source_name>/ preserving
# the source repo's subpath layout, and emits <rules-dir>/MANIFEST.json for
# provenance.
#
# Rule compile/match adapted from OmniScan (Dhilung Kirat, IBM Research).

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def sanitize(name: str) -> str:
    return re.sub(r"[-\s]+", "_", re.sub(r"[^\w\s-]", "", name)).lower()


def is_hidden(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def clone_shallow(git_url: str, dest: Path) -> None:
    subprocess.run(
        ["git", "clone", "--depth=1", git_url, str(dest)],
        check=True,
        capture_output=True,
        timeout=300,
    )


def copy_yara_files(src: Path, dest: Path) -> int:
    count = 0
    for pattern in ("*.yar", "*.yara"):
        for f in src.rglob(pattern):
            rel = f.relative_to(src)
            if is_hidden(rel):
                continue
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
            count += 1
    return count


def fetch(sources_path: Path, rules_dir: Path) -> dict:
    with sources_path.open() as f:
        sources = json.load(f)

    rules_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources_file": str(sources_path),
        "sources": [],
    }

    for source in sources:
        if source.get("type") != "yara":
            continue
        name = source["name"]
        git_url = source.get("git_url") or source.get("giturl")
        if not git_url:
            print(f"[skip] {name}: no git_url", file=sys.stderr)
            continue

        slug = sanitize(name)
        out_dir = rules_dir / slug
        if out_dir.exists():
            shutil.rmtree(out_dir)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / slug
            print(f"[fetch] {name} <- {git_url}")
            try:
                clone_shallow(git_url, tmp_path)
            except subprocess.CalledProcessError as e:
                print(f"[error] clone failed: {e.stderr.decode(errors='replace')}", file=sys.stderr)
                continue
            file_count = copy_yara_files(tmp_path, out_dir)

        manifest["sources"].append(
            {
                "name": name,
                "slug": slug,
                "url": source.get("url"),
                "git_url": git_url,
                "license": source.get("license"),
                "file_count": file_count,
            }
        )
        print(f"[done] {name}: {file_count} rule files -> {out_dir}")

    manifest_path = rules_dir / "MANIFEST.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[manifest] {manifest_path}")
    return manifest


def main() -> int:
    here = Path(__file__).resolve().parent
    default_sources = here.parent / "assets" / "sources.json"
    default_rules = here.parent / "rules"

    parser = argparse.ArgumentParser(description="Fetch YARA rules from sources.json (HEAD).")
    parser.add_argument("--sources", type=Path, default=default_sources,
                        help=f"Path to sources.json (default: {default_sources})")
    parser.add_argument("--rules-dir", type=Path, default=default_rules,
                        help=f"Output rules directory (default: {default_rules})")
    args = parser.parse_args()

    if not args.sources.exists():
        print(f"[error] sources file not found: {args.sources}", file=sys.stderr)
        return 1

    fetch(args.sources, args.rules_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
