from llama_index.core.tools.tool_spec.base import BaseToolSpec


class DPKTransformsToolSpec(BaseToolSpec):
    """

    DPK transforms.

    Methods:
        code2parquet(self, **kwargs) -> str:
           Applies code2parquet transform. Returns a string with the result.
        code_quality(self, **kwargs) -> str:
           Applies code_quality transform. Returns a string with the result.
        prolang_select(self, **kwargs) -> str:
           Applies prolang_select transform. Returns a string with the result.
        doc_chunk(self, **kwargs) -> str:
           Applies doc_chunk transform. Returns a string with the result.
        doc_chunk(self, **kwargs) -> str:
           Applies code2parquet transform. Returns a string with the result.
        doc_quality(self, **kwargs) -> str:
           Applies doc_quality transform. Returns a string with the result.
        lang_id(self, **kwargs) -> str:
           Applies lang_id transform. Returns a string with the result.
        pdf2parquet(self, **kwargs) -> str:
           Applies pdf2parquet transform. Returns a string with the result.
        pii_redactor(self, **kwargs) -> str:
           Applies pii_redactor transform. Returns a string with the result.
        text_encoder(self, **kwargs) -> str:
           Applies text_encoder transform. Returns a string with the result.
        doc_id(self, **kwargs) -> str:
           Applies doc_id transform. Returns a string with the result.
        ededup(self, **kwargs) -> str:
           Applies ededup transform. Returns a string with the result.
        fdedup(self, **kwargs) -> str:
           Applies fdedup transform. Returns a string with the result.
        doc_id(self, **kwargs) -> str:
           Applies doc_id transform. Returns a string with the result.
        filter(self, **kwargs) -> str:
           Applies filter transform. Returns a string with the result.
        resize(self, **kwargs) -> str:
           Applies resize transform. Returns a string with the result.
        tokenization(self, **kwargs) -> str:
           Applies tokenization transform. Returns a string with the result.

    """

    spec_functions = ["code2parquet", "code_quality", "prolang_select", "doc_chunk", "doc_quality", "lang_id",
                      "pdf2parquet", "pii_redactor", "text_encoder", "doc_id", "ededup", "fdedup", "filter",
                      "resize", "tokenization"]

    def code2parquet(self, **kwargs) -> str:
        from .code import code2parquet

        return code2parquet.code2parquet(kwargs=kwargs)

    def code_quality(self, **kwargs) -> str:
        from .code import code_quality

        return code_quality.code_quality(kwargs=kwargs)

    def prolang_select(self, **kwargs) -> str:
        from .code import proglang_select

        return proglang_select.proglang_select(kwargs=kwargs)

    def doc_chunk(self, **kwargs) -> str:
        from .language import doc_chunk

        return doc_chunk.doc_chunk(kwargs=kwargs)

    def doc_quality(self, **kwargs) -> str:
        from .language import doc_quality

        return doc_quality.doc_quality(kwargs=kwargs)

    def lang_id(self, **kwargs) -> str:
        from .language import lang_id

        return lang_id.lang_id(kwargs=kwargs)

    def pdf2parquet(self, **kwargs) -> str:
        from .language import pdf2parquet

        return pdf2parquet.pdf2parquet(kwargs=kwargs)

    def pii_redactor(self, **kwargs) -> str:
        from .language import pii_redactor

        return pii_redactor.pii_redactor(kwargs=kwargs)

    def text_encoder(self, **kwargs) -> str:
        from .language import text_encoder

        return text_encoder.text_encoder(kwargs=kwargs)

    def doc_id(self, **kwargs) -> str:
        from .universal import doc_id

        return doc_id.doc_id(kwargs=kwargs)

    def ededup(self, **kwargs) -> str:
        from .universal import ededup

        return ededup.ededup(kwargs=kwargs)

    def fdedup(self, **kwargs) -> str:
        from .universal import fdedup

        return fdedup.fdedup(kwargs=kwargs)

    def filter(self, **kwargs) -> str:
        from .universal import filter

        return filter.filter(kwargs=kwargs)

    def resize(self, **kwargs) -> str:
        from .universal import resize

        return resize.resize(kwargs=kwargs)

    def tokenization(self, **kwargs) -> str:
        from .universal import tokenization

        return tokenization.tokenization(kwargs=kwargs)
