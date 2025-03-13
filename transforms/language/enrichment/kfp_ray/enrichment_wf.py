
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
import os, sys, json

import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
from kubernetes import client as k8s_client
from workflow_support.compile_utils import ONE_HOUR_SEC, ONE_WEEK_SEC, ComponentUtils

import wff

task_image = f"quay.io/dataprep1/data-prep-kit/{wff.short_name}-ray:latest"

# components
base_kfp_image = "quay.io/dataprep1/data-prep-kit/kfp-data-processing:latest"

# path to kfp component specifications files
component_spec_path = "../../../../kfp/kfp_ray_components/"


# KFPv1 and KFP2 uses different methods to create a component from a function. KFPv1 uses the
# `create_component_from_func` function, but it is deprecated by KFPv2 and so has a different import path.
# KFPv2 recommends using the `@dsl.component` decorator, which doesn't exist in KFPv1. Therefore, here we use
# this if/else statement and explicitly call the decorator.
if os.getenv("KFPv2", "0") == "1":
    # In KFPv2 dsl.RUN_ID_PLACEHOLDER is deprecated and cannot be used since SDK 2.5.0. On another hand we cannot create
    # a unique string in a component (at runtime) and pass it to the `clean_up_task` of `ExitHandler`, due to
    # https://github.com/kubeflow/pipelines/issues/10187. Therefore, meantime we use a unique string created at
    # compilation time.
    import uuid

    compute_exec_params_op = dsl.component_decorator.component(
        func=wff.compute_exec_params_func, base_image=base_kfp_image
    )
    print(
        "WARNING: the ray cluster name can be non-unique at runtime, please do not execute simultaneous Runs of the "
        + "same version of the same pipeline !!!"
    )
    run_id = uuid.uuid4().hex
else:
    compute_exec_params_op = comp.create_component_from_func(
        func=wff.compute_exec_params_func, base_image=base_kfp_image
    )
    run_id = dsl.RUN_ID_PLACEHOLDER

# create Ray cluster
create_ray_op = comp.load_component_from_file(component_spec_path + "createRayClusterComponent.yaml")
# execute job
execute_ray_jobs_op = comp.load_component_from_file(component_spec_path + "executeRayJobComponent.yaml")
# clean up Ray
cleanup_ray_op = comp.load_component_from_file(component_spec_path + "deleteRayClusterComponent.yaml")

wff.ops = dict(
        compute_exec_params=compute_exec_params_op, 
        create_ray=create_ray_op, 
        execute_ray_jobs=execute_ray_jobs_op,
        cleanup_ray=cleanup_ray_op)
wff.run_id = run_id

# Task name is part of the pipeline name, the ray cluster name and the job name in DMF.
TASK_NAME: str = wff.short_name

if __name__ == "__main__":
    if len(sys.argv) > 2:
        wff.task_image = sys.argv[2]
    # Compiling the pipeline
    compiler.Compiler().compile(getattr(wff, wff.short_name), sys.argv[1])
