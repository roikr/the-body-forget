import moderngl_window
from moderngl_window.conf import settings
from moderngl_window.timers.clock import Timer
import moderngl
from moderngl_window import geometry
import numpy as np
import time
import os
from DepthCamera import *
from Video import *

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
    uniform usampler2D tex1;
    uniform usampler2D tex2;
    uniform usampler2D tex3;
    uniform usampler2D tex4;
    uniform usampler2D tex5;
    uniform usampler2D tex6;
    uniform ivec2 view_size;
    uniform ivec2 tex_size;
    uniform ivec2 cam_size;
    uniform bool rec;
    in vec2 uv0;

    void main() {
        vec2 q=(vec2(1.)-uv0);
        ivec2 p=ivec2(q*view_size);
        vec2 cam_pos=vec2(q.x,q.y*cam_size.y/cam_size.x+float(view_size.y-cam_size.y)/view_size.y);
        
        float c0=texture(tex0,cam_pos).x/255.;
        vec3 c1=texture(tex1, vec2(p)/tex_size).xyz/255.;
        float c2=texture(tex2,cam_pos).x/255.;
        vec3 c3=texture(tex3, vec2(p)/tex_size).xyz/255.;
        float c4=texture(tex4,cam_pos).x/255.;
        vec3 c5=texture(tex5, vec2(p)/tex_size).xyz/255.;
        float c6=texture(tex6,cam_pos).x/255.;
        
        
        if (rec) {
            fragColor = vec4(c0,0.0,0.0,1.0);
        } else {
            if (c2*c4*c6>0) discard;
            else if (c2*c4>0) {
                fragColor = vec4(c5*c6,1.0);
            } else if (c4*c6>0) {
                fragColor = vec4(c1*c2,1.0);
            } else if (c6*c2>0) {
                fragColor = vec4(c3*c4,1.0);
            } else {
                fragColor = vec4(c1*c2+c3*c4+c5*c6,1.0);
            }
            //fragColor = vec4(0.,c1,c3,1.0);
        }
        //fragColor = vec4(vec3(c4),1.0);
    }
"""


class QuadFullscreen:
    
    def __init__(self,size, **kwargs):
       
        self.view_size=size
        self.cam_size=(1024,768)
        self.tex_size=(1920,1080)
        w,h=self.view_size
        settings.WINDOW['class'] = 'moderngl_window.context.glfw.Window'
        settings.WINDOW['size'] = self.view_size
        settings.WINDOW['aspect_ratio'] = w/h
        # settings.WINDOW['fullscreen'] = True
        # settings.WINDOW['cursor'] = False
        self.wnd = moderngl_window.create_window_from_settings()
        self.ctx = self.wnd.ctx
        self.quad = geometry.quad_fs()
        self.prog = self.ctx.program(vertex_shader=vertex_shader,fragment_shader=fragment_shader)
        self.vid1=VideoTexture(self.ctx,self.tex_size,3,1,self.prog,'tex1',video='textures/1.mp4')
        self.vid2=VideoTexture(self.ctx,self.cam_size,1,2,self.prog,'tex2')#,video='videos/vid_001.mp4')
        self.vid3=VideoTexture(self.ctx,self.tex_size,3,3,self.prog,'tex3',video='textures/3.mp4')
        self.vid4=VideoTexture(self.ctx,self.cam_size,1,4,self.prog,'tex4')#,video='videos/vid_003.mp4')
        self.vid5=VideoTexture(self.ctx,self.tex_size,3,5,self.prog,'tex5',video='textures/4.mp4')
        self.vid6=VideoTexture(self.ctx,self.cam_size,1,6,self.prog,'tex6')#,video='videos/vid_004.mp4')
        self.videos=os.listdir('videos')
         
        bags=[f'data/{b}.bag' for b in ['20221225_193047','20230116_174627','20230116_190137','20230116_190429']]
        self.cam=DepthCamera(self.ctx,self.cam_size,1,0,self.prog,'tex0',path=bags[3])
        # self.rec=VideoRecorder(self.cam_size)
       
        self.prog['view_size'].value=self.view_size
        self.prog['tex_size'].value=self.tex_size
        self.prog['cam_size'].value=self.cam_size
        self.prog['rec'].value=False
        
        self.counter=0
        
    def render(self, time_: float, frame_time: float):
        [v.update() for v in [self.vid1,self.vid2,self.vid3,self.vid4,self.vid5,self.vid6]]

        for v in [self.vid2,self.vid4,self.vid6]:
            if not v.is_playing():
                v.play(f'videos/{np.random.choice(self.videos)}',False) 

        # recording=self.cam.is_recording()
        # frame=self.cam.update()
        # if recording!=self.cam.is_recording():
        #     if self.cam.is_recording():
        #         filename=f'videos/vid_{self.counter:03d}.mp4'
        #         print(f'start recording: {filename}')
        #         self.rec.start(filename)
        #         self.last_video=filename
        #     else:
        #         print('stop recording')
        #         self.counter+=1
        #         self.rec.stop()
        #         self.vid1.play(self.last_video,True)
        #         videos=np.array(os.listdir('videos'))
                
        #         # for f in np.random.choice(videos,len(videos)):
        #         # self.vid3.play(f'videos/{f}',False)
        #         self.vid3.play(f'videos/{np.random.choice(videos,1)[0]}',True)

        # if self.cam.is_recording() and type(frame)!=type(None):
        #     self.rec.update(frame)


        
        # if type(frame)!=type(None):
            
            # print(time_,frame_time)
        
        # self.prog['rec'].value=self.cam.is_recording()
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
    app=QuadFullscreen((1920,1080))
    # app=QuadFullscreen((1024,768))
    app.run()
    
    
