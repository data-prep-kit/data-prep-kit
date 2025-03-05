# from https://github.ibm.com/mc-connectors/connector/blob/main/gin/common/ai_platforms/callbacks.py

from typing import Dict, Any, List

import logging

from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult

from llm_utils.logging import Logging


class LoggingCallbackHandler(BaseCallbackHandler):
    """
    Callbacks for printing LLM prompt and response.
    """

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""

        llm_log = logging.getLogger(Logging.LLM)
        for prompt in prompts:
            llm_log.info("***LLM prompt***\n%s\n", prompt)
        for handler in llm_log.handlers:
            handler.flush()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        llm_log = logging.getLogger(Logging.LLM)
        llm_log.info("***LLM Response:***\n%s\n", response.generations[0][0].text)
        for handler in llm_log.handlers:
            handler.flush()

    def on_llm_error(self, error, *, run_id, parent_run_id=None, **kwargs) -> Any:
        """Run when LLM returns error."""
        llm_log = logging.getLogger(Logging.LLM)
        llm_log.error(f"***LLM Error:***\n{error}\n")
        for handler in llm_log.handlers:
            handler.flush()

    def on_tool_start(
        self,
        serialized,
        input_str,
        *,
        run_id,
        parent_run_id=None,
        tags=None,
        metadata=None,
        inputs=None,
        **kwargs,
    ):
        """Run when tool starts running"""
        tool_log = logging.getLogger(Logging.TOOL_CALLING)
        tool_log.info(f"***Tool start***\n{serialized}\n{input_str=}\n")

    def on_tool_end(self, output, *, run_id, parent_run_id=None, **kwargs) -> Any:
        """Run when tool ends running."""
        tool_log = logging.getLogger(Logging.TOOL_CALLING)
        tool_log.info(f"***Tool Response***\n{output}\n")

    def on_tool_error(self, error, *, run_id, parent_run_id = None, **kwargs) -> Any:
        """Run when tool returns error."""
        tool_log = logging.getLogger(Logging.TOOL_CALLING)
        tool_log.error(f"***Tool Error:***\n{error}\n")
