from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from langchain_core.tools import BaseTool, BaseToolkit
from langchain_core.utils.pydantic import get_fields
from pydantic import model_validator

# from noop_tool import NoopTransform
from llm_utils.dpk.langchain_tools.tools.universal.fdedup import FdedupTransform
from llm_utils.dpk.langchain_tools.tools.universal.ededup import EdedupTransform
from llm_utils.dpk.langchain_tools.tools.universal.filter import FilterTransform
from llm_utils.dpk.langchain_tools.tools.universal.resize import ResizeTransform
from llm_utils.dpk.langchain_tools.tools.universal.tokenization import TokenizationTransform
from llm_utils.dpk.langchain_tools.tools.universal.doc_id import DocIDTransform


from llm_utils.dpk.langchain_tools.tools.code.code2parquet import Code2ParquetTransform
from llm_utils.dpk.langchain_tools.tools.code.code_quality import CodeQualityTransform
from llm_utils.dpk.langchain_tools.tools.code.proglang_select import ProgLangSelectTransform


from llm_utils.dpk.langchain_tools.tools.language.doc_chunk import DocChunkTransform
from llm_utils.dpk.langchain_tools.tools.language.doc_quality import DocQualityTransform
from llm_utils.dpk.langchain_tools.tools.language.lang_id import LangIdentificationTransform
from llm_utils.dpk.langchain_tools.tools.language.pdf2parquet import Pdf2parquetTransform
from llm_utils.dpk.langchain_tools.tools.language.text_encoder import TextEncoderTransform
from llm_utils.dpk.langchain_tools.tools.language.pii_redactor import PIIRedactorTransform


_FILE_TOOLS: List[Type[BaseTool]] = [
    FdedupTransform,
    EdedupTransform,
    FilterTransform,
    ResizeTransform,
    TokenizationTransform,
    DocIDTransform,
    Pdf2parquetTransform,
    CodeQualityTransform,
    ProgLangSelectTransform,
    DocChunkTransform,
    DocQualityTransform,
    Code2ParquetTransform,
    LangIdentificationTransform,
    TextEncoderTransform,
    PIIRedactorTransform,
]
_FILE_TOOLS_MAP: Dict[str, Type[BaseTool]] = {
    get_fields(tool_cls)["name"].default: tool_cls for tool_cls in _FILE_TOOLS
}


class DataPrepKitToolkit(BaseToolkit):
    """Toolkit for applying data transformations using data prep kit.

    Parameters:
        selected_tools: Optional. The tools to include in the toolkit. If not
            provided, all tools are included.
    """

    selected_tools: Optional[List[str]] = None
    """If provided, only provide the selected tools. Defaults to all."""

    @model_validator(mode="before")
    @classmethod
    def validate_tools(cls, values: dict) -> Any:
        selected_tools = values.get("selected_tools") or []
        for tool_name in selected_tools:
            if tool_name not in _FILE_TOOLS_MAP:
                raise ValueError(
                    f"File Tool of name {tool_name} not supported."
                    f" Permitted tools: {list(_FILE_TOOLS_MAP)}"
                )
        return values

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        allowed_tools = self.selected_tools or _FILE_TOOLS_MAP
        tools: List[BaseTool] = []
        for tool in allowed_tools:
            tool_cls = _FILE_TOOLS_MAP[tool]
            tools.append(tool_cls())  # type: ignore[call-arg]
        return tools


__all__ = ["DataPrepKitToolkit"]
