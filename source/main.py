# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import cv2
import os
from itertools import count
# relative imports
from toolbox.globals import PATHS, PARAMETERS
from source.embedded_communication.send_to_embedded import send_output
from source.videostream.videostream_main import get_latest_frame
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracker
import source.aiming.aiming_main as aiming

# import parameters
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]

def setup(
        get_latest_frame=get_latest_frame,
        on_next_frame=None,
        modeling=modeling,
        tracker=tracker,
        aiming=aiming,
        send_output=send_output
    ):
    """
    this function is used to connect main with other modules
    it can be connected to simulated/testing versions of other modules (laptop)
    or it can be connected to actual versions (tx2)
    
    since we are testing multiple versions of main functions
    this returns a list of the all the different main functions
    """
    
    # 
    # option #1
    #
    def simple_synchronous():
        """
        this function is the most simple version of CV
        - no tracking
        - no multiprocessing/async/multithreading
        
        it takes 2 functions as arguments and uses them to get/send output
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
            x, y, z = aiming.aim(boxes)
            
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(counter, frame, (boxes, confidences), (x,y,z))
            
            # send data to embedded
            send_output(x, y, z)
    
    # 
    # option #2
    # 
    def synchronous_with_tracker():
        # by defaul tracker needs model to be run
        tracker_found_bounding_box = False
        for counter in count(start=0, step=1): # counts up infinitely starting at 0
            frame = get_latest_frame()

            if counter % 20 == 0 or not tracker_found_bounding_box:
                #
                # call model
                #
                boxes, confidences, classIDs = model(frame, confidence, threshold)
                tracker_found_bounding_box = tracker.init(frame,boxes)
            else:
                #
                # call tracker
                #
                frame, tracker_found_bounding_box = tracker.draw(frame)
                
            # FIXME:
            #   the tracker doesn't return bounding boxes
            #   the boxes value is just leftover from whenever the model last ran
            
            # figure out where to aim
            x, y, z = aiming.aim(boxes)
            
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(counter, frame, (boxes, confidences), (x,y,z))
            
            # send data to embedded
            send_output(x, y, z)
    
    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker

    # 
    # option #3
    # 
    # multiprocessing: have main/tracker/videostream/aiming as seperate processes
    # have modeling only be called once tracker fails
    
    # 
    # option #4
    # 
    # have multiple processes and have them all running all the time
    # tracker pulls the latest model rather than waiting to fail before calling modeling

    
if __name__ == '__main__':
    # setup mains with real inputs/outputs
    simple_synchronous, synchronous_with_tracker = setup()
    
    # for now, default to simple_synchronous
    simple_synchronous()
