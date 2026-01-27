## Multimedia/Multimodal Transforms
There is an initial set of 3 transforms: `Faces`, `People` and `NSFW`.
## Faces 

This transform detects people and faces in the image. It provides a pre-trained model designed specifically for face detection.


### User-Configurable Parameters

The table below provides the parameters that users can adjust to control the behavior of the transform:

| Parameter    | Default | Description                                                                                                           |
|--------------|------|-----------------------------------------------------------------------------------------------------------------------|
| `model_path`      |`models/yolov8n-face.pt`    | The model to use for detecting faces. |
                                                            

### output

| Annotation    | Type | Description                                                                                                           |
|--------------|------|-----------------------------------------------------------------------------------------------------------------------|
| `nfaces`       | int  | The count of number of faces identified. |


## People

This transform identifies the number of faces in the image and enables the blurring of faces.


### User-Configurable Parameters

The table below provides the parameters that users can adjust to control the behavior of the transform:

| Parameter    | Default                         | Description                                                                                                        |
|--------------|---------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `mode`       | `blur`                          | Controls whether it is counting people or faces or detects and blurs faces. Allowed values are `count` and `blur`. |
| `threshold`  | `0.6`                           | The minimum score required to declare a face or people detection.                                                  |
| `batch_size` | `50`                            | The size of the batch of images to provide to the model.                                                           |
| `model_path` | `models/yolov8m-200e.pt` if `mode` is `blur` and `models/yolov8m-seg.pt` if `mode` is `count` | The models to use for detecting faces and blurring them or counting faces.                                                                  |

### output

| Annotation    | Type | Description                                                                                                           |
|--------------|------|-----------------------------------------------------------------------------------------------------------------------|
| `nfaces`       | int  | The count of number of faces blurred. |
| `blurred_images`       | list[byte] | Contains the modified image(s) with faces blurred when faces are detected.  List elements are None when the corresponding image did not contain any faces.| 

## NSFW

This transform provides a score for `Not Safe For Work` type of content. It is using the [image-classification Huggingface pipeline](https://huggingface.co/docs/transformers/v4.44.0/en/main_classes/pipelines#transformers.ImageClassificationPipeline) to 
detect not safe for work (NSFW) content.

The transform expects a model which is predicting for each image two classes with each class having a score from 0 to 1.
One class identifies the probability of being a normal image (i.e., called `normal`), and the other class identifies the probability of being an NSFW image (i.e., called `nsfw`).
The actual name of the classes can be specified as arguments (see below).


### User-Configurable Parameters

The transform can be initialized with the following parameters:

| Parameter  | Default  | Description  |
|------------|----------|--------------|
| `model_name`    | `Falconsai/nsfw_image_detection` | The HF model to use for encoding the text. |
| `normal_class`    | `normal` | Name of the predicted class for normal content. |
| `nsfw_class`    | `nsfw` | Name of the predicted class for NSFW content. |

When invoking the CLI, the parameters must be set as `--nsfw_<name>`, e.g., `--nsfw_model_name=Falconsai/nsfw_image_detection`.

### Output

For each row (which may have multiple images), the transform counts how many images have an `nsfw` probability higher than the `normal` one.
For example, if two out of five images contain nsfw content, the output will be `nsfw=2`.

```jsonc
{
    "nsfw": "number",  // number of images detected to be NSFW
}
```



