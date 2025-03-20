import json
from IPython.display import display, Markdown

def parse_plan_string(plan_string):
    """
    Parses a string where each line is a JSON dictionary.
    
    Args:
        plan_string (str): String containing one JSON dictionary per line
    
    Returns:
        list: List of parsed dictionaries
    """
    # Split into lines and filter out empty lines
    lines = [line.strip() for line in plan_string.split('\n') if line.strip()]
    #print(f"{lines}")
    # Parse each line as JSON
    plan_steps = []
    for line in lines:
        try:
            step = json.loads(line)
            plan_steps.append(step)
        except json.JSONDecodeError as e:
            # print(f"Error parsing line: {line}")
            # print(f"Error: {e}")
            continue
    return plan_steps


def extract_plan(msg_content):
    """
    Extracts JSON dictionaries from numbered lines like:
    1. {"name": "tool1", ...}
    2. {"name": "tool2", ...}
    """
    plan_lines = []
    
    for line in msg_content.split('\n'):
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
            
        # Remove numbering prefix if it exists (e.g., "1. ", "2. ", etc.)
        if line[0].isdigit():
            # Find the position after the number and dot
            pos = line.find('. ')
            if pos != -1:
                line = line[pos + 2:]
        
        # Check if the line is a JSON dictionary
        try:
            if line.startswith('{') and line.endswith('}'):
                step = json.loads(line)
                if " #1" in step["step_name"]:
                    plan_lines = [step]
                else:
                    plan_lines.append(step)
        except json.JSONDecodeError as e:
            # print(f"Error parsing line: {line}")
            continue
    return plan_lines

def visualize_plan(plan_input):
    """
    Creates a diagram visualization of a plan.
    
    Args:
        plan_input (str or list): Either a string with JSON dictionaries per line,
                                 or a list of dictionaries
    """
    # Parse the plan if it's a string
    if isinstance(plan_input, str):
        plan_steps = extract_plan(plan_input)
    else:
        plan_steps = plan_input

    graph_str = ["graph LR;"]
    
    # Add nodes and edges
    for i, step in enumerate(plan_steps):
        # Create node with step name and tool name
        node_id = f"step{i}"
        label = f"{step['tool_name']}"
        
        # Create node with proper escaping for quotes
        graph_str.append(f'    {node_id}["{label}"]')
        
        # Add edge to next step if not the last step
        if i < len(plan_steps) - 1:
            next_node = f"step{i+1}"
            graph_str.append(f'    {node_id} --> {next_node}')
    
    # Join all lines with newlines
    diagram = "\n".join(graph_str)
    
    # Display the diagram in the notebook
    display(Markdown(f"```mermaid\n{diagram}\n```"))
