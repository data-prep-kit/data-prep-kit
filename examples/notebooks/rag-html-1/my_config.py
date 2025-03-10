import os 

## Configuration
class MyConfig:
    pass 

MY_CONFIG = MyConfig ()

## Crawl settings
MY_CONFIG.CRAWL_URL_BASE = 'https://thealliance.ai/'
# MY_CONFIG.CRAWL_URL_BASE = 'https://apache.org/'
MY_CONFIG.CRAWL_MAX_DOWNLOADS = 20
MY_CONFIG.CRAWL_MAX_DEPTH = 2
MY_CONFIG.CRAWL_MIME_TYPE = 'text/html'

## Directories
MY_CONFIG.INPUT_DIR = "input"
# MY_CONFIG.INPUT_DIR = "input2/thealliance.ai/"
MY_CONFIG.OUTPUT_DIR = "output"
MY_CONFIG.OUTPUT_DIR_HTML = os.path.join(MY_CONFIG.OUTPUT_DIR , "1-html2parquet")
MY_CONFIG.OUTPUT_DIR_MARKDOWN = os.path.join(MY_CONFIG.OUTPUT_DIR , "2-markdown")
### -------------------------------


# MY_CONFIG.EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
MY_CONFIG.EMBEDDING_MODEL = 'BAAI/bge-small-en-v1.5'
MY_CONFIG.EMBEDDING_LENGTH = 384


### Milvus config
MY_CONFIG.DB_URI = './rag_html.db'  # For embedded instance
MY_CONFIG.COLLECTION_NAME = 'docs'


## LLM Model
# MY_CONFIG.LLM_MODEL = "meta/meta-llama-3-8b-instruct"
# MY_CONFIG.LLM_MODEL = "meta/meta-llama-3-70b-instruct"
# MY_CONFIG.LLM_MODEL = "ibm-granite/granite-3.0-2b-instruct"
MY_CONFIG.LLM_MODEL = "ibm-granite/granite-3.0-8b-instruct"
