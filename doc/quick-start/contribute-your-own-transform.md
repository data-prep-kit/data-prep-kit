<h1 align="center">Data Prep Kit- Developer Tutorial </h1>

<div align="center"> 

<?  [![Status](https://img.shields.io/badge/status-active-success.svg)]() ?>
<?  [![GitHub Issues](https://img.shields.io/github/issues/kylelobo/The-Documentation-Compendium.svg)](https://github.com/IBM/data-prep-kit/issues) ?>
<?  [![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/IBM/data-prep-kit/pulls) ?>
</div> 

In this tutorial, we take the developer through the steps for contributing a new transform to the DPK. We will cover:
1. How to clone the repo and set up the file structure for the transform
1. Write the code by implementing the transform specific functionality 
1. Use the framework capabilities to accelerate development, testing and deployment

For this tutorial, we will follow a suggested flow. Developers are welcome to explore on their own to achieve the same results. Except for the transform name and module name, developers have a lot of freedom in how they choose their class name, file names and file structure. That said, following the convention proposed in this document would make it easier for the community to chime in to help with debugging and maintaining the code base.

The new transform we will build  as part of this tutorial is meant to annotate each document in the data set with a digest value that is calculated using a SHA256, SHA512 or MD5 hash function. The objective is to show how we can use a user defined function to build a transform and how developers can specify the configuration parameters for the transform and how we integrate the transform with the python and/or ray orchestrators.

- For the purpose of this tutorial, our transform will be called **digest** and the python named module is **dpk_digest**. Developers have some freedom in how they name their modules to the extent that the chosen name does not conflict with an existing transform name.

- The user defined function for this tutorial is a simple annotator that uses the python hashlib package: 
 ```  
      hash = hashlib.new(self.algorithm)
      digest=hash.update(elt.encode('utf-8'))
```
- The transform defines a single configuration parameter **digest_algortihm** that specifies the name of the digest algorithm to use and selected from a predefined list that includes **\['SHA256', 'SHA512', or 'MD5'\]**


## List of Steps to follow in this part of the tutorial

1. [Create a folder structure](#setup) - clone git repo and create file structure for new transform
1. [Implement AbstractTableTransform](#digesttransform) - core functionality for annotating documents
1. [Implement TransformConfiguration](#digestconfiguration) - configure and validate transform parameters
1. [Implement PythonTransformRuntimeConfiguration](#digestruntime) - wire the transform to the runtime so it is correctly invoked
1. [Implement RayTransformRuntimeConfiguration](#rayruntime) - extend the transform to scale up using ray
1. [Develop Unit Test](#unittest) - get test data and write Unit Test
1. [Integrate with CI/CD](#cicd) - automate testing, integration and packaging
1. [Create notebook](#notebook) - jupyter notebook showing how the transform can be invoked
1. [Create Readme file](#readme) - Readme file explaining how the transform is used
1. (Optional)[Setup for KFP Pipeline](#kfp) - Create artifacts for integrating with KFP Workflow


## Step 1: Create a folder structure <a name=setup></a>

**fork and clone the repo locally**

This can be done from the github web browser or using the gh CLI as below:

Example using CLI (https://github.com/cli/cli)

```shell
gh auth login --skip-ssh-key
gh repo fork git@github.com:IBM/data-prep-kit.git --default-branch-only 
```

ASSUMPTION: We assume that the developer had already installed git cli and setup her/his public key as part of the developer’s profile.  https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account



**Create a placeholder for the new transform**

The DPK transforms are currently organized in three categories for Code (Transforms that are used specifically for programming languages), 
Language(Transforms that are used specifically for natural languages) and Universal (Transforms that are used for both language and code). It is safe to assume that our transform can be used for calculating the hash for natural languages text and programming languages alike and we will add it to the universal subfolder. We will also create the python module and a skeleton of the code including a notebook and readme.md file. A typical implementation would have the following file structure.

```
data-prep-kit
│
└───transforms
│   |
│   └───universal
│       │
│       └───digest
│            |
│            └───dpk_digest
│            |      │
│            |      │ __init__.py
│            |      │ transform.py
│            |      | runtime.py
│            │      |
│            |      └───ray
│            |           │ __init__.py
│            |           | runtime.py
│            |           │ 
│            └───test
│            │    |
│            │    |test_digest_ray.py
│            │
│            └───test-data
│            │     |
│            |     └───input
│            |     |     │
│            |     |     │ testfile.parquet
│            |     |     
│            |     └───expected
│            |          │
│            |          │ testfile.parquet
│            |          │ metadata.json
│            | 
│            | requirements.txt
│            | Dockerfile.python
│            | Dockerfile.ray
│            | digest.ipynb
│            | README.md
│            | Makefile
```

although our transform does not require additional packages, we need to create an empty requirements.txt file

```shell
cd data-prep-kit/transforms/universal/digest
touch requirements.txt
```

## Step 2: Implement AbstractTableTransform <a name="digesttransform"></a>

**dpk_digest/transform.py** 

This file implements the key logic for the transform. It receives a pyarrow table with a list of documents in the data set and appends a new column with a digest value. We will describe the contents of the file in 2 sections:

- The first portion of the file includes the language for the license used to distribute and use the code and a set of import statements for the library modules that will be needed for invoking this transform.


```python
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

from typing import Any

import pyarrow as pa
import hashlib
from data_processing.transform import AbstractTableTransform
from data_processing.utils import TransformUtils
```

**AbstractTableTransform** defines a template for the APIs that will be invoked by the runtime to trigger the transform.

**TransformUtils** provides a number of shortcuts commonly used by the transforms for data conversions, table manipulations, etc.



- The remaining section of the file implements the Transform method that will be called by the framework when new data is available for annotation. 


```python
class DigestTransform(AbstractTableTransform):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        ## If the algorithm is not specified, use sha256
        self.algorithm = config.get('digest_algorithm', "sha256")

    def transform(self, 
                  table: pa.Table, 
                  file_name: str = None) -> tuple[list[pa.Table], dict[str, Any]]:
            
        ## calculate digest for the content column
        tf_digest = []
        for elt in table['contents'].to_pylist():
            h = hashlib.new(self.algorithm)
            h.update(elt.encode('utf-8'))
            tf_digest.append(h.hexdigest())

        ## digest as a new column to the existing table
        table = TransformUtils.add_column(table=table, 
                                           name='digest', 
                                           content=tf_digest)
        
        metadata = {"nrows": len(table)}
        return [table], metadata
```

**\__init__()** receives a dictionary that represents the different configuration parameters specified by the user. In our case, the only parameter used is the string value representing the name of digest. If the user does not specify a digest, we will use default value for "sha256".

**transform()** The transform method implements the callback that the runtime uses when it identifies new data to be processed by this transform. It
receives a pyarrow table, calculates the digest for each row in the table and appends the digest as a new column to the same table.


**dpk_digest/\__init__.py**

```python
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
###############################################################################
from .transform import *
```

## Step 3: Implement TransformConfiguration <a name="digestconfiguration"></a>

**dpk_digest/runtime.py**  This file implements 3 classes, the first being TransformConfiguration. It defines two user defined methods that must be implemented by the developer for each transform:

* The add_input_params() method is called by the framework to define the set of command line parameters exposed by the runtime to configure the transforms.  The runtime processes the command line parameters and makes them available to the transform instance initializer.
* The apply_input_params() method is called by the framework to validate the values associated with the configuration parameter.

```python
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
import sys
from dpk_digest.transform import DigestTransform
from data_processing.transform import TransformConfiguration
from data_processing.utils import ParamsUtils, CLIArgumentProvider, get_logger
from argparse import ArgumentParser, Namespace
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.runtime.pure_python.runtime_configuration import (
    PythonTransformRuntimeConfiguration,)

logger = get_logger(__name__)

class DigestConfiguration(TransformConfiguration):
    def __init__(self):
        ## Identify the transform implementation that this configuration relates to
        super().__init__(name='digest', transform_class=DigestTransform,)

    def add_input_params(self, parser: ArgumentParser) -> None:
        ## Define how varius configuration parameters should be parsed
        parser.add_argument(
            "--digest_algorithm",
            type=str,
            help="Specify the hash algorithm to use for calculating the digest value.",
        )

    def apply_input_params(self, args: Namespace) -> bool:
        ## Validate each of the configuration parameters received from the user
        captured = CLIArgumentProvider.capture_parameters(args, 'digest', True)
        self.params = self.params | captured
        if captured.get('digest_algorithm') not in ['sha256','SHA512', 'MD5']:
            logger.error(f"Parameter digest_algorithm cannot be other than ['sha256','SHA512', 'MD5']. You specified {args.digest_algorithm}")
            return False
        return True
```



## Step 4: Implement PythonTransformRuntimeConfiguration <a name="digestruntime"></a>

**dpk_digest/runtime.py (continued)**  The other two classes in this file include:

- DigestRuntime: Implements PythonTransformRuntimeConfiguration and wires the transform into the python orchestrator and allows the framework to instantiate, configure and invoke the transfrom.

```Python
class DigestRuntime(PythonTransformRuntimeConfiguration):

    def __init__(self):
        super().__init__(transform_config=DigestConfiguration())

if __name__ == "__main__":
    launcher = PythonTransformLauncher(DigestRuntime())
    launcher.launch()
```



- Digest: Implements a wrapper that simplifies how the transform is invoked and hides some of the complexity that is inherited by the runtime orchestrator.

```Python
class Digest:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        # if input_folder and output_folder are specified, then assume it is represent data_local_config
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"]
            del self.params["output_folder"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        launcher = PythonTransformLauncher(DigestRuntime())
        return_code = launcher.launch()
        return return_code
```

## Step 5: Implement RayTransformRuntimeConfiguration <a name="rayruntime"></a>

**dpk_digest/ray/runtime.py** This file implements the necessary API for integrating the digest transform with the ray orchestrator.

```Python
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
import sys

from data_processing.utils import ParamsUtils, get_logger
from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing_ray.runtime.ray.runtime_configuration import RayTransformRuntimeConfiguration
from dpk_digest.runtime import DigestConfiguration

logger = get_logger(__name__)

class DigestRayRuntime(RayTransformRuntimeConfiguration):

    def __init__(self):
        super().__init__(transform_config=DigestConfiguration())

if __name__ == "__main__":
    launcher = RayTransformLauncher(DigestRayRuntime())
    launcher.launch()
```

- Similarly, we will implement the Digest api for the ray submodule to define a simplified method for the API.

```Python
class Digest:
    def __init__(self, **kwargs):
        self.params = {}
        for key in kwargs:
            self.params[key] = kwargs[key]
        try:
            local_conf = {k: self.params[k] for k in ("input_folder", "output_folder")}
            self.params["data_local_config"] = ParamsUtils.convert_to_ast(local_conf)
            del self.params["input_folder"], self.params["output_folder"]
        except:
            pass
        try:
            worker_options = {k: self.params[k] for k in ("num_cpus", "memory")}
            self.params["runtime_worker_options"] = ParamsUtils.convert_to_ast(worker_options)
            del self.params["num_cpus"], self.params["memory"]
        except:
            pass

    def transform(self):
        sys.argv = ParamsUtils.dict_to_req(d=(self.params))
        launcher = RayTransformLauncher(DigestRayRuntime())
        return_code = launcher.launch()
        return return_code
```



## Step 6: Develop Unit Test <a name="unittest"></a>

- For our testing, we will need some initial data as input to our transform. We will copy it from another transform test folder.

```shell
cd data-prep-kit/transforms/universal/digest
mkdir -p test-data/input
cp ../../language/doc_chunk/test-data/expected/*.parquet test-data/input
```


- Create a virtual environment and run the transform against the input data to produce the expected output data. This will be used by the CI/CD to verify that the logic of the transform always produces the same output for a given input.

```shell
cd data-prep-kit/transforms/universal/digest
python -m venv venv && source venv/bin/activate
pip intall data-prep-toolkit
pip install -r requirements.txt
python -m dpk_digest.runtime --digest_algorithm sha256 --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'expected’}” 
```
If the test code runs properly, we should see 2 new files created in the test-data/expected folder:
```shell
test-data/expected/test1.parquet
test-data/expected/metadata.json
```

- Developers have some freedom in designing their unit tests. In this section we show how developers can use the test fixture defined in the framework to rapidly create unit tests.

**test/test_digest.py**

```python
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

import os

from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from data_processing.runtime.pure_python import PythonTransformLauncher
from dpk_digest.runtime import DigestRuntime


class TestDigestTransform(AbstractTransformLauncherTest):

    def get_test_transform_fixtures(self) -> list[tuple]:
        basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                               "../test-data"))
        fixtures = []
        transform_config = {
            "run_locally": True,
            "digest_algorithm": "sha256", 
        }
        launcher = TransformLauncher(DigestRuntime())
        fixtures.append((launcher, transform_config, 
                         basedir + "/input", 
                         basedir + "/expected"))
        return fixtures
```

## Step 7: Integrate with CI/CD <a name="cicd"></a>

- The repo implements a rich set of functionality for setting up the environment, running unit tests, publishing the transforms to pypi, building the transforms as part of a docker image and running it with Kubeflow. For the purpose of this section, we will explore only a portion of the capabilities that support this initial phase of the implementation.

We will first copy the Makefile template from the parent folder:

```shell
cd data-prep-kit/transforms/universal/digest
cp ../../Makefile.transform.template Makefile
cp ../../Dockerfile.python.template Dockerfile.python
```

- The Makefile has a number of predefined targets that will be useful for testing and publishing the transform. To get a list of available targets, run the following command from the digest folder:

```shell
make
```
Below is a small list of available targets that may be useful at this stage. 
```
Target               Description
------               -----------
clean                Clean up the virtual environment.
venv                 Create the virtual environment using requirements.txt
test-src             Create the virtual environment using requirements.txt and run the unit tests
image                Build the docker image for the transform
test-image           Build and test the docker image for the transform 
publish              Publish the docker image to quay.io container registry
```

- Create virtual environment with all preloaded dependencies:
```shell
make clean && make venv
```

- Run unit tests and verify the proper operations of the code:

```shell
make test-src
```

- Edit transforms/pyproject.toml and add the requirements.txt for the module and the name of the module and its package location:

```shell
digest = { file = ["universal/digest/requirements.txt"]}
...
[tool.setuptools.package-dir]
...
dpk_digest = "universal/digest/dpk_digest"
...
```


## Step 8: Create Notebook <a name="notebook"></a>

The notebook should show how to run the notebook from the current folder. Guidance on how to set up jupyter lab can be found [here](quick-start.md). This is a simple [notebook](https://github.com/mt747/data-prep-kit/blob/block_digest/transforms/universal/digest/digest.ipynb) for our digest transform. 

## Step 9: Create Readme file <a name="readme"></a>

The README file for the transform should have, at a minimum, the following sections: Summary, Contributors, Configuration and command line options, an Example of how to run from command line and link to a notebook. If applicable, it should have more sections on Troubleshooting, Transforming data using the transform image and sections on Ray and/or Spark versions of the transform. 
[This](https://github.com/mt747/data-prep-kit/blob/block_digest/transforms/universal/digest/README.md) is a minimal README file for our digest transform. 

## Step 10: Set up KFP Pipeline  <a name="kfp"></a>

It might be desirable to build a KubeFlow Pipeline (KFP) chaining multiple transforms together. In this section, we will cover the steps a developer needs to take so that the operation team can create a pipeline tailored to their specific use case. We will only cover the artifact that the developer needs to produce to enable the integration of the digest transform in a KFP pipeline.

**kfP-ray/Makefile**

- Create a folder to host KFP related artifacts

```shell
cd data-prep-kit/transforms/universal/digest
mkdir -p kfp_ray
cp ../../Makefile.kfp.template kfp_ray/Makefile
```

**kfP-ray/digest_wf.py**

- Create a KFP definition file. This file will be used to produce the kfp workflow yaml definition file. The full content of this file in available [here](https://github.com/mt747/data-prep-kit/blob/13be7f4349e498041afe9834b1961d158728316a/transforms/universal/digest/kfp_ray/digest_wf.py). We only highlight some of the key elements.


- This file defines the reference to the docker image for the transform and entry point:

    * task_image = "quay.io/dataprep1/data-prep-kit/digest-ray:latest"
    * EXEC_SCRIPT_NAME: str = "-m dpk_digest.ray.runtime"


```Python
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
import os

import kfp.compiler as compiler
import kfp.components as comp
import kfp.dsl as dsl
from workflow_support.compile_utils import ONE_HOUR_SEC, ONE_WEEK_SEC, ComponentUtils


task_image = "quay.io/dataprep1/data-prep-kit/digest-ray:latest"

# the name of the job script
EXEC_SCRIPT_NAME: str = "-m dpk_digest.ray.runtime"
# components
base_kfp_image = "quay.io/dataprep1/data-prep-kit/kfp-data-processing:0.2.3"

# path to kfp component specifications files
component_spec_path = "../../../../kfp/kfp_ray_components/"

```


- It defines the list of configuration parameters that are required by the framework return as a dictionary structure:

    * "digest_algorithm": digest_algorithm,

```Python
def compute_exec_params_func(
    ...
    ...
    digest_algorithm: str,
) -> dict:
    return {
        ...
        ...
        "digest_algorithm": digest_algorithm,
    }
```

- It assigns a name to this workflow task:

    * TASK_NAME: str = "digest"

```Python
# Task name is part of the pipeline name, the ray cluster name and the job name in DMF.
TASK_NAME: str = "digest"
```

- Pipeline definition method and default values:

```Python    
 @dsl.pipeline(
    name=TASK_NAME + "-ray-pipeline",
    description="Pipeline for digest",
    )
def digest(
    ###
    ...
    ###
):
```

- It defines the __main__ entry point for compiling the yaml file required for running kfp.

```Python
if __name__ == "__main__":
    # Compiling the pipeline
    compiler.Compiler().compile(digest, __file__.replace(".py", ".yaml"))
```


## Contributors

- Maroun Touma (touma@us.ibm.com)
- Shahrokh Daijavad (shahrokh@us.ibm.com)

