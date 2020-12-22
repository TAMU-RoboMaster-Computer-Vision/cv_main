# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import multiprocessing
import cv2
import os
from itertools import count
from multiprocessing import Process,Value,Array
from multiprocessing.managers import BaseManager
# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
from source.embedded_communication.embedded_main import embedded_communication
from source.videostream.videostream_main import get_latest_frame
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracker
import source.aiming.aiming_main as aiming

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]

def setup(
        get_latest_frame=get_latest_frame,
        on_next_frame=None,
        modeling=modeling,
        tracker=tracker,
        aiming=aiming,
        #send_output=send_output
        embedded_communication=embedded_communication
    ):
    """
    this function is used to connect main with other modules
    it can be connected to simulated/testing versions of other modules (laptop)
    or it can be connected to actual versions (tx2)
    
    since we are testing multiple versions of main functions
    this returns a list of the all the different main functions
    """
    class MyManager(BaseManager):
        pass
    MyManager.register('tracker', tracker.trackers)

    # 
    # option #1
    #
    def simple_synchronous():
        """
        this function is the most simple version of CV
        - no tracking
        - no multiprocessing/async/multithreading
        """
        for counter in count(start=0, step=1): # counts up infinitely starting at 0
            # get the latest image from the camera
            frame = get_latest_frame()
            if frame is None:
                print("assuming the video stream ended because latest frame is None")
                return
            
            # run the model
            boxes, confidences, classIDs = modeling.get_bounding_boxes(frame, confidence, threshold)
            
            # figure out where to aim
            x, y = aiming.aim(boxes)
            
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(counter, frame, (boxes, confidences), (x,y))
            
            # send data to embedded
            embedded_communication.send_output(x, y)
    
    # 
    # option #2
    # 
    def synchronous_with_tracker():
        """
        the 2nd main function
        - no multiprocessing
        - does use the tracker(KCF)
        """

        realCounter = 1 # can't use counter for frame number since we might ask for the same frame twice in get_latest_video_frame
        frameNumber = 1
        # model needs to run on first iteration
        best_bounding_box = None
        with MyManager() as manager:
            track = manager.tracker()
            for counter in count(start=0, step=1): # counts up infinitely starting at 0

                # grabs frame and ends loop if we reach the last one
                frame = get_latest_frame()
                # stop loop if using get_next_video_frame   
                if frame is None:
                    break
                # stop loop if using get_latest_video_frame(required since there are 3 cases for get_latest_video_frame compared to the 2 cases in get_next_video_frame)
                if isinstance(frame,int):
                    if frame==-1:
                        break
                    else: # this means there are still frames to come
                        continue

                frameNumber+=1
                realCounter+=1
                # run model every model_frequency frames or whenever the tracker fails
                if realCounter % model_frequency == 0 or (best_bounding_box is None):
                    realCounter=1
                    # call model and initialize tracker
                    boxes, confidences, classIDs = modeling.get_bounding_boxes(frame, confidence, threshold)
                    best_bounding_box = track.init(frame,boxes)
                else:
                    best_bounding_box = track.update(frame)

                # optional value for debugging/testing
                x, y = aiming.aim([best_bounding_box] if best_bounding_box else [])

                if not (on_next_frame is None) :
                    on_next_frame(frameNumber, frame, ([best_bounding_box], [1])if best_bounding_box else ([], []), (x,y))
                
    

    def modelMulti(frame,confidence,threshold,best_bounding_box,track,modeling):
        #run the model and update best bounding box to the new bounding box if it exists, otherwise keep tracking the old bounding box
        boxes, confidences, classIDs = modeling.get_bounding_boxes(frame, confidence, threshold)
        potentialbbox = track.init(frame,boxes)
        if potentialbbox:
            best_bounding_box[:] = potentialbbox
        
    # option #4
    # 
    # have tracking almost always running and modeling run in another process
    # tracker pulls the latest model rather than waiting to fail before calling modeling
    def multiprocessing_with_tracker():
        realCounter = 1 # can't use counter for frame number since we might ask for the same frame twice in get_latest_video_frame
        frameNumber = 1
        # model needs to run on first iteration
        
        best_bounding_box = Array('d',[-1,-1,-1,-1])
        process = None
        with MyManager() as manager:
            track = manager.tracker()
            for counter in count(start=0, step=1): # counts up infinitely starting at 0
                # grabs frame and ends loop if we reach the last one
                frame = get_latest_frame()
                # stop loop if using get_next_video_frame   
                if frame is None:
                    break
                # stop loop if using get_latest_video_frame(required since there are 3 cases for get_latest_video_frame compared to the 2 cases in get_next_video_frame)
                if isinstance(frame,int):
                    if frame==-1:
                        break
                    else: # this means there are still frames to come
                        continue
                realCounter+=1
                frameNumber+=1
                # run model if there is no current bounding box
                if best_bounding_box[:] == [-1,-1,-1,-1]:
                    if process is None or process.is_alive()==False:
                        process = Process(target=modelMulti,args=(frame,confidence,threshold,best_bounding_box,track,modeling)) # need to find a way to pass tracker and modeling in properly, in case it's not
                        process.start() 
                        realCounter=1

                else:
                # run model in another process every model_frequency frames
                    if realCounter % model_frequency == 0:
                        # call model and initialize tracker
                        if process is None or process.is_alive()==False:
                            process = Process(target=modelMulti,args=(frame,confidence,threshold,best_bounding_box,track,modeling)) # need to find a way to pass tracker and modeling in properly, in case it's not
                            process.start() 
                    
                    potentialbbox = track.update(frame)
                    best_bounding_box[:] = potentialbbox if potentialbbox else [-1,-1,-1,-1]

                # figure out where to aim
                # if best_bounding_box:
                x, y = aiming.aim(best_bounding_box[:])
                
                # optional value for debugging/testing
                if not (on_next_frame is None) :
                    on_next_frame(frameNumber, frame, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (x,y))
                
                # send data to embedded
                embedded_communication.send_output(x, y)
            process.join()

    
    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    
if __name__ == '__main__':
    # setup mains with real inputs/outputs
    simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup()
    
    # for now, default to simple_synchronous
    multiprocessing_with_tracker