import inspect
import os
import re
import subprocess
import sys
import tempfile
import traceback
from io import StringIO
from typing import List, Optional, TypedDict

import gradio as gr
from langgraph.graph import END, StateGraph


DPK_AVAILABLE = False
TRANSFORM_LAUNCHER_PATH = None
PACKAGE_SRC_DIR = None

try:
    print("--- DPK Discovery (Subprocess Execution) ---")
    script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

    launcher_path = os.path.abspath(
        os.path.join(
            script_dir,
            "..",
            "..",
            "data-processing-lib",
            "python",
            "src",
            "data_processing",
            "runtime",
            "transform_launcher.py",
        )
    )

    package_src_dir = os.path.abspath(os.path.join(launcher_path, "..", "..", ".."))

    print(f"Targeting launcher script: {launcher_path}")
    print(f"Using package source for PYTHONPATH: {package_src_dir}")

    if os.path.isfile(launcher_path) and os.path.isdir(package_src_dir):
        TRANSFORM_LAUNCHER_PATH = launcher_path
        PACKAGE_SRC_DIR = package_src_dir
        DPK_AVAILABLE = True
        print("SUCCESS: DPK transform_launcher.py found and configured for subprocess execution.")
    else:
        print(f"FAILURE: The calculated launcher path or its source directory does not exist.")
        if not os.path.isfile(launcher_path):
            print(f"File not found: {launcher_path}")
        if not os.path.isdir(package_src_dir):
            print(f"Directory not found: {package_src_dir}")

except Exception as e:
    print(f"An unexpected error occurred during DPK discovery: {e}")

print("---------------------------------------------")


# langgraph
class GraphState(TypedDict):
    next_node: Optional[str]
    prompt: Optional[str]
    edit_instructions: Optional[str]
    pipeline_yaml: Optional[str]
    run_output: Optional[str]
    error: Optional[str]


def _run_dpk_as_subprocess(args: List[str]) -> subprocess.CompletedProcess:
    if not DPK_AVAILABLE:
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="DPK is not available.")

    if args[0] == "plan":
        prompt = args[2]
        # Use a regular expression to find a filename in quotes
        match = re.search(r"['\"]([^'\"]+)['\"]", prompt)

        if match:
            filename = match.group(1)
            yaml_output = f"""# Pipeline generated to read the specified file.
transforms:
  - name: read_and_print_file
    params:
      file_path: "{filename}"
"""
        else:
            yaml_output = f"""# Could not determine a filename from your prompt.
# Please specify a filename in quotes, e.g., "Read 'file.txt'".
# Using a default placeholder.
transforms:
  - name: echo
    params:
      message_to_print: "Executing task for: {prompt}"
"""
        return subprocess.CompletedProcess(args, 0, stdout=yaml_output, stderr="")
    elif args[0] == "judge":
        with open(args[2], "r") as f:
            existing_yaml = f.read()
        instructions = args[4]

        edited_yaml = None
        new_file_match = re.search(r"to\s+(['\"]?)([\w\.-]+)\1", instructions)

        if new_file_match:
            new_filename = new_file_match.group(2)
            (updated_yaml, num_replacements) = re.subn(
                r"(file_path:\s*['\"]).*?(['\"])", rf"\g<1>{new_filename}\g<2>", existing_yaml
            )
            if num_replacements > 0:
                edited_yaml = updated_yaml

        if edited_yaml is None:
            edited_yaml = existing_yaml + f"\n# Edit instruction applied: {instructions}\n"

        return subprocess.CompletedProcess(args, 0, stdout=edited_yaml, stderr="")
    elif args[0] == "run":
        config_path = args[2]

        command_str = f'"{sys.executable}" "{TRANSFORM_LAUNCHER_PATH}" "{config_path}"'
        print(f"Executing command via shell: {command_str}")

        env = os.environ.copy()

        current_pythonpath = env.get("PYTHONPATH", "")
        new_pythonpath = f"{PACKAGE_SRC_DIR}{os.pathsep}{current_pythonpath}"
        env["PYTHONPATH"] = new_pythonpath
        print(f"Using PYTHONPATH: {new_pythonpath}")

        try:
            result = subprocess.run(command_str, shell=True, capture_output=True, text=True, check=False, env=env)
            # diagnostics
            print("--- Subprocess Result ---")
            print(f"Return Code: {result.returncode}")
            print(f"STDOUT (first 100 chars): {result.stdout[:100]}")
            print(f"STDERR (first 100 chars): {result.stderr[:100]}")
            print("--- End Subprocess Result ---")
            return result
        except Exception as e:
            error_msg = f"Subprocess execution itself failed: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return subprocess.CompletedProcess(args, 1, stdout="", stderr=error_msg)
    else:
        raise ValueError(f"Unknown command for _run_dpk_as_subprocess: {args[0]}")


def _call_dpk_plan(prompt: str) -> dict:
    if not DPK_AVAILABLE:
        return {"pipeline_yaml": f"# [DEMO] Generating pipeline for: {prompt}\n"}
    try:
        result = _run_dpk_as_subprocess(["plan", "--prompt", prompt])
        return {"pipeline_yaml": result.stdout}
    except Exception as e:
        return {"error": f"# Unexpected error in DPK plan simulation: {e}\n{traceback.format_exc()}"}


def _call_dpk_judge(existing_yaml: str, instructions: str) -> dict:
    if not DPK_AVAILABLE:
        return {"pipeline_yaml": existing_yaml.rstrip() + f"\n# [DEMO edit] {instructions.strip()}\n"}

    path = ""
    try:
        with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False) as f:
            f.write(existing_yaml)
            path = f.name
        result = _run_dpk_as_subprocess(["judge", "--config", path, "--prompt", instructions])
        return {"pipeline_yaml": result.stdout}
    except Exception as e:
        return {"error": f"# Unexpected error in DPK judge simulation: {e}\n{traceback.format_exc()}"}
    finally:
        if os.path.exists(path):
            os.remove(path)


def _call_dpk_run(pipeline_yaml: str) -> dict:
    if not DPK_AVAILABLE:
        return {"run_output": "[DEMO] Would run pipeline:\n" + pipeline_yaml}

    path = ""
    try:
        with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False) as f:
            f.write(pipeline_yaml)
            path = f.name
        proc = _run_dpk_as_subprocess(["run", "--config", path])
        # this formats the graph as a subprocess
        output = f"--- STDOUT ---\n{proc.stdout}\n\n--- STDERR ---\n{proc.stderr}"
        return {"run_output": output}
    except Exception as e:
        return {"error": f"# Error running pipeline: {e}\n{traceback.format_exc()}"}
    finally:
        if os.path.exists(path):
            os.remove(path)


#  LangGraph Nodes
def generate_node(state: GraphState) -> dict:
    return _call_dpk_plan(state.get("prompt", ""))


def edit_node(state: GraphState) -> dict:
    return _call_dpk_judge(state.get("pipeline_yaml", ""), state.get("edit_instructions", ""))


def run_node(state: GraphState) -> dict:
    return _call_dpk_run(state.get("pipeline_yaml", ""))


def router(state: GraphState) -> str:
    return state.get("next_node", "")


# graph definitions
workflow = StateGraph(GraphState)
workflow.add_node("entry", lambda state: {**state})
workflow.set_entry_point("entry")
workflow.add_node("generate", generate_node)
workflow.add_node("edit", edit_node)
workflow.add_node("run", run_node)
workflow.add_conditional_edges("entry", router, {"generate": "generate", "edit": "edit", "run": "run", "": END})
workflow.add_edge("generate", END)
workflow.add_edge("edit", END)
workflow.add_edge("run", END)
app = workflow.compile()


# gradio interface
def handle_generate(prompt: str) -> str:
    if not prompt.strip():
        return "# Please enter a pipeline description."
    result = app.invoke({"next_node": "generate", "prompt": prompt})
    return result.get("pipeline_yaml") or result.get("error", "An unknown error occurred.")


def handle_edit(existing_yaml: str, instructions: str) -> str:
    if not existing_yaml.strip() or not instructions.strip():
        return existing_yaml
    result = app.invoke({"next_node": "edit", "pipeline_yaml": existing_yaml, "edit_instructions": instructions})
    return result.get("pipeline_yaml") or result.get("error", "An unknown error occurred.")


def handle_run(pipeline_yaml: str) -> str:
    if not pipeline_yaml.strip():
        return "# No pipeline to run."
    result = app.invoke({"next_node": "run", "pipeline_yaml": pipeline_yaml})
    return result.get("run_output") or result.get("error", "An unknown error occurred.")


# gradio ui
with gr.Blocks(title="DPK Planning Agent GUI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# DPK Planning Agent GUI")
    if not DPK_AVAILABLE:
        gr.Warning("DPK library not found or failed to import. Running in demo mode.")
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 1. Generate Pipeline")
            prompt_in = gr.Textbox(
                label="Pipeline Description", placeholder="e.g. Read 'input.csv', filter rows...", lines=3
            )
            gen_btn = gr.Button("Generate YAML", variant="primary")
            gr.Examples(
                [
                    "Read a CSV from 'input.csv' and print the first 5 rows.",
                    "Read two CSVs and merge them on the 'id' column.",
                ],
                inputs=prompt_in,
                label="Example Prompts",
            )
        with gr.Column(scale=3):
            yaml_box_1 = gr.Code(label="1. Generated Pipeline (Raw Output)", language="yaml", interactive=False)
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 2. Edit Pipeline (Optional)")
            edit_in = gr.Textbox(
                label="Edit Instructions", placeholder="e.g. Change the output file to 'output.csv'", lines=3
            )
            edit_btn = gr.Button("Apply Edit", variant="primary")
        with gr.Column(scale=3):
            # the main box for running the pipeline
            yaml_box_2 = gr.Code(
                label="2. Final Pipeline YAML (Edit Here Before Running)", language="yaml", interactive=True
            )
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 3. Run Pipeline")
            run_btn = gr.Button("Run Final Pipeline", variant="stop")
            # This output is connected to the 'Run Final Pipeline' button.
            run_out = gr.Code(label="Pipeline Console Output", language="shell", interactive=False)

    # event handlers
    gen_btn.click(fn=handle_generate, inputs=prompt_in, outputs=yaml_box_1)
    gen_btn.click(fn=lambda x: x, inputs=yaml_box_1, outputs=yaml_box_2)
    edit_btn.click(fn=handle_edit, inputs=[yaml_box_1, edit_in], outputs=yaml_box_2)
    run_btn.click(fn=handle_run, inputs=yaml_box_2, outputs=run_out)
    gr.ClearButton([prompt_in, yaml_box_1, edit_in, yaml_box_2, run_out], value="Clear All Fields")

if __name__ == "__main__":
    demo.launch()
