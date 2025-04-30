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

import os, sys, stat, json, re, importlib, yaml, subprocess, tempfile, argparse
from collections import namedtuple

DEFAULT_RAY_HEAD_OPTIONS = dict(cpu=1, memory=4)
DEFAULT_RAY_WORKER_OPTIONS = dict(replicas=2, max_replicas=2, min_replicas=2, cpu=2, memory=4)
KUBERAY_SERVER_URL = "http://kuberay-apiserver-service.kuberay.svc.cluster.local:8888"
KFP_BASE_IMAGE = "quay.io/dataprep1/data-prep-kit/kfp-data-processing:latest"
ADDITIONAL_PARAMS = dict(wait_interval=2, 
    wait_cluster_ready_tmout=400, 
    wait_cluster_up_tmout=300, 
    wait_job_ready_tmout=400, 
    wait_print_tmout=30, 
    http_retries=5, 
    delete_cluster_delay_minutes=0)
DEFAULT_RUNTIME_ACTOR_OPTIONS = dict(num_cpus=1)
DEFAULT_RUNTIME_CODE_LOCATION = dict(github="github", commit_hash="12345", path="path")
DictField = namedtuple("DictField", "Name Value UpdateWithImage Description")
TRANSFORM_DICT_PARAMS = [
    DictField("ray_head_options", DEFAULT_RAY_HEAD_OPTIONS, True, "Ray head options"),
    DictField("ray_worker_options", DEFAULT_RAY_WORKER_OPTIONS, True, "Ray worker options"),
    DictField("runtime_actor_options", DEFAULT_RUNTIME_ACTOR_OPTIONS, False, "Runtime actor options"),
    DictField("runtime_code_location", DEFAULT_RUNTIME_CODE_LOCATION, False, "git repository information"),
    DictField("additional_params", ADDITIONAL_PARAMS, False, "additional parameters for the Ray control commands"),
    ]
Field = namedtuple("Field", "Name Type Description")
# parameters used from the 'transform_common_fields' section
TRANSFORM_COMMON_FIELDS = sorted([ Field(t.Name, dict, t.Description) for t in TRANSFORM_DICT_PARAMS ] + [
    Field("image", str, "image name for the transform"), 
    Field("image_pull_secret", str, "Kubernetes secret for the image repository"), 
    Field("invocation", str, "python arguments for invoking the transform"), 
    Field("env", dict, "environment setting"),
    ], key=lambda x: x.Name)
# parameters used from any transform entry
TRANSFORM_FIELDS = sorted(TRANSFORM_COMMON_FIELDS + [ 
    Field("image_tag", str, "tag for the image name"), 
    Field("transform", str, "the transform name"), 
    Field("name", str, "name to identify this step in workflow, by default the transform name is used"), 
    Field("params", dict, "dictionary param_name: value to replace the default values defined in the transform"),
    Field("args", str, "list of arguments to pass to the transform, by default read fom the transform"), 
    Field("description",str, "description for this step in the workflow, the transfom's description is used by default"), 
    Field("ray_name", str, "name to use for the Ray cluster, the name of the transform is used by default"),
    ], key=lambda x: x.Name)
GlobalField = namedtuple("GlobalField", "Name Type Required Value Description")
GLOBAL_FIELDS = sorted([
    GlobalField("name", str, False, "", "name for this workflow, defaults to the descriptor filename"),
    GlobalField("description", str, False, "", "description for this workflow"),
    GlobalField("server_url", str, False, KUBERAY_SERVER_URL, "KubeRay server URL"),
    GlobalField("dsl_pipeline_name", str, False, "", "DSL function name, defaults to the workflow name"),
    GlobalField("data_max_files", int, False, -1, "number of files to process, -1 to process all"),
    GlobalField("data_num_samples", int, False, -1, "number of samples to process, -1 to process all"),
    GlobalField("data_checkpointing", bool, False, False, "whether to use data checkpointing"),
    GlobalField("transform_common_parameters", dict, False, {}, "parameters that apply to all transforms in this workflow"),
    GlobalField("transforms", list, True, [], "the list of transforms in execution order"),
    GlobalField("kfp_base_image", str, False, KFP_BASE_IMAGE, "dpk/kfp image name"),
    GlobalField("s3_access_secret", str, False, "s3-access", "s3 access secret for the input, output and temporary storage"),
    GlobalField("image_pull_secret", str, False, "image-pull-secret", "secret for getting the dpk/kfp image"),
    GlobalField("input_folder", str, False, "input", "input location"),
    GlobalField("output_folder", str, False, "output", "output location"),
    GlobalField("tmp_folder", str, False, "output/tmp", "temporary storage location"),
    ], key=lambda x: x.Name)

def valid_global_fields():
    return set([f.Name for f in GLOBAL_FIELDS])
def valid_transform_common_fields():
    return set([f.Name for f in TRANSFORM_COMMON_FIELDS])
def valid_transform_fields():
    return set([f.Name for f in TRANSFORM_FIELDS])
#
# resolve all format like string values that reference 'name', 'transform' and 'description'
#
def re_format(d, transform, name, description):
    if isinstance(d, dict):
        return {k: re_format(v, transform, name, description) for k, v in d.items()}
    if isinstance(d, list):
        return [ re_format(v, transform, name, description) for v in d ]
    if isinstance(d, str):
        return d.format(transform=transform, name=name, description=description)
    return d
#
# Update <d> with <u> recursively
#
def r_update(d, u):
    return { 
        k: u.get(k, d.get(k, None)) if not isinstance(u.get(k, d.get(k, None)), dict) else r_update(d.get(k, {}), u.get(k, {}))
        for k in set([k for k in d.keys()]+[k for k in u.keys()])
    }

def re_condition(d):
    d["name"] = d.get("name", d.get("transform", None))
    transform, name, description = [d.get(k, None) for k in ["transform", "name", "description"]]
    return re_format(d, transform, name, description)
#
# Print a warning for every field in <d> not in the <allowed_fields> set
#
def check_fields(d, allowed_fields, where):
    allowed = set(allowed_fields)
    for f in d.keys():
        if f not in allowed:
            print(f"warning: unrecognized field '{f}' in {where}", file=sys.stderr)  
    return d
#
# Search for a dpk transform and and query it for 'short_name', 'description' and the argument list (table)
#
def get_transform_info(transform, module, python_path):
    save_path = [ p for p in sys.path ]
    sys.path += [ p for p in python_path.split(":") if p not in sys.path ]

    module_name = f"dpk_{transform}.{module}"
    tr = importlib.import_module(module_name)

    short_name = tr.short_name
    description = tr.description
    invocation = tr.ray_invocation
    version = tr.__version__
    args = [dict(name=f"{short_name}_{p.Name}", type=p.Type.__name__, value=p.Default, description=p.Description) for p in tr.get_transform_params()]
    
    sys.path = save_path
    return (version, description, args, invocation)

def get_kfp_ray_args(pipeline_config, transform_config):
    tc = transform_config
    pc = pipeline_config
    name = tc["transform"]
    image_info = { k: tc[k] for k in ["image", "image_pull_secret"] if k in tc }
    args = []
    args.append(dict(name=f"ray_name", type="str", value=tc.get("ray_name", f"{pc['name']}-{name}-kfp-ray"), description=f"name of the {name} Ray cluster"))
    #args.append(dict(name=f"{name}_ray_run_id_KFPv2", type="str", value="", description="Ray cluster unique ID used only in KFP v2"))
    for dp in TRANSFORM_DICT_PARAMS:
        value = json.loads(json.dumps(dp.Value))
        value.update(tc.get(dp.Name, {}))
        if dp.UpdateWithImage:
            value.update(image_info)
        args.append(dict(name=f"{dp.Name}", type="dict", value=value, description=dp.Description))
    return args
#
# Defaults for the global parameters
#
def fixup_global_params(pd, input_file):
    name=os.path.basename(input_file)
    global_defaults = {g.Name: g.Value for g in GLOBAL_FIELDS if not g.Required}
    global_defaults.update(dict(
        name=name,
        description=f"KFP pipeline for {name}",
        dsl_pipeline_name=pd.get("name", name),
        ))
    global_defaults.update(pd)
    ## sanitize the dsl name
    global_defaults["dsl_pipeline_name"] = re.sub(r"^([^a-zA-Z])", "dsl_\\1", re.sub(r"(\s|[._::,/*-])+", "_", global_defaults["dsl_pipeline_name"]))
    for f in pd.keys():
        if f not in valid_global_fields():
            print(f"warning: unused global field {f}", file=sys.stderr)
    return global_defaults

def has_dpk_transform(directory):
    with os.scandir(directory) as entries:
        for entry in entries:
            if os.path.isdir(entry) and entry.name.startswith("dpk_"):
                return True
    return False

def scan_dir_for_dpk_transforms(directory):
    if has_dpk_transform(directory):
        return [directory]
    dirs = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if os.path.isdir(entry):
                dset = set(dirs)
                dirs = dirs + [ d for d in scan_dir_for_dpk_transforms(os.path.join(directory, entry.name)) if d not in dset ]
    return dirs
#
# Find all the directories in the path that contain transforms
#
def scan_path_for_dpk_transforms(path):
    dirs = []
    for p in path.split(":"):
        if os.path.isdir(p):
            dset = set(dirs)
            dirs = dirs + [ d for d in scan_dir_for_dpk_transforms(p) if d not in dset ]
    return ":".join(dirs)
#
# Expand the input parameters to the complete set, using the defaults from the transform 
#
def expand_params(input_file, output_file, python_path):
    errors = 0
    ### read the definition file
    with open(input_file, "r") as f:
        pipeline_descriptor = yaml.safe_load(f)

    ### make a python path for transforms
    python_path = scan_path_for_dpk_transforms(python_path)

    ### apply the common parameters and check for errors
    transforms = pipeline_descriptor.get("transforms", None)
    if not transforms:
        print(f"{input_file}: no transforms found", file=sys.stderr)
        return 1, None

    transform_common = pipeline_descriptor.get("transform_common_parameters", {})
    check_fields(transform_common, valid_transform_common_fields(), "transform_common_parameters") 

    for i, t in enumerate(transforms):
        check_fields(t, valid_transform_fields(), f"transform at position {i} ({t.get('name', t.get('transform', '?'))})")

    transform_common = json.dumps(transform_common)
    transforms = [ re_condition(r_update(json.loads(transform_common), tr)) for tr in transforms ]
    
    for i, t in enumerate(transforms):
        if not t.get("transform", None):
            print(f"{input_file}: unknown transform at position {i}", file=sys.stderr)
            errors += 1
        if not t.get("image", None):
            print(f"{input_file}: image not defined for transform at  position {i} ({t.get('transform', '?')})", file=sys.stderr)
            errors += 1

    if errors:
        return 1, None

    ### apply defaults to global parameters
    pipeline_descriptor = fixup_global_params(pipeline_descriptor, input_file)

    ### grab the parameter definiton for each transform
    for i, t in enumerate(transforms):
        transform = t["transform"]
        label = f"{t['name']}" if t["name"] == transform else f"{t['name']} ({transform})"
        # description and invocation can be overridden in the yaml, args must be from the transform
        version, desc, args, invocation = None, None, t.get("args", None), None

        ### load the transform and query it for the argument list, etc.
        if not args:
            for module in ["info", "transform"]:
                try:
                    version, desc, args, invocation = get_transform_info(transform, module, python_path)
                except Exception as e:
                    ### the info module might not exist, but report the failure to load the transfom 
                    if module == "transform":
                        print(f"error: can't get parameters for transform at position {i} ({transform})", file=sys.stderr)
                        print(f"reason: {e}", file=sys.stderr)
                else:
                    break;

        ### can't do without args
        if args is None:
            errors +=1
            continue

        t["description"], t["invocation"] = t.get("description", desc), t.get("invocation", invocation)
        t["version"] = version
        
        ### fixup the image name if we have an explicit tag
        image_tag =  t.get("image_tag", None)
        if image_tag:
            t["image"] = ":".join(t["image"].split(":")[:-1]+[image_tag])

        ### override the default argument values with the ones in the descriptor file

        param_values = { f"{transform}_{p}": v for p, v in t.get("params", {}).items() }
        t["args"] = [dict(name=a["name"], type=a["type"], description=a["description"],  value=param_values.get(a["name"], a["value"])) for a in args]

        ### issue a warning for all params not needed by the transform
        unused_params = [ p for p in t.get("params", {}).keys() if f"{transform}_{p}" not in set([ a["name"] for a in t["args"] ]) ]
        for up in unused_params:
            print(f"warning: parameter \"{up}\" is not used by transform \"{label}\"", file=sys.stderr)

        ### augment the transform arguments with the the ones required by ray and kfp 
        t["kfp_args"] = get_kfp_ray_args(pipeline_descriptor, t)
        if t.get("env", None) is None:
            continue

        envo, envs = {}, {}
        for en, ev in t["env"].items():
            if isinstance(ev, str):
                envs[en] = ev
            elif isinstance(ev, dict):
                if "secret" in ev and "key" in ev:
                    envo[en] = dict(source="secret", name=ev["secret"], key=ev["key"])
                    continue
                source = ev.get("source", None)
                valid_sources = ["SECRET", "CONFIGMAP", "RESOURCE_FIELD", "FIELD"]
                if source is None or source.upper() not in valid_sources:
                    print(f"error: at transform \"{label}\", variable \"{en}\" has unknown source [{source}]", file=sys.stderr)
                    print(f"note: must be one of {', '.join(valid_sources)}", file=sys.stderr)
                    errors += 1
                    continue
                if ev.get("key", None) is None or ev.get("name", None) is None:
                    print(f"error: at transform \"{label}\", variable \"{en}\" needs all \"source\", \"name\" and \"key\" fields", file=sys.stderr)
                    errors += 1
                    continue
                envo[en] = ev
            else:
                envs[en] = f"{ev}"

        t["envo"] = envo
        t["envs"] = envs
        del t["env"]

    pipeline_descriptor["transforms"] = transforms
    if transform_common:
        del pipeline_descriptor["transform_common_parameters"]
    
    if output_file == "-":
        yaml.dump(pipeline_descriptor, sys.stdout, default_flow_style=False)
    elif output_file:
        with open(output_file, "w") as f:
            yaml.dump(pipeline_descriptor, f, default_flow_style=False)

    return errors, pipeline_descriptor
#
# Genereate the KFP python workflow by applying the complete set of parameters to the template
#
def apply_template(descriptor, template_file, output_file):
    if not template_file:
        print("template file is needed", file=sys.stderr)
        return 1, None

    from jinja2 import Environment, FileSystemLoader

    script_dir = os.path.dirname(os.path.abspath(template_file))
    environment = Environment(loader=FileSystemLoader(script_dir))
    template = environment.get_template(os.path.basename(template_file))

    content = template.render(descriptor)

    if output_file == "-":
        sys.stdout.write(content)
    elif output_file:
        with open(output_file, mode="w", encoding="utf-8") as wf:
            wf.write(content)
        st = os.stat(output_file)
        os.chmod(output_file, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return 0, content
#
# Main entry point
#
def make_dpk_workflow(pipeline_file, expanded_pipeline_file, workflow_python_file, workflow_yaml_file, workflow_template_file, transform_search_path):
    rc, descr = expand_params(pipeline_file, expanded_pipeline_file, transform_search_path)
    if rc:
        return rc
    rc, wf = apply_template(descr, workflow_template_file, workflow_python_file)
    if rc:
        return rc
    if workflow_yaml_file:
        wfpy = workflow_python_file
        if not wfpy:
            tmp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False)
            tmp.write(wf)
            tmp.close()
            wfpy = tmp.name
        rc = subprocess.run(["python", wfpy, "-o", workflow_yaml_file]).returncode
        if not workflow_python_file:
            os.unlink(wfpy)
    return rc


if __name__ == "__main__":
    default_template = os.path.join(os.path.dirname(os.path.relpath(__file__)), "template-dpk_wf.py")

    parser = argparse.ArgumentParser(description="pipeline generator")
    parser.add_argument(dest="descriptor", metavar="INPUT", type=str, default="pipeline-descriptor.yaml", help="pipeline definition file (yaml)")
    parser.add_argument("-y", "--yaml", type=str, default=None, help="output pipeline descriptor augmented with all transforms arguments")
    parser.add_argument("-t", "--template", type=str, default=default_template, help="template to generate workflow file from (%(default)s)")
    parser.add_argument("-w", "--workflow", type=str, default=None, help="output python workflow file")
    parser.add_argument("-o", "--output", type=str, default=None, help="output yaml workflow file")
    parser.add_argument("-p", "--path", type=str, default=".", help="python path to search for transforms")
    parser.add_argument("-f", "--help-fields", action='store_true', default=False, help="display the list of valid fields")
    args = parser.parse_args()
    if args.help_fields:
        print("\nGlobal fields")
        print("=============")
        for f in GLOBAL_FIELDS:
            print(f"  {f.Name} ({f.Type.__name__}):\n     {f.Description}, default: {f.Value if f.Value else 'none'}")
        print("\nTransform common fields")
        print("======================")
        for f in TRANSFORM_COMMON_FIELDS:
            print(f"  {f.Name} ({f.Type.__name__}):\n     {f.Description}")
        print("\nTransform fields")
        print("======================")
        for f in TRANSFORM_FIELDS:
            print(f"  {f.Name} ({f.Type.__name__}):\n     {f.Description}")
        rc = 0
    else:
        rc = make_dpk_workflow(args.descriptor, args.yaml, args.workflow, args.output, args.template, args.path)
    sys.exit(rc)
