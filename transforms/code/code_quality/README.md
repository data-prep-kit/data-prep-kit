# Code Quality Transform

The Code Quality transforms captures code specific metrics of input data.

Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions, transform configuration, testing and IDE setup.

## Summary

This transform adds code quality a for documents using multiple heuristics (e.g., length, token ratio, etc.). It supports configuration of tokenizer and language-related fields.

## Configuration and Command Line Options

The set of dictionary keys holding [CodeQualityTransform](dpk_code_quality/transform.py) configuration are as follows:

| Key name                | Default                | Description                                              |
|-------------------------|------------------------|----------------------------------------------------------|
| contents_column_name    | contents               | Name of the column that holds the code/document content  |
| language_column_name    | language               | Name of the column that holds programming language information      |
| tokenizer               | codeparrot/codeparrot  | HuggingFace tokenizer to use                             |
| hf_token                | env-based              | HuggingFace auth token (optional if public)              |



## Example

```bash
python -m dpk_code_quality.runtime \\
  --cq_contents_column_name contents \\
  --cq_language_column_name language \\
  --cq_tokenizer codeparrot/codeparrot \\
  --cq_hf_token <your_hf_token> \\
  --data_local_config "{'input_folder': 'test-data/input', 'output_folder': 'output'}"
