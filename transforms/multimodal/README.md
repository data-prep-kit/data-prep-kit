# Initial Multimodal prototype transform 

Currently (as of 8/1/2024) the proto_transform_local.py can be run after editing to point at a parquet file downloaded 
from box, [here](https://ibm.ent.box.com/s/2cqlu8y4si34mw357t564l4h0trifk7y).

Before running, you will need to create the virtual environment using `make venv`.  See `make help` for other goodies.


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



