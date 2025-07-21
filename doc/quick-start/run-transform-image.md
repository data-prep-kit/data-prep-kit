# Running a Transform Image

Here we address a simple use case of applying a single transform to a 
set of parquet files.
We will build or use one of the pre-built docker images from the repository to process the data.
Additionally, what follows uses the 
[python runtime](../../data-processing-lib/doc/python-runtime.md)
image, but the examples below should also work for the
[ray](../../data-processing-lib/doc/ray-runtime.md)
or
[spark](../../data-processing-lib/doc/spark-runtime.md)
runtime images (`-ray` or `-spark` image name suffix instead of `-python`).

### Building an image
You may build the transform locally in the repository, for example,
```shell
cd transforms/universal/resize
make image-python
docker images | grep resize
```
produces
```
resize-python                                                                   latest            bac595b2751f   28 minutes ago     598MB
quay.io/dataprep1/data-prep-kit/resize-python                                   latest            bac595b2751f   28 minutes ago     598MB
...
```
Or, you can use the pre-built images (latest, or 1.0.0 or later tags) 
on quay.io found at [https://quay.io/user/dataprep1](https://quay.io/user/dataprep1).

### Local Data - Python Runtime
To use an image to process local data we will mount the host
input and output directories into the image.  Any mount
point can be used, but we will use `/input` and `/output`.

To process the data in the `./test-data/input` directory and write it
to the `./output` directory, we mount these directories into
the image at the above mount points.
For example, using the locally built `resize` transform:

```shell
docker run --rm \
-v ./test-data/input:/input \
-v ./output:/output \ 
resize-python:latest \
python -m dpk_resize.runtime \
--resize_max_rows_per_table=125 \ 
--data_local_config "{'input_folder'  : '/input', 'output_folder' : '/output'}" 

```
Please note how a transform-specific parameter for `resize` such as `max_rows_per_table` is used in the example above.  

To run the quay.io located transform instead, substitute 

`resize-python:latest` with `quay.io/dataprep1/data-prep-kit/resize:latest` in this example. 

### Local Data - Ray Runtime

To use the ray runtime, we must first make the ray image using `make image-ray` and then use `resize-ray:latest` or `quay.io/dataprep1/data-prep-kit/resize-ray:latest` in place of `resize-python:latest` in the example above. 

This is functionally equivalent to the python-runtime, but additional
configuration parameters can be provided (see the 
[launcher args](../../data-processing-lib/doc/launcher-options.md))
for details.

