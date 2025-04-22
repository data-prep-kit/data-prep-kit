#!/usr/bin/env python

# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
import os, json, yaml
from typing import NamedTuple

import kfp.compiler
import kfp.components
import kfp.dsl 

from workflow_support.compile_utils import (
    DEFAULT_KFP_COMPONENT_SPEC_PATH,
    ONE_HOUR_SEC,
    ONE_WEEK_SEC,
    ComponentUtils,
)
#
# KFP pipeline with {% for tr in transforms %}{{tr.name}}{% if not loop.last %}, {% endif %}{%- endfor %}
#
KFP_NAME = "{{name}}"
KFP_DESCRIPTION = "{{description}}"
KFP_IMAGE = "{{kfp_base_image}}"
KFP_IMAGE_PULL_SECRET = "{{image_pull_secret}}"

# Data locations
INPUT_FOLDER = "{{input_folder}}"
OUTPUT_FOLDER = "{{output_folder}}"
TMP_FOLDER = "{{tmp_folder}}"

# The secret name for all S3 locations: input, output and temp
S3_SECRET = "{{s3_access_secret}}"

# Input limits 
DATA_MAX_FILES = {{data_max_files}}
DATA_NUM_SAMPLES = {{data_num_samples}}
DATA_CHECKPOINTING = {{data_checkpointing}}

COMPONENT_SPEC_PATH = os.getenv("KFP_COMPONENT_SPEC_PATH", DEFAULT_KFP_COMPONENT_SPEC_PATH)
if not os.path.isfile(os.path.join(COMPONENT_SPEC_PATH, "createRayClusterComponent.yaml")):
    import workflow_support.compile_utils
    base_dir = workflow_support.compile_utils.__file__.split("/")
    while base_dir and base_dir[-1] != "kfp":
        base_dir = base_dir[:-1]
    for root, dirs, files in os.walk("/".join(base_dir)):
        if "createRayClusterComponent.yaml" in files:
            COMPONENT_SPEC_PATH = root
            break

# Compute execution parameters for all transforms
def compute_exec_params_func(
    input_folder: str,
    output_folder: str,
    tmp_folder: str,

    data_max_files: int,
    data_num_samples: int,
    data_checkpointing: bool,

    runtime_pipeline_id: str,

    {% for tr in transforms %}
    # args for {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %}
    {{tr.name}}_runtime_job_id: str,
    {%- for arg in tr.args %}
    {% if tr.name == tr.transform %}{{arg.name}}: {{arg.type}},{% else %}{{tr.name}}_{{arg.name}}: {{arg.type}},{% endif %}
    {%- endfor %}
    {%- for arg in tr.kfp_args %}
    {{tr.name}}_{{arg.name}}: {{arg.type}},
    {%- endfor %}
    {% endfor %}
    ) -> NamedTuple('Outputs', [{% for tr in transforms %}('{{tr.name}}', dict){%- if not loop.last %},{%- endif %}{% endfor %}]):
    from runtime_utils import KFPUtils
    import os

    if not tmp_folder: 
        tmp_folder = os.path.join(output_folder, "tmp")

    {%- for tr in transforms %}
    {%- if not loop.last %}
    tmp_out = os.path.join(tmp_folder, "{{tr.name}}")
    {{tr.name}}_data_s3_config = dict(input_folder=input_folder, output_folder=tmp_out)
    input_folder = tmp_out
    {%- endif %}

    {%- if loop.last %} 
    {{tr.name}}_data_s3_config = dict(input_folder=input_folder, output_folder=output_folder)
    {%- endif %}
    {%- endfor %}

    return (
        {%- for tr in transforms %}
        dict(
            data_s3_config= str({{tr.name}}_data_s3_config),
            {%- if loop.first %}
            data_max_files= data_max_files,
            data_num_samples= data_num_samples,
            {%- endif %}
            {%- if not loop.first %}
            data_max_files= -1,
            data_num_samples= -1,
            {%- endif %}
            data_checkpointing= data_checkpointing,
            runtime_num_workers= KFPUtils.default_compute_execution_params(str({{tr.name}}_ray_worker_options), str({{tr.name}}_runtime_actor_options)),
            runtime_worker_options= str({{tr.name}}_runtime_actor_options),
            runtime_pipeline_id= runtime_pipeline_id,
            runtime_code_location= str({{tr.name}}_runtime_code_location),
            runtime_job_id = {{tr.name}}_runtime_job_id,
            # parameters for {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %}
            {%- for arg in tr.args %}
            {{arg.name}}={% if tr.name == tr.transform %}{{arg.name}}{% else %}{{tr.name}}_{{arg.name}}{% endif %}
            {%- if not loop.last %},{%- endif %}
            {%- endfor %}
        ){%- if not loop.last %},{%- endif %}
        {%- endfor %}
    )

# KFPv1 and KFP2 uses different methods to create a component from a function. KFPv1 uses the
# `create_component_from_func` function, but it is deprecated by KFPv2 and so has a different import path.
# KFPv2 recommends using the `@kfp.dsl.component` decorator, which doesn't exist in KFPv1. Therefore, here we use
# this if/else statement and explicitly call the decorator.
if os.getenv("KFPv2", "0") == "1":
    compute_exec_params_op = kfp.dsl.component_decorator.component(
        func=compute_exec_params_func, base_image=KFP_IMAGE
    )
else:
    compute_exec_params_op = kfp.components.create_component_from_func(func=compute_exec_params_func, base_image=KFP_IMAGE)

def load_component(yaml_fn):
    with open(os.path.join(COMPONENT_SPEC_PATH, yaml_fn), 'r') as file:
        component_yaml = yaml.safe_load(file)
    component_yaml["implementation"]["container"]["image"] = KFP_IMAGE
    component_txt = yaml.dump(component_yaml, sort_keys=False)
    return kfp.components.load_component_from_text(component_txt)

# create Ray cluster
create_ray_op = load_component("createRayClusterComponent.yaml")
# execute job
execute_ray_jobs_op = load_component("executeRayJobComponent.yaml")
# clean up Ray
cleanup_ray_op = load_component("deleteRayClusterComponent.yaml")

# Task name is part of the pipeline name, the ray cluster name and the job name in DMF.
TASK_NAME: str = "{{ pipeline_name }}"

@kfp.dsl.pipeline(
        name = "{{name}}",
        description = "{{description}}",
)
def {{dsl_pipeline_name}}(
    input_folder: str = INPUT_FOLDER,
    output_folder: str = OUTPUT_FOLDER,
    tmp_folder: str = TMP_FOLDER,
    data_s3_access_secret: str = S3_SECRET,
    data_max_files: int = DATA_MAX_FILES,
    data_num_samples: int = DATA_NUM_SAMPLES,
    data_checkpointing: bool = DATA_CHECKPOINTING,
    runtime_pipeline_id: str = "pipeline_id",
    server_url: str = "{{server_url}}",
    {% for tr in transforms %}
    # args for {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %}
    {{tr.name}}_ray_run_id_KFPv2: str = "",
    {%- for arg in tr.kfp_args %}
    {{tr.name}}_{{arg.name}}: {{arg.type}} = {% if arg.type == "str" %}'{{arg.value}}'{% else %}{{arg.value}}{% endif %},
    {%- endfor %}
    {%- for arg in tr.args %}
    {% if tr.name == tr.transform %}{{arg.name}}{% else %}{{tr.name}}_{{arg.name}}{% endif %}: {{arg.type}} = {% if arg.type == "str" %}'{{arg.value}}'{% else %}{{arg.value}}{% endif %},
    {%- endfor %}
    {% endfor %}
):
    """
    {{name}} - {{description}}
    :param input_folder:
    :param output_folder:
    :param tmp_folder:
    :param data_s3_access_secret: s3 access secret
    :param data_max_files: maximum number of files to process
    :param data_num_samples: number of samples to process
    :param data_checkpointing: data checkpointing 
    :param runtime_pipeline_id: 
    :param server_url:
    {%- for tr in transforms %}
    {%- for arg in tr.args %}
    :param {% if tr.name == tr.transform %}{{arg.name}}{% else %}{{tr.name}}_{{arg.name}}{% endif %}: {{arg.description}}
    {%- endfor %}
    {%- for arg in tr.kfp_args %}
    :param {{tr.name}}_{{arg.name}}: {{arg.description}}
    {%- endfor %}
    {% endfor %}
    :return: None
    """
    # In KFPv2 dsl.RUN_ID_PLACEHOLDER is deprecated and cannot be used since SDK 2.5.0. On another hand we cannot create
    # a unique string in a component (at runtime) and pass it to the `clean_up_task` of `ExitHandler`, due to
    # https://github.com/kubeflow/pipelines/issues/10187. Therefore, meantime the user is requested to insert
    # a unique string created at run creation time.
    if os.getenv("KFPv2", "0") == "1":
        print("WARNING: the ray cluster name can be non-unique at runtime, please do not execute simultaneous Runs of the "
              "same version of the same pipeline !!!")
        {%- for tr in transforms %}
        {{tr.name}}_run_id = {{tr.name}}_ray_run_id_KFPv2
        {%- endfor %}
    else:
        {%- for tr in transforms %}
        {{tr.name}}_run_id = kfp.dsl.RUN_ID_PLACEHOLDER
        {%- endfor %}
    # create the final clean_up task
    {%- for tr in transforms %}
    {%- if loop.last %}
    {% if legacy %}
    {{tr.name}}_clean_up_task = cleanup_ray_op(ray_name={{tr.name}}_ray_name, run_id={{tr.name}}_run_id, server_url=server_url)
    {% else %}
    {{tr.name}}_clean_up_task = cleanup_ray_op(ray_name={{tr.name}}_ray_name, run_id={{tr.name}}_run_id, server_url=server_url, additional_params=str({{tr.name}}_additional_params))
    {% endif %}
    ComponentUtils.add_settings_to_component({{tr.name}}_clean_up_task, ONE_HOUR_SEC * 2)
    {{tr.name}}_clean_up_task.set_display_name("Stop {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %} Ray cluster")
    with kfp.dsl.ExitHandler({{tr.name}}_clean_up_task):
    {%- endif %}
    {%- endfor %}
        # compute execution params
        compute_exec_params_task = compute_exec_params_op(
            input_folder= input_folder,
            output_folder= output_folder,
            tmp_folder= tmp_folder,

            data_max_files= data_max_files,
            data_num_samples= data_num_samples,
            data_checkpointing= data_checkpointing,

            runtime_pipeline_id= runtime_pipeline_id,
            {% for tr in transforms %}
            # args for {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %}
            {{tr.name}}_runtime_job_id= {{tr.name}}_run_id,
            {%- for arg in tr.args %}
            {% if tr.name == tr.transform %}{{arg.name}}{% else %}{{tr.name}}_{{arg.name}}{% endif %}={% if tr.name == tr.transform %}{{arg.name}}{% else %}{{tr.name}}_{{arg.name}}{% endif %},
            {%- endfor %}
            {%- for arg in tr.kfp_args %}
            {{tr.name}}_{{arg.name}}= {{tr.name}}_{{arg.name}},
            {%- endfor %}
            {% endfor %}
        )
        ComponentUtils.add_settings_to_component(compute_exec_params_task, ONE_HOUR_SEC * 2)
        {%- for tr in transforms %}
        # start Ray cluster for {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %}
        {{tr.name}}_ray_cluster = create_ray_op(
            ray_name={{tr.name}}_ray_name,
            run_id={{tr.name}}_run_id,
            ray_head_options={{tr.name}}_ray_head_options,
            ray_worker_options={{tr.name}}_ray_worker_options,
            server_url=server_url,
            additional_params=str({{tr.name}}_additional_params),
        )
        {{tr.name}}_ray_cluster.set_display_name("Start {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %} Ray cluster")
        ComponentUtils.add_settings_to_component({{tr.name}}_ray_cluster, ONE_HOUR_SEC * 2)
        {%- if loop.first %}
        {{tr.name}}_ray_cluster.after(compute_exec_params_task)
        {%- else %}
        {{tr.name}}_ray_cluster.after(last_clean_task)
        {%- endif %}

        # execute {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %} job
        {{tr.name}}_execute_job = execute_ray_jobs_op(
            ray_name={{tr.name}}_ray_name,
            run_id={{tr.name}}_run_id,
            additional_params=str({{tr.name}}_additional_params),
            exec_params=compute_exec_params_task.outputs["{{tr.name}}"],
            exec_script_name="{{tr.script_name}}",
            server_url=server_url,
        )
        {{tr.name}}_execute_job.set_display_name("Run {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %}")
        ComponentUtils.add_settings_to_component({{tr.name}}_execute_job, ONE_WEEK_SEC)
        if os.getenv("KFPv2", "0") == "1":     
            from kfp import kubernetes
            
            # FIXME: Due to kubeflow/pipelines#10914, secret names cannot be provided as pipeline arguments.
            # As a workaround, the secret name is hard coded.
            env2key = ComponentUtils.set_secret_key_to_env()
            kubernetes.use_secret_as_env(task={{tr.name}}_execute_job, secret_name=S3_SECRET, secret_key_to_env=env2key)
        else:
            ComponentUtils.set_s3_env_vars_to_component({{tr.name}}_execute_job, data_s3_access_secret)
        {{tr.name}}_execute_job.after({{tr.name}}_ray_cluster)
        {%- if not loop.last %}
        # cleanup {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %} Ray cluster
        {% if legacy %}
        {{tr.name}}_clean_up_task = cleanup_ray_op(ray_name={{tr.name}}_ray_name, run_id={{tr.name}}_run_id, server_url=server_url)
        {% else %}
        {{tr.name}}_clean_up_task = cleanup_ray_op(ray_name={{tr.name}}_ray_name, run_id={{tr.name}}_run_id, server_url=server_url, additional_params=str({{tr.name}}_additional_params))
        {% endif %}
        ComponentUtils.add_settings_to_component({{tr.name}}_clean_up_task, ONE_HOUR_SEC * 2)
        {{tr.name}}_clean_up_task.set_display_name("Stop {% if tr.name == tr.transform %}{{tr.name}}{% else %}{{tr.name}} ({{tr.transform}}){% endif %} Ray cluster")
        {{tr.name}}_clean_up_task.after({{tr.name}}_execute_job)
        last_clean_task = {{tr.name}}_clean_up_task
        {%- endif %}
        {%- endfor %}

if __name__ == "__main__":
    import argparse
    default_output = os.path.relpath(__file__.replace(".py", ".yaml"))
    parser = argparse.ArgumentParser(description="KFP pipeline with {% for tr in transforms %}{{tr.name}}{% if not loop.last %}, {% endif %}{%- endfor %}")
    parser.add_argument("-o", "--output", type=str, default=default_output, help="output kubeflow file (%(default)s)")
    parser.add_argument("-i", "--image", type=str, default=KFP_IMAGE, help="KFP base image (%(default)s)")
    parser.add_argument("-p", "--pull_secret", type=str, default=KFP_IMAGE_PULL_SECRET, help="KFP base image pull secret name (%(default)s)")
    parser.add_argument("-s", "--s3_access_secret", type=str, default=S3_SECRET, help="COS access secret name (%(default)s)")
    parser.add_argument("-t", "--tmp_folder", type=str, default=TMP_FOLDER, help="temporary storage (COS folder) (%(default)s)")
    parser.add_argument("-f", "--input_folder", type=str, default=INPUT_FOLDER, help="COS folder with data to be processed (%(default)s)")
    parser.add_argument("-d", "--output_folder", type=str, default=OUTPUT_FOLDER, help="COS folder to store the processed data (%(default)s)")

    args = parser.parse_args()
    KFP_IMAGE=args.image
    KFP_IMAGE_PULL_SECRET==args.pull_secret
    S3_SECRET=args.s3_access_secret
    INPUT_FOLDER=args.input_folder
    OUTPUT_FOLDER=args.output_folder
    TMP_FOLDER=args.tmp_folder

    # Compiling the pipeline
    kfp.compiler.Compiler().compile({{dsl_pipeline_name}}, args.output)
