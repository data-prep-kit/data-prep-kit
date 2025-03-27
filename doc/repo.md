# Repository Structure and Use 

Here we discuss the structure, use and approach to code management in the repo.
# Setup

There are various entry points that you can choose based on the use case. Each entry point has its pre-requirements and setup steps.
The common part of are:
#### Prerequisites
- Python 3.10 or 3.11 
-Docker/Podman

Two important development tools will also be installed using the steps below:
- [pre-commit](https://pre-commit.com/)
- [twine](https://twine.readthedocs.io/en/stable/) 

#### Installation Steps
```shell
pip install pre-commit
pip install twine
...
git clone git@github.com:IBM/data-prep-kit.git
cd data-prep-kit
pre-commit install
```
Please note that there are further installation steps 
for running the transforms in general, as documented 
[here](../data-processing-lib/ray/README.md) 
and on a local Kind cluster or on an existing Kubernetes 
cluster, as documented [here](../kfp/doc/setup.md).


# Repository structure
* data_processing_lib - provides the core transform framework and library 
supporting data transformations in 3 runtimes
    * python 
    * ray
    * spark
 
* transform
    * universal
        * noop 
        * ...
    * code
        * code_quality
        * ...
    * language
        * ...
* kfp - Kubeflow pipeline support
    * kfp_support_lib - Data Preparation Kit Library. KFP support
    * kfp_ray_components - Kubflow pipeline components used in the pipelines
* scripts


# Build and Makefiles
Makefiles are used for operations performed across all projects in the directory tree.
There are two types of users envisioned to use the make files.  

* adminstrators - perform git actions and release management 
* developers - work with core libraries and transforms

Each directory has access to a `make help` target that will show all available targets.

## Administrators 
Generally, administrators will issue make commands from the top of the repository to, for example
publish a new release.  The top level make file provides a set of targets that 
are executed recursively, which as a result are expected to be implementd by
sub-directories.  These and their semantics are expected to be implemented,
as appropriate, in the sub-directories are as follows:

* clean - Restore the directory to as close to initial repository clone state as possible. 
* build - Build all components contained in a given sub-directory.  
This might include pypi distributions, images, etc.
* test -  Test all components contained in a given sub-directory. 
* publish - Publish any components in sub-directory. 
This might include things published to pypi or the docker registry.
* set-versions - apply the DPK_VERSION to all published components. 

Sub-directories are free to define these as empty/no-op targets, but generally are required
to define them unless a parent directory does not recurse into the directory.

### Build and deploy a dev release for integration testing (Recommended step for all transforms prior to merging the corresponding PR)

1. Create your fork from the main repo or sync an existing fork with main repo
1. Clone the fork
    ```shell
    git clone git@github.com:<USER>/data-prep-kit.git data-prep-kit-dev
    cd data-prep-kit-dev
    ```
1. Create a new local branch from dev
    ```shell
    git checkout dev
    git checkout -b "testing-$(date '+%Y-%m-%d')"
    ```
1. Merge changes from remote branch (if more than one PR, repeat below for each PR). In the example below, replace '<fork_url>' and '<branch_name>' with the git url and branch from each PR (e.g, PR1, PR2, ...)
    ```shell
     git remote add <remote_name_PR1> <fork_url> 
     git fetch <remote_name_PR1> <branch_name>
     git merge <remote_name_PR1>/<branch_name>
     ```
1. Change to the transforms folder, clean any previous build, build a new wheel and publish the wheel as a dev branch to pypi. Follow [instructions](https://packaging.python.org/en/latest/specifications/pypirc/#using-another-package-index) to setup your environment to be able to publish:
    ```shell
    cd transforms
    rm -fr build dist data_prep_toolkit_transforms.egg-info
    make build-pkg-dist
    pip install twine
    make publish-dist
    ```
1. **Note**- 'make publish-dist' will fail if a previous build with the same tag is already present on pypi. In this case, add a 'build tag' and publish again. The 'build tag' is a number that immediately follows the distribution package version seperated by a dash `({distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl)`

    ```shell
    mv dist/data_prep_toolkit_transforms-1.0.1.dev1-py3-none-any.whl dist/data_prep_toolkit_transforms-1.0.1.dev1-1-py3-none-any.whl
    ```
    ```shell
    make publish-dist
    ```
   **Note**-  'make publish-dist' will fail if the choosen 'build tag' already exists. In this case, consult the pypi site to identify the latest build tag previously used and increment by 1
   
1. When testing the new wheel in a notebook or a venv, make sure to use the --no-cache option: `pip install --no-cache data-prep-toolkit-transforms-1.0.1.dev1`
    
    

## Developers
Generally, developers will be working in a python project directory
(e.g., data-processing-lib/python, transforms/universal/filter, etc.) 
and can issue the administrator's make targets (e g., build, test, etc)
or others that might be defined locally
(e.g., venv, test-image, test-src in transform projects).
Key targets are as follows:

* venv -  creates the virtual environment from either a pyproject.toml or requirements.txt file.
 
If working with an IDE, one generally makes the venv, then configures the IDE to 
reference the venv, src and test directories.

Transform projects generally include these transform project-specific targets for convenience,
which are triggered with the the `test` target.

* test-src - test python tests in the test directory
* test-image - build and test the docker image for the transform

Please also consult [transform project conventions](../transforms/README.md#transform-project-conventions) for 
additional considerations when developing transforms.

### Transforms and KFP 
The kfp_ray directories in the transform projects provide 
`workflow-` targets and are dedicated to handling the 
[Kubeflow Pipelines](https://github.com/kubeflow/pipelines) 
workflows for the specified transforms.

```

