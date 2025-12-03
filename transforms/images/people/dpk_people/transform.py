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

from argparse import Namespace, ArgumentParser

from data_processing.multimodal.abstract_transform import (
    AbstractMultimodalTransform,
    AbstractMultimodalTransformConfiguration,
)
from data_processing.utils import CLIArgumentProvider

from data_processing.multimodal.util import JsonUtils
from dpk_people.peopledetect import PeopleDetect
from dpk_people.faceblur import *
import os

from data_processing.utils import get_dpk_logger
logger = get_dpk_logger()


shortname = "people"
cli_prefix = f"{shortname}_"
model_path_key = "model_path"

count_model_path_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/yolov8m-seg.pt"))
blur_model_path_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/yolov8m_200e.pt"))
model_path_default = blur_model_path_default    # to match default mode = blur
model_path_cli_key = f"{cli_prefix}{model_path_key}"

mode_key = "mode"
#mode_default = "count" # or blur
mode_default = "blur"
mode_cli_key = f"{cli_prefix}{mode_key}"

threshold_key = "threshold"
threshold_default = 0.6
threshold_cli_key = f"{cli_prefix}{threshold_key}"

batch_size_key = "batch_size"
batch_size_default = 50
batch_size_cli_key = f"{cli_prefix}{batch_size_key}"

class PeopleTransform(AbstractMultimodalTransform):
    def __init__(self, config: dict[str,Any]):
        super().__init__(config)
        self.mode = config.get(mode_key,mode_default)
        self.model_path = config.get(model_path_key, None)
        if self.model_path is None:
            if self.mode == "blur":
                self.model_path = blur_model_path_default
            else:
                self.model_path = count_model_path_default
        self.threshold = config.get(threshold_key,threshold_default)
        self.batch_size = config.get(batch_size_key,batch_size_default)

        if "count" in self.mode:
            self.pdetect = PeopleDetect(self.model_path)
        else:
            self.fb = FaceBlur(self.model_path)



    def _merge_annotations(self, merged: dict, addend: dict, past_merge_count: int) -> dict:
        """
        Merges the two dictionaries of annotations from across multiple images in the same row.
        """
        new_dict = {}

        if "count" in self.mode:
            for key, value in merged.items():
                 new_dict[key] = value + addend[key]
        else:
            for key, value in merged.items():
                if key == 'blurred_images':
                    assert isinstance(value, list)
                    assert isinstance(addend[key], list)
                    copy = merged[key].copy()
                    copy.extend(addend[key])
                    extended = copy
                    #self.logger.info(f"{value=}, {addend[key]=}, {copy=}, {extended=}")
                    new_dict[key] = extended
                else:
                    new_dict[key] = value + addend[key]

        return new_dict   # TODO: needs implementation


    def _get_dummy_annotations(self):
        """
        Provides the definition of the annotations to be assigned to the dummy/missing images.
        """
        if "count" in self.mode:
            return {"people": 0}
        else:
            return {"blurred_images": [], "nfaces": 0}

    def _annotate_images(self, image_batch: list[bytes], image_paths:list[str]) -> list[dict]:
        if "count" in self.mode:
            return self._count_people(image_batch)
        else:
            return self._blur_people(image_batch, image_paths)

    def _blur_people(self, image_batch: list[bytes], image_paths:list[str]) -> list[dict]:

        # Use self.model to annotate all images.

        blur_annotations_batch = []
        im_list = []

        format_list = []
        ct = 0
        for image in image_batch:
            # An appended set of columns for this image.
            image  = JsonUtils.convert_bytes_to_image(image)
            #imgarray = image #np.asarray(image)
            imgarray = np.asarray(image)
            im_list.append(imgarray)
            fmt = image.format
            if fmt is None:
                impth = image_paths[ct]
                tokens = impth.split(".")
                fmt = tokens[-1].lower()
                if fmt == "jpg":
                    fmt = 'jpeg'
                #print('None converted to ', f"{fmt=}")
            #print(image_paths[ct])

            #print('using ', f"{fmt=}")
            format_list.append(fmt)
            ct += 1

        res_list = self.fb.run_face_blur_objectlist(im_list, self.threshold, self.batch_size)
        logger.debug(f"{res_list}")
        assert len(res_list)==len(im_list)

        ct = 0
        for result in res_list:
            blurim = result['blurred-im']
            nfaces = result['nfaces']

            if blurim is None:  # error in annotation
                # blurim = Image.fromarray(blurim)
                blur_annotations = None
                #raise RuntimeError("some image failed") #this is temporary till we fix the superclass
            else:
                if nfaces == 0:  # no error but no faces
                    blurim = None
                else:
                    #blurim = JsonUtils.convert_PILimage_to_image(blurim, format_list[ct])
                    blurim = JsonUtils.convert_numpy_to_image(blurim, format_list[ct])
                    #blurim = blurim.tobytes()

                blur_annotations = {"blurred_images": [blurim], "nfaces": nfaces}

            ct += 1

            blur_annotations_batch.append(blur_annotations)

        return blur_annotations_batch

    def _count_people(self, image_batch: list[bytes]) -> list[dict]:

        annotations_batch = []
        # Use self.model to annotate all images.

        annotations = {}
        im_list = []

        for image in image_batch:
            # An appended set of columns for this image.

            image = JsonUtils.convert_bytes_to_image(image)
            imgarray = image #np.asarray(image)
            im_list.append(imgarray)

        #print(f"{len(im_list)=}")
        #results = self.model(image)
        confidence = 0.5
        verbose = False
        batchsize = 200
        people_count, nonpeople_count, res_list = self.pdetect.run_people_detector_objectlist(im_list, confidence, batchsize, verbose)
        #result = self.pdetect.run_people_detector_object(image, confidence, verbose)
        #print(f"{len(im_list) = }")
        #print(f"{len(res_list) = }")

        for result in res_list:
           if result == True:
             image_annotations = {"people": 1}
           else:
             image_annotations = {"people": 0}

           annotations_batch.append(image_annotations)

        #print(f"{res_list=}")
        #print(f"{len(res_list)=}")
        #print(f"{annotations_batch=}")

        return annotations_batch

class PeopleTransformConfiguration(AbstractMultimodalTransformConfiguration):

    def __init__(self):
        super().__init__("people", PeopleTransform)

    def add_input_params(self, parser: ArgumentParser) -> None:
        """
        Add Transform-specific arguments to the given  parser.
        This will be included in a dictionary used to initialize the NOOPTransform.
        By convention a common prefix should be used for all transform-specific CLI args
        (e.g, noop_, pii_, etc.)
        """
        parser.add_argument(
            f"--{model_path_cli_key}",
            type=str,
            default=None,   # Let init() set the default based on mode, if not provided here.
            help=f"The path to the people model to load. Default {model_path_default}.",
        )
        parser.add_argument(
            f"--{mode_cli_key}",
            type=str,
            default=mode_default,
            help=f"Mode of operation, one of 'blur' or 'count'. Default is {mode_default}"
        )
        parser.add_argument(
            f"--{threshold_cli_key}",
            type=float,
            default=threshold_default,
            help=f"Threshold to use when detecting faces/people. Default is {threshold_default}"
        )
        parser.add_argument(
            f"--{batch_size_cli_key}",
            type=int,
            default=batch_size_default,
            help=f"Batch size to use when processing images.  Default is {batch_size_default}"
        )

    def apply_input_params(self, args: Namespace) -> bool:
        """
        Validate and apply the arguments that have been parsed
        :param args: user defined arguments.
        :return: True, if validate pass or False otherwise
        """
        captured = CLIArgumentProvider.capture_parameters(args, cli_prefix, False)
        self.params = self.params | captured
        self.logger.info(f"parameters are : {self.params}")
        return True