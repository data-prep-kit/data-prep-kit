generate_prompt_str = """
Create a Python script that implements the following workflow plan. Each step in the plan follows this JSON structure:
{step_template}
Key requirements:

Assume all tools are available in a 'tools.py' file - just import them and don't put an implementation of the tools
Create a main function that accepts the variable parameters as command-line arguments using argparse
Create an execute_workflow function that implements the plan step by step
Each step should store its result in a results dictionary using the step_ev as key
Each subsequent step should be able to reference previous steps' results using the step_ev values
Include basic error handling and progress logging.
The script should be runnable from command line.
The python code shouldn't include the dictionaries of the plan's steps
parse the plan steps and for each step add its tool call.
If there are hardcoded values of the input parameters of the steps then add an appropriate input argument with the hardcoded value as a default values of the argument.

Here's the plan to implement:
{plan}
Please generate a complete, runnable Python script that implements this particular plan without including it, the file should got all the input parameters in the main as args.
Note: If a step uses a previous step's output, it will reference it using the step_ev value (e.g., #E1, #E2). Your implementation should resolve these references to their actual values during execution.

Here's a template for the script structure:

import argparse
import os
from tools import (
    #tools functions
)

def extract_output_folder(message):
    pattern = r"output_folder\s+(?:{)?(.*?)(?:}|\.|$)"
    match = re.search(pattern, message)
    if match:
        return match.group(1)
    return None

def execute_workflow(args):
    results["Ev1"] = transform1()._run(args.in_folder, args.out_folder+"_transform1Name", rest params)
    results["Ev2"] = transform2()._run(extract_output_folder(results["Ev1"]), extract_output_folder(results["Ev1"])+"_transform2Name", rest params)
    ...
    return results


def main():
    parser = argparse.ArgumentParser(description="Execute the workflow plan.")
    parser.add_argument(
        "--in_folder",
        type=str,
        required=True,
        help="Input folder for the workflow.",
    )
    parser.add_argument(
        "--out_folder",
        type=str,
        required=True,
        help="Output folder for the workflow.",
    )parser.add_argument(
        "--tool_param",
        type=type of the parameter,
        required=True,
        help="description of the argument",
    )
    # The rest of the arguments

    args = parser.parse_args()

    try:
        results = execute_workflow(args)
        print(results)
    except Exception as e:
        print(f"An error occurred")


if __name__ == "__main__":
    main()
"""


#  Each step in the plan follows this JSON structure:
# {step_template}
generate_prompt_str_with_example = """
Create a Python script that implements the following workflow plan.
Key requirements:

Create a main function that accepts the variable parameters as command-line arguments using argparse.
Create an execute_workflow function that implements the plan step by step.
Each step should store its result in a results dictionary using the step_ev as key.
Each subsequent step should be able to reference previous steps' results using the step_ev values.
The script should be runnable from command line.
The python code shouldn't include the dictionaries of the plan's steps.
Parse the plan steps and for each step add its tool call.
If there are hardcoded values of the input parameters of the steps then replace it with an appropriate input argument with the hardcoded value as a default values of the argument (for example filter_criteria_list=args.filter_criteria_list, data_files_to_use=args.data_files_to_use).
The function calls of "_run()" of the steps must not include hardcoded values in the parameters, just use args or outputs from previous steps.
Each parameter in the transform run call should be from an output of a previous transform or an argument of the script.
The script must include the import lines of the transform tools.
The script must use from parse_output function and import it "from helpers import parse_output".
The script must get the envirnoment variables and pass the data_type and data_s3_cred parameters to each step.

Here's the plan to implement:
====
{plan}
====
Please generate a complete, runnable Python script that implements this particular plan without including it, the file should got all the input parameters in the main as args.
Note: If a step uses a previous step's output, it will reference it using the step_ev value (e.g., #E1, #E2). Your implementation should resolve these references to their actual values during execution.
====

Here's an example:
====
For the following plan
{{"step_name": "Step #1 language identification", "tool_name": "language_id", "tool_input": [{{"in_folder": "user_input", "out_folder": "user_input"}}], "import": "from llm_utils.dpk.langchain_tools.tools.language.lang_id import LangIdentificationTransform", "step_ev": "Ev1"}}
{{"step_name": "Step #2 filter english documents", "tool_name": "filter_transform", "tool_input": [{{"in_folder": "#Ev1", "out_folder": "#Ev1", "filter_criteria_list": "[lang==en]"}}], "import": "from llm_utils.dpk.langchain_tools.tools.universal.filter import FilterTransform", "step_ev": "Ev2"}}
{{"step_name": "Step #3 tokenization", "tool_name": "tokenization", "tool_input": [{{"in_folder": "#Ev2", "out_folder": "#Ev2"}}], "import": "from llm_utils.dpk.langchain_tools.tools.universal.tokenization import TokenizationTransform"}}

the code should be:
```python
import argparse
import os
from helpers import parse_output
from llm_utils.dpk.langchain_tools.tools.universal.filter import FilterTransform
from llm_utils.dpk.langchain_tools.tools.language.lang_id import LangIdentificationTransform
from llm_utils.dpk.langchain_tools.tools.universal.tokenization import TokenizationTransform

def execute_workflow(args):
    results = 
    res = LangIdentificationTransform()._run(
        data_type=args.data_type,
        data_s3_cred={{"access_key": args.access_key, "secret_key": args.secret_key, "url": args.url}},
        input_folder=args.in_folder,
        output_folder=args.out_folder+"_langid"
    )
    results["Ev1"] = parse_output(res)
    res = FilterTransform()._run(
        data_type=args.data_type,
        data_s3_cred={{"access_key": args.access_key, "secret_key": args.secret_key, "url": args.url}},
        input_folder=results["Ev1"],
        output_folder=results["Ev1"]+"_filter",
        filter_criteria_list=args.filter_criteria_list
    )
    results["Ev2"] = parse_output(res)
    res = TokenizationTransform()._run(
        data_type=args.data_type,
        data_s3_cred={{"access_key": args.access_key, "secret_key": args.secret_key, "url": args.url}},
        input_folder=results["Ev2"],
        output_folder=results["Ev2"]+"_token"
    )
    results["Ev3"] = parse_output(res)
    return results


def main():
    parser = argparse.ArgumentParser(description="Execute the workflow plan.")
    parser.add_argument(
        "--in_folder",
        type=str,
        required=True,
        help="Input folder for the workflow.",
    )
    parser.add_argument(
        "--out_folder",
        type=str,
        required=True,
        help="Output folder for the workflow.",
    )
    parser.add_argument(
        "--filter_criteria_list",
        type=str,
        required=True,
        default="[lang==en]",
        help="Filter query for the workflow.",
    )

    args = parser.parse_args()
    args.data_type = "s3"
    args.access_key = os.environ.get('ACCESS_KEY')
    args.secret_key = os.environ.get('SECRET_KEY')
    args.url = os.environ.get('MINIO_URL')

    try:
        results = execute_workflow(args)
        print(results)
    except Exception as e:
        print(f"An error occurred:")


if __name__ == "__main__":
    main()
```
====

"""
