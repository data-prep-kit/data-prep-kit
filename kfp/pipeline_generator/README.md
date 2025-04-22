## Steps to generate a pipeline

- Create a `descriptor.yaml` file for the required task. See for example the demo pipeline
  descriptor [example-pipeline.yaml](example-pipeline.yaml).

- Create a Python virtual environment with the necessary tooling for the workflow generator, and activate it: 
    ```bash
    make -C ../../transforms workflow-venv
    source ../../transforms/venv/bin/activate
    ```

- Run the workflow generator:
  ```bash
  ./make_dpk_wf.py --workflow demo_wf.py --path ../../transforms example-pipeline.yaml
  ```
