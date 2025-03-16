# Merge Transform
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary
This transform merges two or more tables, assuming that while the tables have different sets of columns, their rows
contain the same data. It facilitates **embarrassingly parallel** data processing by merging the results.

The transform receives a list of directories (merge_input_dirs) from which the tables to be merged are located.
One of these tables serves as the main table and is provided as a regular table for other transforms. The transform
loads the tables to be merged based on the specified directories and the relative path of the main table.

Example:

- Data Access input_folder: test/input
- merge_input_dirs: test/input1,test/input2
- main Table Path: test/input/a/b.parquet
- tables to Merge: test/input1/a/b.parquet and test/input2/a/b.parquet

In this scenario, the main table is created from the `test/input/a/b.parquet` file, and the transform will merge it with
tables based on `test/input1/a/b.parquet` and `test/input2/a/b.parquet` files.

Note: this transformer doesn't support Data Access with multiple input parameters.
