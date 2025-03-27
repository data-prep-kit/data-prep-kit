This directory contains implementation of DPK transforms as [langchain](https://python.langchain.com/v0.1/docs/modules/tools/) or [llama-index](https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/tools/) tools.

* **[`langchain_tools`](./langchain_tools):** directory contains code to define DPK transforms as langchain tools similar to the tools defined in [here](https://github.com/langchain-ai/langchain/tree/master/libs/community/langchain_community/tools).
* **[`llama_index_tools`](./llama_index_tools):** directory contains code to define DPK transforms as llama-index tools similar to the tools defined in [here](https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/tools).
* **[`dpk_common.py`](./dpk_common.py):** contains definitions used in both of the implementations defined above. 

For example usage please look at [`dpk_as_tools.ipynb`](../../dpk_as_tools.ipynb) notebook.


In addition, this directory contains files that define the context for the [`DPK agent`](../../Planning_DPK_agent.ipynb):

* **[`tools.py`](./tools.py):** Json dictionaries that describe the tools to pass it to the agent. Each dictionary describes a DPK transform.
* **[`examples.py`](./examples.py):** Examples of tasks and their matched plan. Used in the planner prompt to get more accurate results.
* **[`constraints.py`](./constraints.py):** Constrains that the generated plan or pipeline should satisfy.