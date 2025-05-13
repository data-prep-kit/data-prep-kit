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
import copy
from PIL import Image
import numpy as np


def make_object_list(imagelistfile, imgdir):
    imagefilepaths = read_imagelist_contents(imagelistfile)
    return get_image_arrayswithdir(imagefilepaths, imgdir)


def read_imagelist_contents(imagelistpath):
    imagelist = []
    with open(imagelistpath, "r+") as file:
        for line in file:
            # Remove the newline character at the end of the line
            line = line.strip()
            # Append the line to the list
            imagelist.append(line)
    return imagelist


def get_image_array(fullpath):
    imgloaded = copy.deepcopy(Image.open(fullpath))  # check if this is needed in parallel mode to close out the readers
    imgarray = np.asarray(imgloaded)
    # return imgarray
    if (len(imgarray.shape) == 2):
        # gray scale image
        rgb_img = np.stack((imgarray,) * 3, axis=-1)
        return rgb_img
    else:
        return imgarray


# from a list of images and an image dir
def get_image_arrayswithdir(imagelist, imgdir):
    validimages = []
    validimagenames = []
    invalidimagenames = []
    i = 0
    for k in range(len(imagelist)):
        img = imagelist[k]

        #if (k % 100 == 0):
        #    print(k, img)

        fullpath = imgdir + "/" + img
        imgarray = get_image_array(fullpath)
        # imgloaded = copy.deepcopy(Image.open(fullpath))
        # imgarray=np.asarray(imgloaded)
        validimages.append(imgarray)
        validimagenames.append(img)

    return validimagenames, validimages


def get_image_arrays(imagelist):
    validimages = []
    validimagenames = []
    invalidimagenames = []
    i = 0
    for k in range(len(imagelist)):
        img = imagelist[k]

        #if (k % 100 == 0):
        #    print(k, img)

        imgloaded = copy.deepcopy(Image.open(img))
        imgarray = np.asarray(imgloaded)
        validimages.append(imgarray)
        validimagenames.append(img)

    return validimagenames, validimages