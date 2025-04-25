from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[5]

# FILE-BASED registry
FILE_TRANSFORM_REGISTRY = {
    "web2parquet" : 
        {"path": _REPO_ROOT / "transforms/universal/web2parquet/dpk_web2parquet/transform.py",
         "class": "Web2ParquetTransform",
         },
    "doc_chunk" : 
        {"path": _REPO_ROOT / "transforms/language/doc_chunk/dpk_doc_chunk/transform.py",
         "class": "DocChunkTransform",
         },
    "doc_quality" :
        {"path": _REPO_ROOT / "transforms/language/doc_quality/dpk_doc_quality/transform.py",
         "class": "DocQualityTransform",
         },
    "html2parquet" :
        {"path": _REPO_ROOT / "transforms/language/html2parquet/dpk_html2parquet/transform.py",
         "class": "Html2ParquetTransform",
         },
    "lang_id" : 
        {"path": _REPO_ROOT / "transforms/language/lang_id/dpk_lang_id/transform.py",
         "class": "LangIdentificationTransform",
         },
    "pdf2parquet" : 
        {"path": _REPO_ROOT / "transforms/language/pdf2parquet/dpk_pdf2parquet/transform.py",
         "class": "Pdf2ParquetTransform",
         },
    "text_encoder" : 
        {"path": _REPO_ROOT / "transforms/language/text_encoder/dpk_text_encoder/transform.py",
         "class": "TextEncoderTransform",
         },
    "pii_redactor" : 
        {"path": _REPO_ROOT / "transforms/language/pii_redactor/dpk_pii_redactor/transform.py",
         "class": "PIIRedactorTransform",
         },
    "doc_id" : 
        {"path": _REPO_ROOT / "transforms/universal/doc_id/dpk_doc_id/transform_python.py",
         "class": "DocIDTransform",
         },
    "hap" : 
        {"path": _REPO_ROOT / "transforms/universal/hap/dpk_hap/transform.py",
         "class": "HAPTransform",
         },
    # "bloom" :
    #     {"path": _REPO_ROOT / "transforms/universal/bloom/dpk_bloom/transform.py",
    #      "class": "BLOOMTransform",
    #      },
    "ededup" : 
        {"path": _REPO_ROOT / "transforms/universal/ededup/dpk_ededup/transform_python.py",
         "class": "EdedupTransform",
         },
    # "fdedup" : 
    #     {"path": _REPO_ROOT / "transforms/universal/fdedup/dpk_fdedup/transform.py",
    #      "class": "",
    #      },
    "tokenization" : 
        {"path": _REPO_ROOT / "transforms/universal/tokenization/dpk_tokenization/transform.py",
         "class": "TokenizationTransform",
         },
    "similarity" : 
        {"path": _REPO_ROOT / "transforms/language/similarity/dpk_similarity/transform.py",
         "class": "SimilarityTransform",
         },
    "filter" : 
        {"path": _REPO_ROOT / "transforms/universal/filter/dpk_filter/transform.py",
         "class": "FilterTransform",
         },
    "code_profiler" : 
        {"path": _REPO_ROOT / "transforms/code/code_profiler/dpk_code_profiler/transform.py",
         "class": "CodeProfilerTransform",
         },
    "extreme_tokenized" : 
        {"path": _REPO_ROOT / "transforms/language/extreme_tokenized/dpk_extreme_tokenized/transform.py",
         "class": "ExtremeTokenizedTransform",
         },
    "readability" : 
        {"path": _REPO_ROOT / "transforms/language/readability/dpk_readability/transform.py",
         "class": "ReadabilityTransform",
         },
    "profiler" : 
        {"path": _REPO_ROOT / "transforms/universal/profiler/dpk_profiler/runtime.py",
         "class": "ProfilerTransform",
         },
    "resize " : 
        {"path": _REPO_ROOT / "transforms/universal/resize/dpk_resize/transform.py",
         "class": "ResizeTransform",
         },
    "gneissweb_classification" : 
        {"path": _REPO_ROOT / "transforms/language/gneissweb_classification/dpk_gneissweb_classification/transform.py",
         "class": "ClassificationTransform",
         },
    "rep_removal" : 
        {"path": _REPO_ROOT / "transforms/universal/rep_removal/dpk_rep_removal/transform.py",
         "class": "RepRemovalTransform",
         },
    "tokenization2arrow" : 
        {"path": _REPO_ROOT / "transforms/universal/tokenization2arrow/dpk_tokenization2arrow/transform.py",
         "class": "Tokenization2ArrowTransform",
         },
}

MODULE_TRANSFORM_REGISTRY = {
    "web2parquet" :
        {"module": "dpk_web2parquet.transform",
         "class": "Web2ParquetTransform",
         },
    "doc_chunk" :
        {"module": "dpk_doc_chunk.transform",
         "class": "DocChunkTransform",
         },
    "doc_quality" :
        {"module": "dpk_doc_quality.transform",
         "class": "DocQualityTransform",
         },
    "html2parquet" :
        {"module": "dpk_html2parquet.transform",
         "class": "Html2ParquetTransform",
         },
    "lang_id" :
        {"module": "dpk_lang_id.transform",
         "class": "LangIdentificationTransform",
         },
    "pdf2parquet" :
        {"module": "dpk_pdf2parquet.transform",
         "class": "Pdf2ParquetTransform",
         },
    "text_encoder" :
        {"module": "dpk_text_encoder.transform",
         "class": "TextEncoderTransform",
         },
    "pii_redactor" :
        {"module": "dpk_pii_redactor.transform",
         "class": "PIIRedactorTransform",
         },
    "doc_id" :
        {"module": "dpk_doc_id.transform_python",
         "class": "DocIDTransform",
         },
    "hap" :
        {"module": "dpk_hap.transform",
         "class": "HAPTransform",
         },
    # "bloom" :
    #     {"module": "dpk_bloom.transform",
    #      "class": "BLOOMTransform",
    #      },
    "ededup" :
        {"module": "dpk_ededup.transform_python",
         "class": "EdedupTransform",
         },
    # "fdedup" :
    #     {"module": module("transforms/universal/fdedup/dpk_fdedup/transform.py",
    #      "class": "",
    #      },
    "tokenization" :
        {"module": "dpk_tokenization.transform",
         "class": "TokenizationTransform",
         },
    "similarity" :
        {"module": "dpk_similarity.transform",
         "class": "SimilarityTransform",
         },
    "filter" :
        {"module": "dpk_filter.transform",
         "class": "FilterTransform",
         },
    "code_profiler" :
        {"module": "dpk_code_profiler.transform",
         "class": "CodeProfilerTransform",
         },
    "extreme_tokenized" :
        {"module": "dpk_extreme_tokenized.transform",
         "class": "ExtremeTokenizedTransform",
         },
    "readability" :
        {"module": "dpk_readability.transform",
         "class": "ReadabilityTransform",
         },
    "profiler" :
        {"module": "dpk_profiler.runtime",
         "class": "ProfilerTransform",
         },
    "resize " :
        {"module": "dpk_resize.transform",
         "class": "ResizeTransform",
         },
    "gneissweb_classification" :
        {"module": "dpk_gneissweb_classification.transform",
         "class": "ClassificationTransform",
         },
    "rep_removal" :
        {"module": "dpk_rep_removal.transform",
         "class": "RepRemovalTransform",
         },
    "tokenization2arrow" :
        {"module": "dpk_tokenization2arrow.transform",
         "class": "Tokenization2ArrowTransform",
         },
}