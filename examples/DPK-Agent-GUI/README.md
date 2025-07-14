# DPK Planning Agent GUI

This is a [Gradio](https://www.gradio.app/)-based web interface to generate, edit, and run data pipelines using the Data Prep Kit (DPK) transform launcher via LangGraph `StateGraph`. It falls back to a demo mode when the DPK library is unavailable.
## Features

* **Pipeline Generation:** Generate YAML pipelines from natural language prompts.
* **Pipeline Editing:** Apply edit instructions to existing pipeline YAML.
* **Pipeline Execution:** Run pipelines via the DPK launcher and display console output.
* **Demo Mode:** If the DPK launcher script is not found, the app simulates pipeline generation and execution.

## Prerequisites

* **Operating System:** macOS, Linux, or Windows
* **Python:** 3.10 or newer
* **Git:** Required to clone this repository and the DPK repository

## Installation

Clone both this GUI repository and the Data Prep Kit repository:

```bash
# 1. Clone the GUI
git clone https://github.com/<username>/dpk-planning-agent-gui.git
cd dpk-planning-agent-gui

# 2. Clone the Data Prep Kit (DPK) as a sibling directory
cd ..
git clone https://github.com/data-prep-kit/data-prep-kit.git
cd dpk-planning-agent-gui
```

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

pip install --upgrade pip
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

**Note:** You can install the Data Prep Kit via PyPI (when available), by running:

```bash
pip install data-prep-toolkit-transforms[language]
```

## Repository Structure

```
 project-root/
 ├── dpk-planning-agent-gui/
 │   ├── dpk_planning_agent_gui.py       # Main application script
 │   ├── requirements.txt                # Python dependencies
 │   └── README.md                       # This file
 └── data-prep-kit/                      # Cloned Data Prep Kit repository
    └── python/src/data_processing/
        └── runtime/transform_launcher.py
```

## Usage

1. Ensure the virtual environment is active:

```bash
source venv/bin/activate
```

2. Run the application:

```bash
python dpk_planning_agent_gui.py
```

3. Open your browser at the URL printed in the console (e.g., `http://localhost:7860`).
4. Use the three-step interface:
   1. **Generate Pipeline:** Enter a natural-language prompt to create a pipeline YAML.
   2. **Edit Pipeline :** Apply modifications to the generated YAML.
   3. **Run Pipeline:** Executes the final YAML and view standard output/error.

## Configuration & Environment Variables

* **DPK Discovery:** The script detects `transform_launcher.py` at `../data-prep-kit/python/src/data_processing/runtime/transform_launcher.py`. If your DPK is in a different path, set the `TRANSFORM_LAUNCHER_PATH` environment variable:

```bash
export TRANSFORM_LAUNCHER_PATH="/path/to/transform_launcher.py"
```

* **PYTHONPATH:** The app injects the DPK `PACKAGE_SRC_DIR` into `PYTHONPATH` for subprocess calls. No manual editing required.

## Development

* **Branching:** Create feature branches off `main` for new work.
* **Testing:** Add unit tests for `_run_dpk_as_subprocess`, `handle_generate`, `handle_edit`, and `handle_run`.

## Contributing

Contributions are welcome! Please open issues or pull requests in this repository.

**Note for Developers:** Update the `requirements.txt` file after installing new package by running:

```bash
pip freeze > requirements.txt
```