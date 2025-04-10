# Header Cleanser Transform

The Header Cleanser transform removes license and copyright headers from code files.

Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions, transform configuration, testing and IDE setup.

## Summary

The **Header Cleanser** module is a versatile tool designed to remove license and copyright headers from code files.  
It supports over 90 programming languages and utilizes the [ScanCode Toolkit](https://scancode-toolkit.readthedocs.io/en/stable/getting-started/install.html) to identify license and copyright information.

## Configuration and Command Line Options

The set of dictionary keys holding [HeaderCleanserTransform](dpk_header_cleanser/transform.py) configuration are as follows:

| Key name     | Default  | Description                                       |
|--------------|----------|---------------------------------------------------|
| column       | contents | Name of the input column containing code          |
| license      | true     | Whether to remove license headers                 |
| copyright    | true     | Whether to remove copyright headers               |

### Launched Command Line Options

When running the transform with the Ray launcher (`TransformLauncher`), the following command-line arguments are available in addition to the [launcher options](../../../data-processing-lib/doc/launcher-options.md):

- `--header_cleanser_column` – sets the input column name  
- `--header_cleanser_license` – whether to remove license (true/false)  
- `--header_cleanser_copyright` – whether to remove copyright (true/false)  
- `--header_cleanser_n_processes` – number of processes to use  
- `--header_cleanser_tmp_dir` – temp directory for intermediate files  
- `--header_cleanser_timeout` – timeout per file in seconds  
- `--header_cleanser_skip_timeout` – whether to skip files on timeout  

## Example

```bash
python -m dpk_header_cleanser.runtime \
  --header_cleanser_column contents \
  --header_cleanser_license true \
  --header_cleanser_copyright true \
  --data_local_config "{'input_folder': 'test-data/input', 'output_folder': 'output'}"
```

## Sample Notebook

[header_cleanser.ipynb](../header_cleanser.ipynb)


## Testing

Currently, we have:
* [Unit test](test/test_header_cleanser.py)
* [Unit test for Ray](test/test_header_cleanser_ray.py)
