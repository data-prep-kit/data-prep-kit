import importlib.resources
import json
import os
import subprocess
from ansiblelint.schemas import __file__ as schemas_module
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from typing import Optional

schemas_package_name = "code_quality.schemas"

def kubeconform_k8s_check(k8s_yaml: str) -> bool:
    return _kubeconform_check(k8s_yaml)

def kubeconform_openshift_check(openshift_yaml: str) -> bool:
    with importlib.resources.as_file(
        importlib.resources.files(schemas_package_name)
    ) as schema_dir:
            schema_location = os.path.join(
                schema_dir, "openshift/v4.9.18-standalone-strict/{{.ResourceKind}}.json"
    )

    return _kubeconform_check(openshift_yaml, schema_location)

def kubeconform_crd_check(k8s_crd_yaml: str) -> bool:
    with importlib.resources.as_file(
        importlib.resources.files(schemas_package_name)
    ) as schema_dir:
        schema_location = os.path.join(
            schema_dir,
            "CRD/CRDs-catalog-main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json",
        )
    return _kubeconform_check(k8s_crd_yaml, schema_location)

def _kubeconform_check(k8s_yaml: str, schema_location: Optional[str] = None) -> bool:
    """Returns True if the string is a valid K8/openshift YAML.
    Note: This requires the kubeconform CLI to be installed to function."""

    result = subprocess.run(
        ["kubeconform"]
        + ([] if schema_location is None else ["-schema-location", schema_location]),
        input=k8s_yaml.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return result.returncode == 0

def get_ansible_schemas():
    schemas = {}
    # print("--",os.listdir(os.path.dirname(schemas_module)))
    for file in os.listdir(os.path.dirname(schemas_module)):
        if file[0] != '_' and file.endswith('.json'):
            type = file.split('.')[0]
            if type in ["playbook", "tasks"]:
                fname = os.path.join(os.path.dirname(schemas_module), file)
                with open(fname, encoding="utf-8") as f:
                    schemas[type] = json.load(f)
    return schemas

schemas = get_ansible_schemas()


def validate_yaml(yaml_str, schema):
    try:
        validate(instance=yaml_str, schema=schema)
    except ValidationError as exc:
        return 'validation failed', exc.message
    except Exception as e:
        return 'validation Exception', e
    return '', ''

def validate_ansible(content):
    try:
        yaml_data = yaml.safe_load(content)
    except Exception:
        return False
    
    for type, schema in schemas.items():
        err, _ = validate_yaml(yaml_data, schema)
        if err == '':
            print(f"{type:22}: OK")
            return True
    return False
