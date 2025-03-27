import os
from dotenv import dotenv_values
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import LLM
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import BaseMessage, ChatResult, ChatGeneration, AIMessage
from langchain.chat_models.base import BaseChatModel
from pydantic import Field
from llm_utils.callbacks import LoggingCallbackHandler
from typing import Iterator, List, Optional, Any, Dict
import replicate

CONFIG_LOCATION = ".env"


class ReplicateChatModel(BaseChatModel):
    model_id: str = Field(description="The Replicate model ID")
    params: Dict = Field(default_factory=dict, description="Model parameters")

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional = None,
                  **kwargs) -> ChatResult:
        prompt = " ".join(m.content for m in messages)
        response = replicate.run(self.model_id, input={"prompt": prompt, **self.params})
        message = AIMessage(content=response)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional = None,
                **kwargs) -> Iterator[ChatGeneration]:
        print(f"replicate stream")
        prompt = " ".join(m.content for m in messages)
        for chunk in replicate.stream(self.model_id, input={"prompt": prompt, **self.params}):
            yield ChatGeneration(message=AIMessage(content=chunk))

    @property
    def _llm_type(self) -> str:
        return "replicate"


def getLLM(inference: str, model_id: str = None, config: dict = None) -> LLM:
    loggingCallbackHandler = LoggingCallbackHandler()
    if config is None:
        config = dotenv_values(CONFIG_LOCATION)

    if inference == "ollama":
        from langchain_ollama.llms import OllamaLLM

        if model_id is None or len(model_id) == 0:
            model_id = "llama3.1:70b"
        return OllamaLLM(model=model_id, temperature=0, callbacks=[loggingCallbackHandler])
    elif inference == "watsonx":
        from langchain_ibm import WatsonxLLM
        from genai.schema import DecodingMethod

        parameters = {
            "decoding_method": DecodingMethod.GREEDY,
            "max_new_tokens": 1024,
            "min_new_tokens": 1,
            "temperature": 0,
            "top_k": 50,
            "top_p": 1,
        }
        if model_id is None or len(model_id) == 0:
            # see supported models at https://dataplatform.cloud.ibm.com/samples?context=wx
            model_id = "meta-llama/llama-3-70b-instruct"

        return WatsonxLLM(
            model_id=model_id,
            apikey=config["WATSONX_APIKEY"],
            url=config["WATSONX_URL"],
            project_id=config["WATSON_PROJECT_ID"],
            params=parameters,
            callbacks=[loggingCallbackHandler],

        )
    else:
        raise ValueError(
            f"Inference type {inference} is wrong, supported values are [ollama, watsonx]"
        )


def getChatLLM(
        inference: str, model_id: str = None, config: dict = None, params: Optional[Dict[str, Any]] = None
) -> BaseChatModel:
    loggingCallbackHandler = LoggingCallbackHandler()

    if config is None:
        config = dotenv_values(CONFIG_LOCATION)

    if inference == "ollama":
        from langchain_ollama import ChatOllama

        if model_id is None or len(model_id) == 0:
            model_id = "llama3.1:70b"
        return ChatOllama(model=model_id, temperature=0, callbacks=[loggingCallbackHandler])

    elif inference == "watsonx":
        from langchain_ibm import ChatWatsonx
        from genai.schema import DecodingMethod

        parameters = {
            "decoding_method": DecodingMethod.GREEDY,
            "max_new_tokens": 1024,
            "min_new_tokens": 1,
            "temperature": 0,
            "top_k": 50,
            "top_p": 1,
        }
        if model_id is None or len(model_id) == 0:
            # see supported models at https://dataplatform.cloud.ibm.com/samples?context=wx
            model_id = "meta-llama/llama-3-70b-instruct"

        return ChatWatsonx(
            model_id=model_id,
            apikey=config["WATSONX_APIKEY"],
            url=config["WATSONX_URL"],
            project_id=config["WATSON_PROJECT_ID"],
            params=parameters,
            callbacks=[loggingCallbackHandler],
        )
    elif inference == "replicate":
        if model_id is None:
            model_id = "meta/meta-llama-3-70b-instruct"
        default_params = {
            "temperature": 0,
            "max_length": 1024,
            "max_new_tokens": 4096,
            "top_p": 1
        }
        if params:
            default_params.update(params)
        os.environ["REPLICATE_API_TOKEN"] = config["REPLICATE_API_TOKEN"]
        return ReplicateChatModel(model_id=model_id, params=default_params, callbacks=[loggingCallbackHandler])
    else:
        raise ValueError(
            f"Inference type {inference} is wrong, supported values are [ollama, watsonx]"
        )
