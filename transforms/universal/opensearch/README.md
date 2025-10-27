# OpenSearch Transform 
Please see the set of
[transform project conventions](../../README.md#transform-project-conventions)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
The OpenSearch Transform takes a table and pushes its rows into an OpenSearch index. If the table includes a column with embeddings (i.e., lists of floats), the transform sets up a k-NN vector index so you can run similarity searches. If there’s no embeddings column, it just creates a regular keyword-based index.
You can control the index name, document ID column, and which columns hold the content and embeddings. The transform also lets you delete an existing index before writing, and configure security settings depending on whether your OpenSearch server uses authentication and SSL.
This transform is useful when you want to make your data searchable—either by keywords or by vector similarity—using OpenSearch.

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
                        without username and password. If False, OPENSEARCH_USERID and OPENSEARCH_PASSWORD 
                        environment variables must be defined.
  --os_verify_certs OS_VERIFY_CERTS
                        If True, the OpenSearch client and server should use correct SSL certificates
```

If the `os_disable_security` option is `False`, set OpenSearch credentials via the following environment 
variables before running:

```bash
export OPENSEARCH_USERID=admin
export OPENSEARCH_PASSWORD="Mypass1word"
```
Please note that the password is the **same** password that you have set for the OpenSearch server (see below)
# Local OpenSearch execution

If you don't have an Openearch server, you can install it according to these [instructions](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/index/). 

Probably, the simplest way is to execute OpenSearch in Docker containers:

```bash
git clone   https://github.com/opensearch-project/opensearch-build
export OPENSEARCH_INITIAL_ADMIN_PASSWORD=Mypass1word
cd opensearch-build/docker/release/dockercomposefiles/
docker-compose -f docker-compose-default.x.yml up -d 
```

Please note that the password has to contain at least 8 characters, including uppercase and lowercase letters, and a number. 
Also, since docker-compose is downloading the image from Docker Hub by default, you may run into a docker credential issue (rate limit) for an unauthenticated account. In this case, please login to docker before the docker-compose command above:
```bash
docker login docker.io -u yourdockerusername -p yourdockerpassword
```

If you want, you can execute OpenSearch **without** security protections (developer, demo mode). The yml file below is provided in the DPK repo and is not in the `opensearch-build/docker/release/dockercomposefiles/` directory above. 
```bash
docker-compose -f ./unsecured-docker-compose.yml up -d
```
In this case, you don't need a username and a password to access the OpenSearch REST API or its dashboard.

You can check the OpenSearch dashboard by logging into: http://localhost:5601/ after the server has started. 
