# Folder2Parquet

The Folder2Parquet transforms load content form files and folders into a parquet file.
Per the set of [transform project conventions](../../README.md#transform-project-conventions)
the following runtimes are available:

* python - provides the base python-based transformation
  implementation.

Also, please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Contributors

- Maroun Touma (touma@us.ibm.com)


## Summary

Create one or more parquet files where each row represent the content read from the files found in the designated input folder, subfolders and zip files. The default behavior for the transform is to create a single parquet for each subfolder and each zip file. 


## Parameters

The transform can be initialized with the following parameters.

| Parameter                 | Default         | Description                                                                                                                                                                                          |
|---------------------------|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `data_files_to_use`       | -               | The files extensions to be considered when running the transform. Example value `['.txt','.pdf','.docx','.pptx','.zip']`.                        |
| `fewer_parquets`              | False              | Reduce the number of parquet files by consolidating all files found in all subfolders in a single parquet. zip files will always be loaded into seperate zip files                                                                             |
                                                  
