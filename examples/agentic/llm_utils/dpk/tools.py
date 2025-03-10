tools_json = '''
[
    {"name": "exact_dedup", "description": "Exact data deduplication is used to identify (and remove) redundant records.",
        "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
            {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"}],
        "import": "from llm_utils.dpk.langchain_tools.tools.universal.ededup import EdedupTransform"},

    {"name": "Pdf2Parquet", "description": "The Pdf2Parquet transform generates parquet files containing the converted document.",
        "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
            {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"},
            {"name": "data_files_to_use", "description": "files extentions to transform.", "type": "list"}],
        "import": "from llm_utils.dpk.langchain_tools.tools.language.pdf2parquet import Pdf2parquetTransform"},

    {"name": "doc_quality", "description": "The doc_quality transform will calculate and annotate several metrics which are useful to assess the quality of the document.",
        "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
            {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"},
            {"name": "docq_bad_word_filepath", "description": "path to bad words file.", "type": "str"}],
        "import": "from llm_utils.dpk.langchain_tools.tools.language.doc_quality import DocQualityTransform"},

    {"name": "document_id", "description": "The Document ID transforms adds a document identification (unique integers and content hashes), which later can be used in de-duplication operations.",
    "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
        {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"},
        {"name": "doc_id_int_column", "description": "Compute unique integer id and place in the given named column.", "type": "str"}],
    "import": "from llm_utils.dpk.langchain_tools.tools.universal.doc_id import DocIDTransform"},

    {"name": "language_id", "description": "The Language Identification transforms added a column containing the language of the document.",
    "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
        {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"}],
    "import": "from llm_utils.dpk.langchain_tools.tools.language.lang_id import LangIdentificationTransform"},

    {"name": "filter_transform", "description": "The filter transforms provides SQL-based expressions for filtering rows and optionally column removal from parquet files.",
    "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
        {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"},
        {"name": "filter_criteria_list", "description": "list of sql queries to filter the input files.", "type": "list"}],
    "import": "from llm_utils.dpk.langchain_tools.tools.universal.filter import FilterTransform"},

    {"name": "tokenization", "description": "The tokenization transform annotates pyarrow tables and parquet files to add a column containing tokens for the document column.",
    "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
        {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"}],
    "import": "from llm_utils.dpk.langchain_tools.tools.universal.tokenization import TokenizationTransform"},

    {"name": "tool_not_implemented", "description": "A placeholder tool for the casses when a suitable tool cannot be found"}
]
'''

# tools_json = json.dumps(json.loads(tools_json))
# {"name": "fuzzy_dedup", "description": "The fdedup transforms removes documents that are very similar to each other.",
#     "input": [{"name": "in_folder", "description": "input directory to transform files from.", "type": "str"},
#         {"name": "out_folder", "description": "destination directory to store the transformed files.", "type": "str"}],
#     "import": "from llm_utils.dpk.langchain_tools.tools.universal.fdedup import FdedupTransform"},