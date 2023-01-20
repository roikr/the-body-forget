# background substraction on shader
# TODO: use median of bg and test in depth range (as done in extarct_contours_v1.py)

import moderngl_window
from moderngl_window.conf import settings
from moderngl_window.timers.clock import Timer
import moderngl
from moderngl_window import geometry
import numpy as np

import time
import os
from DepthCamera import *


vertex_shader="""
    #version 330
    in vec3 in_position;
    in vec2 in_texcoord_0;
    out vec2 uv0;

    void main() {
        gl_Position = vec4(in_position, 1);
        uv0 = in_texcoord_0;
    }
"""

fragment_shader="""
    #version 330
    out vec4 fragColor;
    uniform usampler2D tex0;
    uniform bool rec;
    in vec2 uv0;

    void main() {
        float c=texture(tex0,vec2(uv0.x,1.-uv0.y)).x;
        //float c=texture(tex0,uv0).x;
        fragColor=vec4(mix(vec3(c),vec3(c,0.,0.),float(rec)),1.0);
    }
"""

        
class QuadFullscreen:
    
    def __init__(self,size, **kwargs):
       
        self.cam_size=self.view_size=size
        w,h=self.view_size
        settings.WINDOW['class'] = 'moderngl_window.context.glfw.Window'
        settings.WINDOW['size'] = self.view_size
        settings.WINDOW['aspect_ratio'] = w/h
        # settings.WINDOW['fullscreen'] = True
        self.wnd = moderngl_window.create_window_from_settings()
        self.ctx = self.wnd.ctx
        self.quad = geometry.quad_fs()
        self.prog = self.ctx.program(vertex_shader=vertex_shader,fragment_shader=fragment_shader)
        # bags=[f'data/{b}.bag' for b in ['20221225_193047','20230116_174627','20230116_190137','20230116_190429']]
        self.cam=DepthCamera(self.ctx,self.cam_size,1,0,self.prog,'tex0') #,path=bags[3])
        self.prog['rec'].value=False
        
        self.counter=0
        
    def render(self, time_: float, frame_time: float):
        self.cam.update()
        self.prog['rec'].value=self.cam.is_recording()
        self.ctx.clear()
        self.quad.render(self.prog)

    def run(self):
        timer = Timer()
        timer.start()

        while not self.wnd.is_closing:
            self.wnd.clear()
            time, frame_time = timer.next_frame()
            self.render(time, frame_time)
            self.wnd.swap_buffers()

        self.wnd.destroy()


if __name__ == '__main__':
    app=QuadFullscreen((1024,768))
    app.run()
    
    
