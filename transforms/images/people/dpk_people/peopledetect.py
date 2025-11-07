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
from datetime import datetime
import os
import copy
from ultralytics import YOLO
import traceback
import numpy as np
import tarfile
import io
class PeopleDetect():
    def __init__(self,yolo_modelpath):
        #torch.cuda.set_device(1)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO(yolo_modelpath)
        self.model.to(device)
        
        
    ## *********** Code for handling object arrays for people detector ************
    
    def make_object_list(self,imagelistfile,imgdir):
        imagefilepaths=self.read_imagelist_contents(imagelistfile)
        return self.get_image_arrays(imagefilepaths,imgdir)
    
    def get_image_array(self,fullpath):
        
        #fullpath=imgdir+"/"+imgname
        imgloaded = copy.deepcopy(Image.open(fullpath)) #check if this is needed in parallel mode to close out the readers
        imgarray=np.asarray(imgloaded)
        return imgarray
    
    def get_image_arrays(self,imagelist,imgdir):
        validimages=[]
        validimagenames=[]
        invalidimagenames=[]
        i=0
        for k in range(len(imagelist)):
            img=imagelist[k]
           
            if (k%100==0):
                print(k,img)

            fullpath=imgdir+"/"+img
            imgloaded = copy.deepcopy(Image.open(fullpath))
            imgarray=np.asarray(imgloaded)
            validimages.append(imgarray)
            validimagenames.append(img)
    
        return validimagenames,validimages
    
    #if the incoming file is a list of image objects as numpy arrays
    def run_people_detector_objectlist(self,objectlist,confscore,batchsize,chatty=False):
        start_time=datetime.now()
        #same size as the given images
        mark_images=[]
       
        
        for maxj in range(0,len(objectlist),batchsize):
            #if (maxj%100==0):
            #    print(maxj, " out of ", len(objectlist))
            #resultperbatch=self.run_people_detector_perobjectbatch(objectlist[maxj:(maxj+1)*batchsize],confscore,chatty)
            resultperbatch = self.run_people_detector_perobjectbatch(objectlist[maxj:(maxj + batchsize)], confscore, chatty)
            mark_images+=resultperbatch
        people_count=mark_images.count(True)
        nonpeople_count=mark_images.count(False)
        #print("Number of people images = ", people_count)
        #print("Number of non-people images = ", nonpeople_count)
        duration = datetime.now()-start_time
        #print("Time taken = ",duration)
        return people_count,nonpeople_count,mark_images
    
    def run_people_detector_perobjectbatch(self,objectpathlist,confscore,chatty=False):
        resultlist=[]
        #try:
       # print(imagepathlist)
        results = self.model(objectpathlist,verbose=chatty,conf=confscore)  # return a list of Results objects
        index=0
        #one result per image in the list
        for result in results:
           # masks = result.masks.data #if segmentation output is desired
            boxes = result.boxes.data
            clss = boxes[:, 5]
            # get indices of results where class is 0 (people in COCO)
            people_indices = torch.where(clss == 0)
            if (len(people_indices[0])>0):
                resultlist.append(True)
            else:
                resultlist.append(False)
        #except:
        #     print(traceback.format_exc())
         
        return resultlist
    
    def run_people_detector_object(self,object,confscore,chatty=False):
        
        try: 
            #start_time=datetime.now()
            results = self.model(object,verbose=chatty,conf=confscore)  # return a list of Results objects
            index=0
            #single result since there is only one image
            for result in results:
               # masks = result.masks.data
                boxes = result.boxes.data
                clss = boxes[:, 5]
                # get indices of results where class is 0 (people in COCO)
                people_indices = torch.where(clss == 0)
                if (len(people_indices[0])>0):
                    return True
            #duration = datetime.now()-start_time
           # print("Time taken = ",duration)
        except:
             print(traceback.format_exc())
        
        return False
    
   #************** Bulk processing ************
    def update_result_file(self,outfile,resultperbatch,imagefilelist):
        fop=open(outfile,'a')
        for i in range(len(imagefilelist)):
            fop.write(imagefilelist[i]+"\t"+str(resultperbatch[i])+"\n")
        fop.close()
    #do this only if they have the same shape
   
    #this runs the detector on an entire directory, collecting batchsize of files at a time and appends to a file
    #since the directory could have a large list of files 
    def run_people_detector_bulk(self,imgdir,resultfile,confscore,batchsize,chatty=False):
       # print("batch size = ", batchsize)
        start_time=datetime.now()
        countfiles=0
        people_count=0
        nonpeople_count=0
        total_files=0
        imagefilelist=[]
        cumulativeresult=[]
        for root, dirs, files in os.walk(imgdir, topdown=False, onerror=None, followlinks=True):
            for filename in files:
                #add support for other formats if necessary based on the detector
                if (filename != '.DS_Store') and ((filename.endswith('.jpg')) or (filename.endswith('.png'))):
                    
                    
                    imagepath= os.path.join(root, filename)
                    if (total_files%batchsize==0):
                        print("Processing file #", total_files)
                        if (len(imagefilelist)>0):
                            resultperbatch=self.run_people_detector_perimagebatch(imagefilelist,confscore,chatty)
                            cumulativeresult+=resultperbatch
                            #print(len(imagefilelist),len(resultperbatch))
                            self.update_result_file(resultfile,resultperbatch,imagefilelist)
                            people_count+=resultperbatch.count(True)
                            nonpeople_count+=resultperbatch.count(False) #if some failed
                        imagefilelist=[] #time to start a new one
                    imagefilelist.append(imagepath)
                    total_files+=1
        if (len(imagefilelist)>0):
            #give the last run
            print("Processing last run")              
            resultperbatch=self.run_people_detector_perimagebatch(imagefilelist,confscore,chatty)
            self.update_result_file(resultfile,resultperbatch,imagefilelist)
            cumulativeresult+=resultperbatch
            people_count+=resultperbatch.count(True)
            nonpeople_count+=resultperbatch.count(False) 
        print("Total number of images found to have people = ", people_count, " out of ",total_files)
        print("Total number of images not found with people = ", nonpeople_count, " out of ",total_files)
        duration = datetime.now()-start_time
        print("Time taken = ",duration)
       # print("Cumulative result= ", cumulativeresult)
        return people_count,nonpeople_count,cumulativeresult
    
     #************** Processing image file lists ************
    #meant for small image lists, for very large, read from the directory
    def read_imagelist_contents(self,imagelistpath):
        imagelist=[]
        with open(imagelistpath, "r+") as file:
            for line in file:
                # Remove the newline character at the end of the line
                line = line.strip()
                # Append the line to the list
                imagelist.append(line)
        return imagelist
        
    #expects a list of images to process and topdir where they are located. Returns marks on the images in the same order
    #marks them as True if they contain people
    def run_people_detector_imagelist(self,imagelistpath,topdir,confscore,batchsize,chatty=False):
        start_time=datetime.now()
        imagelist=self.read_imagelist_contents(imagelistpath)
        mark_images=[]
        pathlist=[]
        for i in range(len(imagelist)):
            imagepath=topdir+imagelist[i]
            pathlist.append(imagepath)
        for maxj in range(0,len(pathlist),batchsize):
            if (maxj%100==0):
                print(maxj, " out of ", len(pathlist))
            resultperbatch=self.run_people_detector_perimagebatch(pathlist[maxj:(maxj+1)*batchsize],confscore,chatty)
            mark_images+=resultperbatch
        people_count=mark_images.count(True)
        nonpeople_count=mark_images.count(False)
        print("Number of people images = ", people_count)
        print("Number of non-people images = ", nonpeople_count)
        duration = datetime.now()-start_time
        print("Time taken = ",duration)
        return people_count,nonpeople_count,mark_images
    
    def run_people_detector_perimagebatch(self,imagepathlist,confscore,chatty=False):
        resultlist=[]
        try: 
           # print(imagepathlist)
            results = self.model(imagepathlist,verbose=chatty,conf=confscore)  # return a list of Results objects
            index=0
            #one result per image in the list
            for result in results:
               # masks = result.masks.data #if segmentation output is desired
                boxes = result.boxes.data
              #  print("bbox shape = ",boxes.shape)
                clss = boxes[:, 5]
               # print("class = ",clss)
              #  print("class shape = ",clss.shape)

                # get indices of results where class is 0 (people in COCO)
                people_indices = torch.where(clss == 0)
                if (len(people_indices[0])>0):
                    resultlist.append(True)
                else:
                    resultlist.append(False)
        except:
            print(traceback.format_exc())
            #print("File ", len(imagepathlist), " or something went wrong")
           
         
        return resultlist
    
    ## ********** Run per image file.  **************
    
    #returns true or false which can be reused in json insertion into relevant column for this image
    def run_people_detector_perimage(self,imagepath,confscore,chatty=False):
        
        try: 
           # start_time=datetime.now()
            results = self.model(imagepath,verbose=chatty,conf=confscore)  # return a list of Results objects
            index=0
            #single result since there is only one image
            for result in results:
               # masks = result.masks.data
                boxes = result.boxes.data
                clss = boxes[:, 5]
                # get indices of results where class is 0 (people in COCO)
                people_indices = torch.where(clss == 0)
                if (len(people_indices[0])>0):
                    return True
           # duration = datetime.now()-start_time
            #print("Time taken = ",duration)
        except:
             print(traceback.format_exc())
        
        return False
    
    #if an image directory is given. imagedir ends with /
    def run_people_detector_perimagedir(self,imagefile,imagedir,confscore,chatty=False):
        #start_time=datetime.now()
        try: 
            imagepath=imagedir+imagefile
            results = self.model(imagepath,verbose=chatty,conf=confscore)  # return a list of Results objects
            index=0
            #single result since there is only one image
            for result in results:
               # masks = result.masks.data
                boxes = result.boxes.data
                clss = boxes[:, 5]
                # get indices of results where class is 0 (people in COCO)
                people_indices = torch.where(clss == 0)
                if (len(people_indices[0])>0):
                    return True
        except:
             print(traceback.format_exc())
       # duration = datetime.now()-start_time
       # print("Time taken = ",duration)
        return False
    
    ##******** Run on tar images and tar files ******************
    
    def run_people_detector_tarfiles(self,tardir,outdir,confscore):
         for root, dirs, files in os.walk(tardir, topdown=False, onerror=None, followlinks=True):
                for filename in files:
                    if (".tar" in filename):
                        tarpath=os.path.join(root, filename)
                        self.process_tart(tarpath,outdir,confscore)
      
    
    def process_tar(self,tarfilename,outdir,confscore):
        recordfile=outdir+tarfilename.replace(".tar",".txt")
        fop=open(recordfile,'a')

        with tarfile.open(tarfilename, 'r') as tf:
       # my_tarfile = tarfile.open(tarfilename)
            index = tf.getnames()
            count=0
            count_nonpeople=0
            for i in range(len(index)):
                if (i%1000==0):
                    print(i,"/",len(index))
                dirorfilename=index[i]
            #print(dirorfilename)
                if (".jpg" in dirorfilename):
                    tarinfo = tf.getmember( dirorfilename)
                    image = tf.extractfile(tarinfo)
                    image = Image.open(image)
                   # print(type(image))
                    if (not (pdetect.run_people_detector_object(image,confscore,False))):
                        count_nonpeople+=1
                        fop.write(dirorfilename+"\n")
                        #print(dirorfilename)
                 #   with my_tarfile.extractfile(dirorfilename) as binary, io.TextIOWrapper(binary) as image:
                       # print(type(img),img.shape)
                        #image = image.read()

                       # image = Image.open(image)

                    #result=pdetect.run_people_detector_perimagedir(dirorfilename,imagedir,confscore,chatty=False):
                    count+=1
            print(len(index),count,count_nonpeople,count_nonpeople/count)
            fop.close()
    
    

def parsearguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('--model', type=str, default='yolov8m-seg.pt', help="path to the model file")
        parser.add_argument('--mode', type=str, default='image', help="Mode in which to operate: Choices are: 'image', 'list','bulk','tar'")
       # group1 = parser.add_argument_group(title='Group of optional arguments')
        parser.add_argument('--topdir', default='.',type=str,help='image directory name ends with /')
        parser.add_argument('--confidence', default=0.5, type=float,help="confidence score for persons")
        parser.add_argument('--batchsize', default=100, type=int,help='batch size for bulk processing')
        parser.add_argument('--verbose', default=False, type=bool,help="Whether detailed output is needed")
        parser.add_argument('--name', type=str, help="Name of image file if image file, else imagelist, else directory, etc. or output file in bulk mode")
        args = parser.parse_args()
        return args
#usage:
#python peopledetect.py --mode='bulk' --topdir='/gpfs/fs0/data/BioInspiredMems/datasets/flickr30k/test/' --name='out.txt' --batchsize=5 --verbose=True
#python peopledetect.py --mode='list' --topdir='/gpfs/fs0/data/BioInspiredMems/datasets/flickr30k/flickr30k-images/' --name='imagelist.txt' --batchsize=5
#python peopledetect.py --mode='image' --name='/gpfs/fs0/data/BioInspiredMems/datasets/flickr30k/flickr30k-images/2326133103.jpg'
if __name__ == "__main__":
    args = parsearguments()
    #print(args)
    pdetect=PeopleDetect(args.model)
    if args.mode=='image':
        if (args.topdir==None):
            #boolean result
            people_present=pdetect.run_people_detector_perimage(args.name,args.confidence,args.verbose)
           # print(people_present)
        else:
            people_present=pdetect.run_people_detector_perimagedir(args.name,args.topdir,args.confidence,args.verbose)
          #  print(people_present)
    elif args.mode=='list':
        #counts and list of booleans
        people_count,nonpeople_count,mark_array=pdetect.run_people_detector_imagelist(args.name,args.topdir,args.confidence,args.batchsize,args.verbose)
       # print(mark_array)
    elif args.mode=='bulk':
        #counts and list of booleans for the entire directory
        people_count,nonpeople_count,mark_array=pdetect.run_people_detector_bulk(args.topdir,args.name,args.confidence,args.batchsize,args.verbose)
        #print(mark_array)
    elif args.mode=='tar':
        pdetect.run_people_detector_tarfiles(args.topdir,args.name,args.confidence)
       
    else:
        print("Unknown mode or not yet implemented")
    
    
    #model = model_pipeline(args)