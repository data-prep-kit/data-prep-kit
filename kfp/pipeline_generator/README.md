## Steps to generate a new pipeline

- create a `descriptor.yaml` file for the required task, see for example, the [demo pipeline descriptor](example-pipeline.yaml)).

- create a venv with the necessary tooling for the workflow generator, and activate i: 
    `make -C ../../transforms workflow-venv` and `source ../../transforms/venv/bin/activate`

- run the workflow generator:
    `python make_dpk_wf.py --workflow demo_wf.py --path ../../transforms example-pipeline.yaml`
