# OpenSource Transform 
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
The openserach transform creates and inserts data into an [OpenSearch k-NN vector index](https://docs.opensearch.org/latest/vector-search/creating-vector-index/). 
It assumes that embeddings are generated externally, following the process described in the [OpenSearch documentation](https://docs.opensearch.org/latest/vector-search/creating-vector-index/#storing-raw-vectors-or-embeddings-generated-outside-of-opensearch)
. For details on how to search the vector store, please refer to the [OpenSearch documentation](https://docs.opensearch.org/latest/vector-search/searching-data/).

## Output Format
None

## Usage
The following command line arguments are available in addition to the options provided by the launcher.

```bash
  --os_host OS_HOST     Specify the OpenSearch host:port. Defaults to localhost:9200
  --os_index OS_INDEX   Specify the name of the OpenSearch Index to write
  --os_document_id_column_name OS_DOCUMENT_ID_COLUMN_NAME
                        Name of the table column that identy a unique document ID
  --os_embeddings_column_name OS_EMBEDDINGS_COLUMN_NAME
                        Embeddings Column name
  --os_dimension_size OS_DIMENSION_SIZE
                        Embeddings length
  --os_content_column_name OS_CONTENT_COLUMN_NAME
                        Column name to get content
  --os_delete_index OS_DELETE_INDEX
                        If true, delete the index before applying the transform
```

