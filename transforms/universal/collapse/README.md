# Document ID Python Annotator

Please see the set of [transform project conventions](../../README.md#transform-project-conventions) for details on general project conventions,
transform configuration, testing and IDE set up.

## Contributors
- Maroun Touma (touma@us.ibm.com)

## Description

This transform merges all the text columns specified by the user into a single column. By default, the merged columns will be removed from the parquet file to reduce the overall size of the output parquet file

## Input Parameters Used by This Transform

| Configuration Parameters                    | Data Type | Description                      |
|---------------------------------------------|-----------|----------------------------------|
| coillpase_input_columns | list       | List of columns that need to be merged together |
| coillpase_output_column | str        | Name of the resulting column that will contain the merged text     |
| coillpase_field_seperator| str       | Character used to sperate the merged content. Default value is '.' |


## Usage

### Code example

[notebook](collapse.ipynb)


