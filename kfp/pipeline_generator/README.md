## Description 

`make_dpk_wf.py` generates a Kubeflow pipeline that sequentially runs a series of transforms, using the Ray operator, handig over the output of one transform to the input of the next. 
The pipeline is described minimally in a YAML file that is the only input to the generator. 
The tool queries the transfom modules for the list of valid parameters and their default values. 
These values can be explicitly overridden in the pipeline descriptor if needed.

The pipeline decriptor YAML consists of a global section with settings that apply to the entire workflow and the list of transforms that are part of that workflow. 
An optional section with setting common to all the transforms helps in keeping the descriptor concise.

## Fields in the global section
The following fields are valid in the global section:

- `data_checkpointing: bool`
     Whether to use data checkpointing, the default is `False`.
- `data_max_files: int`
     The number of files to process, use `-1` to process all (default).
- `data_num_samples: int`
     The number of samples to process, `-1` to process all (default).
- `description`
     Description for this workflow. There is no default.
- `dsl_pipeline_name`
     The DSL function name, defaults to the workflow name.
- `image_pull_secret`
     The secret for getting the DPK/KFP image by default set to `"image-pull-secret"`.
- `input_folder`
     The location of the input data, by default set to `"input"`.
- `kfp_base_image`
     The DPK/KFP image name. The default is `quay.io/dataprep1/data-prep-kit/kfp-data-processing:latest`.
- `name`
     Name for this workflow. Used by Kubeflow to generate name for other Kubernets object, so it recommended to be kept short. If not set it will default to the descriptor filename.
- `output_folder`
     Location to store the output of the last tranform in the chain, by default set to `"output"`.
- `s3_access_secret`
     The name of the s3 access secret. The same secret is used for the input, output and temporary storage. By default set to the string `"s3-access"`.
- server_url:
     KubeRay server URL, the default is `http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888`
- `tmp_folder`
     Location temporary to store intermediate transform outputs. Defaults to the string `"output/tmp"`.
  
- `transform_common_parameters`
     Settings that apply to all transforms in the workflow, see below. 
- `transforms`
     The list of transforms in execution order. See below for valid fields.

## Fields in the transforms section
The following fields are valid in each transform the section. The fields marked with <sup>**C**</sup> are also valid in the common transform section. 

Note that the transform settings are used to *update* the common settings when present. e.g. if the common section has `ray_worker_options: {cpu:1, memory:4}` and the transform has  `ray_worker_options: {cpu:2, gpu:1}`, the final `ray_worker_options` setting for the transform will be `{cpu:2, gpu: 1, memory:4}`

- `transform`
     The transform name. The tool will try to load a **dpk_*transform*.transfom** or **dpk_*transform*.info** module to query for arguments and description.
- `name`
     Name to identify this step in workflow, must be unique. By default the transform name is used for this purpose, but it is required when the same transform is used more than once in the workflow.

- `description`
     Description for this step in the workflow. The transfom's description is used by default.

- `image`<sup>**C**</sup>
     The name of the image for this transform. There is no default and this field is required.

- `image_pull_secret`<sup>**C**</sup>
     Kubernetes secret for the image repository
  
- `image_tag`
     A tag to be used in the image name when the image is set in the common section.

- `ray_head_options: dict`<sup>**C**</sup>
     Ray head options.

- `ray_name`
     Name to use for the Ray cluster, the name of the transform is used by default.
  
- `ray_worker_options: dict`<sup>**C**</sup>
     Ray worker options.
  
- `runtime_actor_options: dict`<sup>**C**</sup>
     Runtime actor options.
  
- `runtime_code_location: dict`<sup>**C**</sup>
     Git repository information.
  
- `invocation`<sup>**C**</sup>
     Python arguments for invoking the transform.

- `additional_params: dict`<sup>**C**</sup>
     Additional paramters for the Ray control commands.

- `env: dict`<sup>**C**</sup>
     Envronment variables. Either in the form `VAR_NAME: VALUE` or as a three field dictionary:
  ```yaml
  VARNAME:
      source: SOURCE # One of SECRET, CONFIGMAP, RESOURCE_FIELD, or FIELD. 
      name: name
      key: key
  ```
- `volumes: list[dict]`<sup>**C**</sup>
     Volumes to mount in the Ray worker pods. The default type is PVC. 
  ```yaml
  volumes:
    - source: cos-pile # Name of the PVC
      mount_path: /models
      read_only: true
      type: pvc
  ```

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
