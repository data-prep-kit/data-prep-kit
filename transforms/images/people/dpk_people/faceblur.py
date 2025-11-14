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

import torch
import argparse
from PIL import Image
from PIL import Image, ImageDraw, ImageFilter
from datetime import datetime
import os
import copy
from ultralytics import YOLO
import traceback
import numpy as np
import tarfile
import io
import json
import cv2
from dpk_people.utils import *


class FaceBlur():
    def __init__(self, yolo_modelpath, verbosebit=False):
        # torch.cuda.set_device(1)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print("device = ", device)
        self.model = YOLO(yolo_modelpath)
        self.model.to(device)
        self.verbose = verbosebit

    ## *********** Code for handling object arrays for Face detection and Blur ************

    # if the incoming file is a list of image objects as numpy arrays
    def run_face_blur_objectlist(self, objectlist, threshold, batchsize):
        start_time = datetime.now()
        # same size as the given images
        out_objects = []  # If no people are found, the image is returned as is without modification
        # marks if the results are in Number of Faces or -1 if there is an error. 0 if no faces.

        for maxj in range(0, len(objectlist), batchsize):
            #if (maxj % 100 == 0):
            #    print(maxj, " out of ", len(objectlist), maxj, maxj + batchsize)
            resultperbatch = self.run_face_blur_perobjectbatch(objectlist[maxj:(maxj + batchsize)], threshold)
            out_objects += resultperbatch  # concatenation
        if (len(objectlist) != len(out_objects)):
            print("Mismatch between the inputs and output lengths could be due to other reasons")

        duration = datetime.now() - start_time
        print("Time taken = ", duration)
        return out_objects

    # blur each image result
    def cv2_blur(self, image, result, threshold):
        imgwidth = image.shape[0]
        imgheight = image.shape[1]
        outimg = image.copy()
        bboxes = result.boxes.xyxy.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()
        cls = result.boxes.cls.cpu().numpy()  # classes
        imageMap = {}
        actual_faces = 0
        imageMap["error-message"] = None
        if (len(bboxes) > 0):
            for j in range(len(bboxes)):
                (x1, y1, x2, y2), score, c = bboxes[j], scores[j], cls[j]
                if score >= threshold:  # check here if c is actually a face class
                    x = int(min(x1, x2))
                    y = int(min(y1, y2))
                    xp = int(max(x1, x2))
                    yp = int(max(y1, y2))
                    w = xp - x
                    h = yp - y
                    print(w, h)
                    roi = outimg[y:y + h, x:x + w]
                    roi = cv2.GaussianBlur(roi, (41, 41), 10)
                    outimg[y:y + roi.shape[0], x:x + roi.shape[1]] = roi
                    actual_faces += 1

        imageMap["blurred-im"] = outimg
        imageMap["nfaces"] = actual_faces
        return imageMap

    # use the imagenet blurring process
    def composite_blur(self, image, result, threshold):
        imgwidth = image.shape[0]
        imgheight = image.shape[1]
        img = Image.fromarray(image, 'RGB')
        outimg = img.copy()
        mask = Image.new(mode="L", size=img.size, color="white")
        bboxes = result.boxes.xyxy.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()
        cls = result.boxes.cls.cpu().numpy()  # classes
        imageMap = {}
        actual_faces = 0
        imageMap["error-message"] = None
        if (len(bboxes) > 0):
            max_diagonal = 0
            draw = ImageDraw.Draw(mask)
            for j in range(len(bboxes)):
                (x1, y1, x2, y2), score, c = bboxes[j], scores[j], cls[j]
                # print("Class = ", c)
                if (c > 0):
                    print(c)
                if score >= threshold:  # check here if c is actually a face class

                    diagonal = max(x2 - x1, y2 - y1)
                    max_diagonal = max(max_diagonal, diagonal)
                    maskbbox = [x1 - 0.1 * diagonal, y1 - 0.1 * diagonal, x2 + 0.1 * diagonal, y2 + 0.1 * diagonal]
                    draw.rectangle(maskbbox, fill="black")
                    actual_faces += 1
            blurred_img = outimg.filter(ImageFilter.GaussianBlur(0.1 * max_diagonal))
            blurred_mask = mask.filter(ImageFilter.GaussianBlur(0.1 * max_diagonal))
            outimg = Image.composite(outimg, blurred_img, blurred_mask)
        imageMap["blurred-im"] = np.array(outimg)
        imageMap["nfaces"] = actual_faces
        return imageMap

    # either returns an empty list or a full list of size objectbatchlist
    # empty list is an indication to go into debug mode and examine one image at a time (go to individual mode)
    def run_face_blur_perbatch(self, objectbatchlist, threshold):

        try:
            # print(imagepathlist)
            red = (255, 0, 0)
            resultlist = []
            results = self.model.predict(objectbatchlist, verbose=self.verbose, save=False)
            if (len(results) == (len(objectbatchlist))):
                for i, result in enumerate(results):
                    # imageMap=self.cv2_blur(objectbatchlist[i],result,threshold)
                    imageMap = self.composite_blur(objectbatchlist[i], result, threshold)
                    # print(imageMap)
                    resultlist.append(imageMap)
            return resultlist
        except:
            print(traceback.format_exc())
            return []

    def empty_map(self):
        imageMap = {}
        imageMap["blurred-im"] = None
        imageMap["nfaces"] = 0
        imageMap["error-message"] = "Something went wrong in this image."
        return imageMap

    def run_individual_mode(self, objectpathlist, threshold):
        resultlist = []
        try:
            for i in range(len(objectpathlist)):
                # only one file is passed in
                perimagelist = self.run_face_blur_perbatch([objectpathlist[i]], threshold)
                if (len(perimagelist) != 1):
                    imageMap = self.empty_map()
                    resultlist.append(imageMap)
                else:
                    resultlist.append(perimagelist[0])
        except:
            # if for any reason the face detector fails, return an error_message
            imageMap = self.empty_map()
            resultlist.append(imageMap)
        return resultlist

    def run_face_blur_perobjectbatch(self, objectpathlist, threshold):
        # first run on the entire batch. If it succeeds, we are done
        resultlist = self.run_face_blur_perbatch(objectpathlist, threshold)
        if (len(resultlist) == len(objectpathlist)):
            # no need to recurse, return result
            return resultlist
        else:
            # no need to recurse even here since the list is small and we can manually check
            return self.run_individual_mode(objectpathlist, threshold)



