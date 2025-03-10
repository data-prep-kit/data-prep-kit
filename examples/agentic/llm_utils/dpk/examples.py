example_task = '''
For example, If the required task was Filter the parquet files to include only english documents. The the plan should be the following:
{"step_name": "Step #1 language identification", "tool_name": "language_id", "tool_input": [{"in_folder": "user_input", "out_folder": "user_input"}], "step_ev": "Ev1"}
{"step_name": "Step #2 filter english documents", "tool_name": "filter_transform", "tool_input": [{"in_folder": "#Ev1"}, {"out_folder": "user_input"}, {"filter_criteria_list": [lang==en]}], "step_ev": "Ev2"}
'''


example_task1 = '''
For example, If the required task was Filter the parquet files to include only english documents. The the plan should be the following:
{"step_name": "Step #1 language identification", "tool_name": "language_id", "tool_input": [{"in_folder": "user_input", "out_folder": "user_input"}], "import": "from llm_utils.dpk.langchain_tools.tools.language.lang_id import LangIdentificationTransform", "step_ev": "Ev1"}
{"step_name": "Step #2 filter english documents", "tool_name": "filter_transform", "tool_input": [{"in_folder": "#Ev1", "out_folder": "#Ev1", "filter_criteria_list": "[lang==en]"}], import: "from llm_utils.dpk.langchain_tools.tools.universal.filter import FilterTransform", "step_ev": "Ev2"}
'''


example_task2 = '''
For example, If the required task was Filter the parquet files to include only english documents. The the plan should be the following:
{"step_name": "Step #1 language identification", "tool_name": "language_id", "tool_input": [{"in_folder": "user_input", "out_folder": "user_input+'_langid'"}], "import": "from llm_utils.dpk.langchain_tools.tools.language.lang_id import LangIdentificationTransform", "step_ev": "Ev1"}
{"step_name": "Step #2 filter english documents", "tool_name": "filter_transform", "tool_input": [{"in_folder": "#Ev1", "out_folder": "#Ev1+'_filter'", "filter_criteria_list": "[lang==en]"}], import: "from llm_utils.dpk.langchain_tools.tools.universal.filter import FilterTransform", "step_ev": "Ev2"}
'''
