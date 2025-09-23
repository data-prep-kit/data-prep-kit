
## Overall structure

```
pipeline (e.g. pipeline-gwclassication.yaml)
    |
    |-- Task (e.g. task-repo.yaml)
    |    |
    |    |-- git clone github.com/data-prep-kit
    |
    |--Task (e.g. task-docling.yaml)
    |    |
    |    |-- RayJob (e.g. docling2parquet-rayjob.yaml)
    |
    |--Task (e.g. task-ededup.yaml)
    |   |
    |   |-- RayJob (e.g. ededup-rayob.yaml)
    |   
    |-- Task (e.g. task-gwclassification.yaml)
    |   |
    |   |-- Rayjob (e.g. gneissweb_classification-rayjob.yaml)
    |
```    


### Pipeline defines a shared workspace dpk-pipeline-ws mapped to a shared PVC. All tasks have read/write access to PVC

### The Clone task downloads the latest rayjob yaml files from git to the shared PVC

### All subsequent tasks use the shared PVC to retreive the job description 

### Pipeline expects configuration parameters such Bucket name, Inuput folder and output folder for each transform 
```
spec:
  workspaces:
    - name: dpk-pipeline-ws
  params:
    - name: S3_BUCKET_PATH
      description: Bucket name or bucket name and path for the root S3 folder 
      type: string
    - name: HTML_ZIP
      type: string
      description: The input folder for the docling transform
    - name: DOCLING_OUTPUT
      type: string
      description: The output folder for the docling transform
    - name: EDEDUP_INPUT
      type: string
      description: The input folder for the EDedup transform
    - name: EDEDUP_OUTPUT
      type: string
      description: The output folder for the EDedup transform
    - name: GW_MATH_INPUT
      type: string
      description: The input folder for the GW Math Classifier
    - name: GW_MATH_OUTPUT
      type: string
      description: The output folder for the GW Math Classifier
```


### Task run in the specified sequence and require to wait for each other

```
tasks:
    - name: execute-repo-task
      taskRef:
        name: repo
      workspaces:
    - name: execute-docling-task
      taskRef:
        name: docling
      runAfter:
        - execute-repo-task
      workspaces:
      params:
    - name: execute-ededup-task
      taskRef:
        name: ededup
      runAfter:
        - execute-docling-task
      workspaces:
      params:
    - name: execute-gw-classification-task
      taskRef:
        name: gwclassification
      runAfter:
        - execute-ededup-task
      workspaces:
      params:
```