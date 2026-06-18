# YARA Transform

The YARA Transform scans a bytes (or string) column using [YARA](https://virustotal.github.io/yara/) rules and annotates each row with match metadata. It is the natural downstream of `folder2parquet`: ingest arbitrary files into a parquet with a `binary_contents` column, then run YARA over those bytes to flag malware, suspicious patterns, or corpus contaminants.

Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up. The following runtimes are available:

* [python](./dpk_yara/transform.py) — base Python implementation
* [ray](./dpk_yara/ray/runtime.py) — the base transform running under Ray

## Contributors

- Dhilung Kirat (dkirat@us.ibm.com)
- Shalisha Witherspoon (shalisha.witherspoon@ibm.com)

## Summary

For each row, the transform scans the value of `yara_input_column` (default `binary_contents`) against every rule in every source subdirectory of the configured rules directory, and appends four columns:

| Column | Type | Meaning |
|---|---|---|
| `yara_matched` | bool | Any rule matched |
| `yara_rules` | list<string> | Matched rule names |
| `yara_tags` | list<string> | Union of tags across matches |
| `yara_categories` | list<string> | Source subdirectories that contributed a match |

The transform accepts either binary or string columns. Strings are encoded UTF-8 (with `errors="replace"`). Nulls are treated as empty and never match.

## Rules

Rules are organized as `<rules_dir>/<source_name>/<preserved/subpaths>/*.yar`. Each top-level subdirectory is compiled as an independent ruleset so `yara_categories` can attribute matches back to their upstream source.

### Rule sources

Rule sources are declared in [`assets/sources.json`](./assets/sources.json). Each entry:

```json
{
  "type": "yara",
  "name": "ReversingLabs YARA Rules",
  "git_url": "https://github.com/reversinglabs/reversinglabs-yara-rules.git",
  "license": "MIT"
}
```

To add a new source, add an entry and rebuild the image (or re-run `scripts/fetch_rules.py`).

### Bootstrapping rules

Rules are **not committed** — they are fetched at build time. Docker images bake them into `/app/rules` via `scripts/fetch_rules.py` (shallow clones, tracks upstream HEAD). For local development:

```bash
python scripts/fetch_rules.py
# or:
make fetch-rules
```

`make venv` runs this automatically.

### Rules directory resolution

The transform resolves `yara_rules_dir` in this order:

1. `--yara_rules_dir` CLI arg / `yara_rules_dir` config key
2. `$DPK_YARA_RULES_DIR`
3. `/app/rules` (baked into the Docker image)
4. `<package_dir>/../rules` (populated by `fetch_rules.py` in source tree)

## Configuration and Command Line Options

| Key | Default | Description |
|---|---|---|
| `yara_input_column` | `binary_contents` | Column to scan (bytes or string) |
| `yara_rules_dir` | auto-resolve | Root of rule source subdirectories |
| `yara_category` | `None` | Restrict scanning to one source subdirectory |
| `yara_matched_column` | `yara_matched` | Output bool column |
| `yara_rules_column` | `yara_rules` | Output list<string> of matched rule names |
| `yara_tags_column` | `yara_tags` | Output list<string> of tags |
| `yara_categories_column` | `yara_categories` | Output list<string> of source categories |
| `yara_fail_on_compile_error` | `false` | Raise on rule compile failure instead of logging |

## Metadata Fields

Per-table statistics (aggregated by the runtime):

* `clean` — rows with no match
* `infected` — rows with at least one match

## Pipeline example

```
folder2parquet  →  yara  →  filter (drop yara_matched == true)
```

`folder2parquet` produces `binary_contents`, `file_name`, `document_uuid`. `yara` annotates it. `filter` can then quarantine or drop matched rows.

## Running

### Locally

```bash
make venv               # creates venv, installs deps, fetches rules
source venv/bin/activate
python -m dpk_yara.local_python
```

### Tests

```bash
make test
```

Tests use `test-rules/eicar/eicar.yar` (committed) so they run hermetically without network access.

### Docker

```bash
make image
```

Produces a Python image with rules baked in under `/app/rules` and `DPK_YARA_RULES_DIR` pre-set.

## Credits

Bundled rule sources (fetched at build time from `assets/sources.json`):

| Source | License | URL |
|---|---|---|
| ReversingLabs YARA Rules | MIT | https://github.com/reversinglabs/reversinglabs-yara-rules |
| Trellix ATR YARA Rules | Apache-2.0 | https://github.com/advanced-threat-research/Yara-Rules |
