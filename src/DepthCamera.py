import numpy as np
import pyrealsense2 as rs
import datetime
import cv2
import time
from Video import Texture
from contours_utils import *

class DepthCamera(Texture):
    def __init__(self,*args,path=None):
        super().__init__(*args)
        # start=time.time()
        self.pipeline = rs.pipeline()   
        config = rs.config()
        if path:
            rs.config.enable_device_from_file(config, path,repeat_playback=True)
        # config.enable_all_streams() 
        config.enable_stream(rs.stream.depth,1024,768, rs.format.z16, 30)
        config.enable_stream(rs.stream.confidence) #, 1280, 720, rs.format.raw8, 30)
        profile=self.pipeline.start(config)
        # playback = profile.get_device().as_playback()
        depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
        depth_intrinsics = depth_profile.get_intrinsics()
        w, h = depth_intrinsics.width, depth_intrinsics.height
        assert (w,h)==self.size
        self.counter=100
        self.bg_conf=np.empty((self.counter,h,w),dtype=np.uint8)
        self.bg_depth=np.empty((self.counter,h,w),dtype=np.uint16)
        
        self.d_res=0.00025
        self.d_min=int(2/self.d_res)
        self.d_max=int(3/self.d_res)
        self.min_area=10000
        self.kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        self.d_trigger=int(3/self.d_res)
        self.capturing_duration=10
        self.playback_duration=10
        self.start=time.time()
        self.capturing=False
               
    def is_ready(self):
        return self.counter==0

    def is_capturing(self):
        return self.capturing

    def update(self):
        
        capturing=self.capturing

        frame=None
        frameset = self.pipeline.poll_for_frames() 
        if frameset: 
            for frame in frameset:
                profile_type=frame.get_profile().stream_type()
                if profile_type==rs.stream.depth:
                    depth=np.array(frame.get_data())
                if profile_type==rs.stream.confidence:
                    conf=np.array(frame.get_data())

            if self.counter>0:
                i=len(self.bg_depth)-self.counter
                self.bg_depth[i]=depth
                self.bg_conf[i]=conf
                self.counter-=1
                if self.counter==0:
                    self.med_conf=np.median(self.bg_conf,0)
                    self.med_depth=np.median(self.bg_depth,0)
                    self.mean_depth=self.bg_depth.mean(0)
                    self.low_conf_mask=self.med_conf<128
                    del self.bg_depth,self.bg_conf
                    # self.std_depth=self.bg_depth.std(0)
                    # del self.bg_conf,self.bg_depth
                    # self.M_med_conf_16=(med_conf==16)
                    # self.M_med_conf_bt_16=(med_conf>16)
                   
                    
           
            frame=np.zeros_like(depth,dtype='u1')
            if self.is_ready():
                conf_mask=conf>=128
                bg_mask=np.abs(self.mean_depth-depth.astype('f'))>150
                depth_mask=(depth>self.d_min) & (depth<self.d_max)
                mask=conf_mask & (bg_mask | (~bg_mask & self.low_conf_mask)) & depth_mask
                # M=np.block([[mask,conf_mask],[bg_mask,~bg_mask & bg_conf_mask]])
                # h,w=depth.shape
                # M=cv2.resize(255*M.astype('u1'),(w,h))
                M=mask
                I=M.astype('u1')
                I=cv2.morphologyEx(I,cv2.MORPH_OPEN,self.kernel,iterations=3)
                I=cv2.morphologyEx(I,cv2.MORPH_DILATE,self.kernel,iterations=2)
                
                # frame=255*I
                cntrs=extract_contours(I,self.min_area)
                if len(cntrs):
                    
                    C=cv2.fillPoly(np.zeros_like(depth,dtype='u1'),cntrs,(255),cv2.LINE_AA).astype('bool')
                    frame[M&C]=255*(1-(depth[M&C]-self.d_min)/(self.d_max-self.d_min))

                    med=np.median(depth[M&C])
                    if med<self.d_trigger and not self.capturing and time.time()-self.start>self.playback_duration:
                        self.capturing=True
                        self.start=time.time()

                    if self.capturing and med>self.d_trigger:
                        self.capturing=False
                        self.start=time.time()
                        
                else:
                    if self.capturing:
                        self.capturing=False
                        self.start=time.time()

            else:
                M=(conf>=128) & (depth>self.d_min) & (depth<self.d_max)
                frame[M]=255*(1-(depth[M]*self.d_res-self.d_min)/(self.d_max-self.d_min))
            
            self.load(frame)
        
        if self.capturing and time.time()-self.start>self.capturing_duration:
            self.capturing=False
            self.start=time.time()
            

        if capturing!=self.capturing:
            
            print(f'capturing status change: {self.capturing}')

        return frame

   
