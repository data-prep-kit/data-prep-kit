# PDF Processing with Data Prep Kit

Show cases Data Prep Kit capabilities of processing PDFs.

We will demonstrate the following:

- Extracting text from PDF files
- removing duplicates (exact and fuzzy matches)
- accessing document quality and removing documents containing spam words, placeholder content like 'lorem ipsum' ..etc.

**Workflow**

![](images/data-prep-kit-3-workflow.png)

## Setting up Python Environment

The code can be run on either 

1.  Google colab: very easy to run; no local setup needed.
2.  On your local Python environment.  Here is a quick guide.  You can  find instructions for latest version [here](../../../README.md#-getting-started)

```bash
conda create -n data-prep-kit -y python=3.11
conda activate data-prep-kit

# install the following in 'data-prep-kit' environment
cd examples/notebooks/pdf-processing-1
pip3 install  -r requirements.txt

# start jupyter and run the notebooks with this jupyter
jupyter lab
```

## Data Files

PDF files are located in [examples/data-files/pdf-processing-1](../../data-files/pdf-processing-1/)

## Running the code

[python version](pdf_processing_1_python.ipynb)  &nbsp;    [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/IBM/data-prep-kit/blob/dev/examples/notebooks/pdf-processing-1/pdf_processing_1_python.ipynb)

[ray version](pdf_processing_1_ray.ipynb)  &nbsp;   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/IBM/data-prep-kit/blob/dev/examples/notebooks/pdf-processing-1/pdf_processing_1_ray.ipynb)

## Troubleshooting

If you encounter any errors loading libraries, try creating a custom kernel and using it to run the notebooks.

```bash
python -m ipykernel install --user --name=data-prep-kit --display-name "dataprepkit"
# and select this kernel within jupyter notebook
```


