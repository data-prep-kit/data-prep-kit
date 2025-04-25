# Initial Multimodal prototype transform 

Currently (as of 8/1/2024) the proto_transform_local.py can be run after editing to point at a parquet file downloaded 
from box, [here](https://ibm.ent.box.com/s/2cqlu8y4si34mw357t564l4h0trifk7y).

Before running, you will need to create the virtual environment using `make venv`.  See `make help` for other goodies.


## Json2Parquet (aka j2p)
This transform converts a single .json (or .jsonl) file to 1 or more .parquet files.
The input json contains a list of dictionaries.
Each dictionary has the following keys: 
* `id` - a string or integer or json `null`.
* `image` - either
  1. a list of strings.  each string is a path to an image file.  This may be an empty list.
paths may be absolute or relative.
  2. a single string.  a path to an image file. may also be an empty string "".
  3. a json `null`
* `converstations` - a list of dictionaries representing a conversation about the images.
Each dictionary contains the following keys:
    * `from` - generally human, gpt, or other
    * `value` - a natural language phrase, either a question or answer.
    
An example, file can be found [here](test-data/j2p/input/sample.jsonl)

The [j2p transform](src/j2p/j2p_transform.py) reads the json(l) file and creates a pyarrow Table
n which each top level dictionary in the json creates a row in the table.  
The table created, has the following schema/columns:
* `id` - a string containing the original id.  integer ids in the source are converted to strings.  Python `None` if field has a json `null`.
* `orig_image_fpaths` - a list of strings containing the original value of the `image` field in the json record.  Never python `None`, but an empty list is allowed.
* `image_bins` - a list of the image bytes read from the paths in the source `image` field (or parquet file's `orig_image_fpaths`).
Never None, but an empty list is allowed.  Same length as `orig_image_fpaths`.
* `source` - string. None if not present in json.
* `contents` - a concatenation of the `conversation.value` fields.
* `fixed_image_fpaths` - the relative path(s) to use when writing out the corresponding image(s) (from `image_bins` or other image-containing column).
* `index` - 0-based index of row corresponding to input json file. Same length as `orig_image_fpaths`.
* `absolute_image_paths` - source of image(s) when read into the parquet file. Same length as `orig_image_fpaths`.
* `orig_json_path` -  absolute path to the json source file. (As reported by DataAccess, w/o s3:// when on cos).

When converting a json dictionary of values, if there is any problem reading
the referenced images, the dictionary will be dropped and not included in the
table.

### J2P Parameters

| Parameter                      | Default              | Description                                                                                                  |
|--------------------------------|----------------------|--------------------------------------------------------------------------------------------------------------|
| `image_path_prefix`            | None                 | The common path expected on image file paths                                                                 |
| `image_path_prefix_alias`      | None                 | The common path where the images will actually be read from by replacing the common prefix with this prefix. |
| `parquet_size_limit`           | `209715200` (200 mb) | The target size for the resulting parquet files.                                                             |
| `secondary_data_access_config` | None                 | Enables the writing of the parquet to an alternate COS/S3 endpoint.  Example, { 'access_key': '...', 'secret_key': '...', 'url': 'https://s3.us-east....', 'region': 'us-east' 'input_folder': 'some/bucket', 'output_folder': 'some/other/bucket' }                               |

## PeopleTransform 
Allows the annotation of rows with information about people and faces in the image.
It also enables the blurring of faces.

If any image in the list of images within a row causes an exception in processing,
the row is dropped from the table.


### Annotations 

It adds the following annotations for `count` mode.

| Parameter    | Type | Description                                                                                                           |
|--------------|------|-----------------------------------------------------------------------------------------------------------------------|
| `people`       | int  | The count of people identified. |

It adds the following annotations for `blur` mode.

| Parameter    | Type | Description                                                                                                           |
|--------------|------|-----------------------------------------------------------------------------------------------------------------------|
| `nfaces`       | int  | The count of number of faces identified. |
| `blurred_images`       | list[byte] | Contains the modified image(s) with faces blurred when faces are detected.  List elements are None when the corresponding image did not contain any faces. 

### Parameters

| Parameter    | Default                         | Description                                                                                                        |
|--------------|---------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `mode`       | `blur`                          | Controls whether it is counting people or faces or detects and blurs faces. Allowed values are `count` and `blur`. |
| `threshold`  | `0.6`                           | The minimum score required to declare a face or people detection.                                                  |
| `batch_size` | `50`                            | The size of the batch of images to provide to the model.                                                           |
| `model_path` | `models/"models/yolov8m-seg.pt` | The model to use for detecting faces or people.                                                                    |

## NsfwTransform 

The transform is using the [image-classification Huggingface pipeline](https://huggingface.co/docs/transformers/v4.44.0/en/main_classes/pipelines#transformers.ImageClassificationPipeline) to i
detect not safe for work (NSFW) content.

The transform expects a model which is predicting on each image two classes with each a score from 0 to 1.
One class identifies the probability of being a normal image (e.g. called `normal`), the other class the probability of being a NSFW image (e.g. called `nsfw`).
The actual name of the classes can be specified as argument (see below).


### Annotations 

For each row (which may have multiple images), the transform counts how many images have a `nsfw` probability higher than the `normal` one.
For example, if two images on 5 contain nsfw content, the output will be `nsfw=2`.

```jsonc
{
    "nsfw": "number",  // number of images detected to be NSFW
}
```


### Parameters

The transform can be initialized with the following parameters.

| Parameter  | Default  | Description  |
|------------|----------|--------------|
| `model_name`    | `Falconsai/nsfw_image_detection` | The HF model to use for encoding the text. |
| `normal_class`    | `normal` | Name of the predicted class for normal content. |
| `nsfw_class`    | `nsfw` | Name of the predicted class for NSFW content. |

When invoking the CLI, the parameters must be set as `--nsfw_<name>`, e.g. `--nsfw_model_name=Falconsai/nsfw_image_detection`.

## Parquet2Json (aka p2j)
This converts each parquet into a json(l) file and optionally writes out the images.
The output json(l) format includes all the keys of the original input.

Running this transform on multiple .parquet files, will produce multiple json files.
In this case, it is likely preferred to write jsonl so that they can then all be
`cat`ed together after the run to produce a single jsonl file.

### JSON Format

Each parquet file creates a single json or jsonl file always containing the following:

* `id` - a string as create/copied from the json read by j2p
* `conversations` - a dictionary as created/copied from the json read by j2p
* `images`  
    * if not writing images, this is the original value copied from the json read by j2p.
    * if writing images, then this is a path to the images written relative to the output directory of the Data Access
object (and where the json files are written).

Additional fields can be included by using the `exported_columns` configuration
(soon `additional_columns`) configuration.

### Writing images

When writing out the image, the `fixed_image_paths` are used to write the image
files relative to the output of the destination json(l) files.
If `blurred_images` column is present 
(as included in the `exported_columns` list), 
those images will be written out.  
If any element of the `blurred_images` list is None, then there were no
faces to be blurred/modified and the original image from `image_bins` is used.

### Parameters

| Parameter  | Default  | Description                                                                                                                          |
|------------|----------|--------------------------------------------------------------------------------------------------------------------------------------|
| `as_jsonl`    | `True`| Controls format and extension of json files written.                                                                                 | 
| `export_columns`    | ` ['id', 'orig_image_fpaths', 'conversations', 'fixed_image_fpaths', 'source']`| Names the columns to be included in the output json.                                                                                 |
| `write_images`      | `False`|                                                                                                                                      | 
| `write_image_path`    | `./`| Path to write image file to.  If relative path, it is relative to Data Access output directory where the json files will be written. | 


### Next release of p2j
We plan to change the parameters (`export_columns` -> `additional_columns`) as follows:

| Parameter            | Default | Description                                                                                                                                           |
|----------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| `as_jsonl`           | `True`  | Controls format and extension of json files written. json if False, json if True.                                                                     | 
| `additional_columns` | ` []`   | Names of additional columns to be included in the output json.  This does not include any image-containing columns.                                   |
| `image_column`       | ""      | If set to a non-empty string, then this implies that images from the named column are to be written to the directory specified by `write_image_path`. | 
| `write_image_path`   | `./`    | Path to write image file to.  If relative path, it is relative to Data Access output directory where the json files will be written.                  | 

It is implied that `id`, `conversations` and `images` fields are ALWAYS written out
with the ability to include additional columns if desired.



