# OpenSource Transform 
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
The openserach transform creates and inserts data into an index.
If an embeddings column is present, a [k-NN vector index](https://docs.opensearch.org/latest/vector-search/creating-vector-index/) is created; otherwise, a regular index is used.

## Output Format
None

## Usage

The following command line arguments are available in addition to the options provided by the launcher.

```bash
  --os_index OS_INDEX   Specify the name of the OpenSearch Index to write. If the index does not already exist, it will be automatically created.
  --os_document_id_column_name OS_DOCUMENT_ID_COLUMN_NAME
                        Name of the table column that identy a unique document ID
  --os_embeddings_column_name OS_EMBEDDINGS_COLUMN_NAME
                        Embeddings Column name
  --os_dimension_size OS_DIMENSION_SIZE
                        Embeddings length
  --os_content_column_name OS_CONTENT_COLUMN_NAME
                        Column name to get content
  --os_delete_index OS_DELETE_INDEX
                        If set to true, the index will be deleted before the transform is applied. 
                        If the index does not exist, no action is taken.
  --os_disable_security OS_DISABLE_SECURITY
                        If True, the OpenSearch server works without security checks and the client should use http, 
                        without username and password. If False, OPENSEARH_USERID and OPENSEARCH_PASSWORD 
                        environment variables must be defined.
  --os_verify_certs OS_VERIFY_CERTS
                        If True, the OpenSearch client and server should use correct SSL certificates
```

If `os_disable_security` option is `False`, set OpenSearch credentials via the following environment 
variables before running:

```bash
export OPENSEARH_USERID=admin
export OPENSEARCH_PASSWORD=""
```

# Local Opensearch execution

If you don't have Opensearch server, you can install it according to the [instructions](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/index/). 

Probably, the simplest way is to execute Opensearch in Docker containers:
```bash
git clone   https://github.com/opensearch-project/opensearch-build
export OPENSEARCH_INITIAL_ADMIN_PASSWORD=mypassword
cd opensearch-build/docker/release/dockercomposefiles/
docker-compose -f docker-compose-default.x.yml up -d 
```

If you want to run Opensearch **without** security protections (developer, demo mode)
```bash
docker-compose -f ./unsecured-docker-compose.yaml up -d
```
In this case you don't need username and password to access opensearch REST API and its dashboard.
