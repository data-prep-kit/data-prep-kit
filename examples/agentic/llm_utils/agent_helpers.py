from pathlib import Path
import requests
import json
from typing import List, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from .visualize_plan import visualize_plan


# Define the state
class State(TypedDict):
    plan: List[str]
    task: str
    context: str
    planning_attempts: int  # track planning iterations
    feedback: str
    need_judge: bool
    needs_revision: bool

# step_template_dict = {"step_name": "Step #", "tool_name": "tool_name", "tool_input": [{"param_name": "param_value"}], "step_ev":"Ev1"}
step_template_dict = {"step_name": "Step #", "tool_name": "tool_name", "tool_input": [{"param_name": "param_value"}], "import": "import line of the tool", "step_ev":"Ev1"}
step_template = json.dumps(step_template_dict)

# url = "https://raw.githubusercontent.com/roytman/test_repo/refs/heads/main/instructlab.md"
# response = requests.get(url)
# md_content = response.text


# Define the planner node
def planner(state: State, llm, prompt: str, tools: str, example: str, context: str) -> State:
    planner_prompt = ChatPromptTemplate.from_template(prompt)
    planner_chain = planner_prompt | llm
    output = planner_chain.invoke({
        "task": state["task"],
        "tool_not_implemented": "tool_not_implemented",
        "tools": tools,
        "example_task": example,
        "context": context,
        "previous_plan": '\n'.join(state['plan']),
        "feedback": state['feedback']
    })
    output.content = "".join(output.content)
    state['plan'] = output.content.split('\n')
    state['current_step'] = 0
    print(f"\033[36m\033[1m\nPlanner: suggested plan is:\033[0m")
    print(output.content)
    visualize_plan(output.content)
    return state


# Define the edge conditions
def is_plan_complete(state: State) -> bool:
    return state['current_step'] >= len(state['plan'])

def generate_run_file(llm, plan, prompt, output_file) -> State:
    generate_chain = ChatPromptTemplate.from_template(prompt) | llm
    evaluation = generate_chain.invoke({
        "step_template": step_template,
        "plan": plan
    })
    # Split the evaluation into feedback and decision
    evaluation.content = "".join(evaluation.content)
    eval_parts = evaluation.content.split('\n')
    code = extract_python_code(eval_parts)
    # format the content
    import black
    formatted_code = black.format_str(code, mode=black.FileMode())
    save_python_file(formatted_code, output_file)

def judge(state: State, llm, prompt: str, tools: str, context: str) -> State:
    # Get judge's evaluation
    judge_chain = ChatPromptTemplate.from_template(prompt) | llm
    evaluation = judge_chain.invoke({
        "task": state['task'],
        "plan": '\n'.join(state['plan']),
        "context": context,
        "tools": tools,
    })
    # Split the evaluation into feedback and decision
    evaluation.content = "".join(evaluation.content)
    eval_parts = evaluation.content.split('\n')
    decision_line = next((line for line in eval_parts if 'NEEDS_REVISION:' in line), '')
    needs_revision = 'yes' in decision_line.lower()

    eval_parts = evaluation.content.splitlines()
    decision_line = ""
    filtered_lines = []
    for line in eval_parts:
        if 'NEEDS_REVISION:' in line:
            decision_line = line
        else:
            filtered_lines.append(line)
    
    # Store results in state
    print(f"\033[36m\033[1m\nJudge: review:\033[0m")
    print(evaluation.content)
    state['feedback'] = '\n'.join(filtered_lines)
    state['needs_revision'] = needs_revision
    state['planning_attempts'] = state['planning_attempts'] + 1
    return state

def is_plan_OK(state: State) -> bool:
    if state["planning_attempts"] >= 3:
        return True
    return not state['needs_revision']

def need_judge(state: State) -> bool:
    return state["need_judge"]

def is_user_review_OK(state: State) -> bool:
    if state["feedback"] in ["", "OK", "okay"]:
        print("The planning is done")
        return True
    return False

def user_review(state: State) -> bool:
    state['planning_attempts'] = 0
    return state

# User review function
def get_user_review(state: State) -> State:
    new_state = state.copy()
    feedback = input("\nPlease review the plan and provide feedback (or print 'okay', 'OK' or just Enter to continue): ")
    new_state['feedback'] = feedback
    new_state['planning_attempts'] = 0
    new_state['need_judge'] = False
    
    return new_state

def get_steps(plan):
    json_steps = []
    for json_str in plan:
        if json_str.strip():  # Skip empty lines
          try:
            json_obj = json.loads(json_str)
            json_steps.append(json_obj)
          except json.JSONDecodeError as e:
            print(f"Skip line")
    return json_steps

# Define the generator node (simplified for this example)
def generator(state: State, llm, prompt: str, file_name: str="llm_plan_generated.py") -> State:
    steps = get_steps(state["plan"])
    llm_output = generate_run_file(llm, steps, prompt, file_name)
    return state

def extract_python_code(llm_output: list) -> str:
    code = []
    in_code_block = False
    
    for line in llm_output:
        if line.strip() == '```python':
            in_code_block = True
            continue
        elif line.strip() == '```':
            in_code_block = False
            continue
            
        if in_code_block:
            code.append(line)
            
    return '\n'.join(code)

def save_python_file(code: str, filename: str):
    try:
        with open(filename, 'w') as f:
            f.write(code)
        print(f"Successfully saved code to {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")

def code_validator_noop(state: State) -> State:
    return state
