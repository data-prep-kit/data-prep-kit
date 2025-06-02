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

import importlib
import importlib.util
from transform_registry import FILE_TRANSFORM_REGISTRY, MODULE_TRANSFORM_REGISTRY

def create_transform_from_file(transform_name: str, params: dict = None):
    if transform_name not in FILE_TRANSFORM_REGISTRY:
        raise ValueError(f"Transform '{transform_name}' not in FILE_TRANSFORM_REGISTRY.")

    entry = FILE_TRANSFORM_REGISTRY[transform_name]
    file_path = entry["path"]
    class_name = entry["class"]

    spec = importlib.util.spec_from_file_location(f"file_transform_{transform_name}", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, class_name):
        raise ImportError(f"Class '{class_name}' not found in module loaded from {file_path}")

    return getattr(module, class_name)((params or {}))


def create_transform_from_module(transform_name: str, params: dict = None):
    if transform_name not in MODULE_TRANSFORM_REGISTRY:
        raise ValueError(f"Transform '{transform_name}' not in MODULE_TRANSFORM_REGISTRY.")

    entry = MODULE_TRANSFORM_REGISTRY[transform_name]
    module_path = entry["module"]
    class_name = entry["class"]

    module = importlib.import_module(module_path)

    if not hasattr(module, class_name):
        raise ImportError(f"Class '{class_name}' not found in module '{module_path}'")

    return getattr(module, class_name)((params or {}))

def validate_all_transforms():
    failed = []

    for name in FILE_TRANSFORM_REGISTRY:
        try:
            print(f"Validating file-based transform: {name}")
            create_transform_from_file(name, {'urls':['https://wikipedia.com'],
'int_column': 'int_column',
'max_rows_per_table': 10,
'gcls_model_credential': 'test',
'gcls_model_file_name': 'model',
'aggregator': 'test'
})
        except Exception as e:
            print(f"Failed to load file-based transform '{name}': {e}")
            failed.append(name)

    for name in MODULE_TRANSFORM_REGISTRY:
        try:
            print(f"Validating module-based transform: {name}")
            create_transform_from_module(name, {'urls':['https://wikipedia.com'],
'int_column': 'int_column',
'max_rows_per_table': 10,
'gcls_model_credential': 'test',
'gcls_model_file_name': 'model',
'aggregator': 'test'
})
        except Exception as e:
            print(f"Failed to load module-based transform '{name}': {e}")
            failed.append(name)

    if not failed:
        print("\nAll transforms validated successfully!")
    else:
        print(f"\n{len(failed)} transform(s) failed: {failed}")


if __name__ == "__main__":
    validate_all_transforms()

