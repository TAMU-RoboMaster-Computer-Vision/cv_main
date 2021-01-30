import pyrealsense2 as rs
import numpy as np
import cv2
from toolbox.globals import PARAMETERS,print

streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
gridSize = PARAMETERS['aiming']['grid_size']

pipeline = rs.pipeline()                                            # declares and initializes the pipeline variable
config = rs.config()                                                # declares and initializes the config variable for the pipeline
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
config.disable_stream(rs.stream.color)
#config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
profile = pipeline.start(config)

# bbox[x coordinate of the top left of the bounding box, y coordinate of the top left of the bounding box, width of box, height of box]
def WorldCoordinate(bbox):
    frames = pipeline.wait_for_frames()     # gets all frames
    depth_frame = frames.get_depth_frame()  # gets the depth frame
    depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
    depth_value = 0.5
    depth_pixel = [depth_intrin.ppx, depth_intrin.ppy]
    depth_point = rs.rs2_deproject_pixel_to_point(depth_intrin, depth_pixel, depth_value)
    return depth_point
    if not depth_frame:                     # if there is no aligned_depth_frame or color_frame then leave the loop
        return None

bbox = [410,140,65,120]

while True:
    try:
        print(WorldCoordinate(bbox))
    except:
        pipeline.stop()
