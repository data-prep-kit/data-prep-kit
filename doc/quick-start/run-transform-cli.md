# Running a Transform from the Command Line 
Here we address a simple use case of applying a single transform to a 
set of parquet files. 
We'll use the `pdf2parquet` transform as an example, but in general, this process
will work for any of the transforms contained in Data Prep Kit.
Additionally, what follows uses the 
[python runtime](../../data-processing-lib/doc/python-runtime.md)
but the examples below should also work for the
[ray](../../data-processing-lib/doc/ray-runtime.md)
or
[spark ](../../data-processing-lib/doc/spark-runtime.md)
runtimes.

### Install data prep kit from PyPi

The latest version of the Data Prep Kit is available on PyPi for Python 3.10, 3.11 or 3.12. It can be installed using: 

```bash
pip install  'data-prep-toolkit-transforms[ray,all]'
```

The above installs all available transforms and both the python and Ray runtimes. 

NOTE: As of this writing, on linux systems there is an 
[issue](https://github.com/IBM/data-prep-kit/issues/873) 
installing `fasttext` for the `lang_id` transform. 
A workaround is to
[install using conda](quick-start.md#conda).
Alternatively, you may choose to install only the transform(s) of interest (see below).

When installing select transforms, users can specify the name of the transform in the pip command, rather than [all]. For example, use the following command to install only the pdf2parquet transform:
```bash
pip install 'data-prep-toolkit-transforms[pdf2parquet]'
```
As an alternative, installing in a conda environment
can be found
[here](quick-start.md#conda).

### Run a transform at the command line
Here we run the `pdf2parquet` transform on its input data to 
import pdf content into rows of a parquet file.
First, we load some data for the transform to run on using the following python code:
```python
import urllib.request
import shutil
shutil.os.makedirs("input", exist_ok=True)
urllib.request.urlretrieve("https://raw.githubusercontent.com/IBM/data-prep-kit/dev/transforms/language/pdf2parquet/test-data/input/archive1.zip", "input/archive1.zip")
urllib.request.urlretrieve("https://raw.githubusercontent.com/IBM/data-prep-kit/dev/transforms/language/pdf2parquet/test-data/input/redp5110-ch1.pdf", "input/redp5110-ch1.pdf")
```
```shell 
% ls input
archive1.zip		redp5110-ch1.pdf
```

Next we run `pdf2parquet` on the data in the `input` folder.
```shell
python -m dpk_pdf2parquet.transform_python \
    --data_local_config "{ 'input_folder': 'input', 'output_folder': 'output'}" \
    --data_files_to_use "['.pdf', '.zip']" 
```
Parquet files are generated in the designated `output` folder:
```shell
% ls output
archive1.parquet        metadata.json           redp5110-ch1.parquet
```
All transforms are runnable from the command line in the manner above.