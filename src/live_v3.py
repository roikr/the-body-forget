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
import subprocess

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
    uniform usampler2D bg;
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
        vec2 q=vec2(1.-uv0.x,uv0.y);
        ivec2 p=ivec2(q*view_size);
        vec2 cam_pos; //=vec2(q.x,q.y*cam_size.y/cam_size.x+float(view_size.y-cam_size.y)/view_size.y);
        
        float dy=float(view_size.x)/cam_size.x*cam_size.y-view_size.y;
        vec2 pos=vec2(p.x,p.y);
        vec2 cam_win=vec2(view_size.x,float(view_size.x)/cam_size.x*cam_size.y);
        cam_pos=pos/cam_win;
        cam_pos.y=1.-cam_pos.y;
        

        float c0=texture(tex0,cam_pos).x/255.;
        vec3 c1=texture(tex1, vec2(p)/tex_size).xyz/255.*1.2;
        
        float c2=texture(tex2,cam_pos).x/255.;
        vec3 c3=texture(tex3, vec2(p)/tex_size).xyz/255.*1.2;
        
        float c4=texture(tex4,cam_pos).x/255.;
        vec3 c5=texture(tex5, vec2(p)/tex_size).xyz/255.*1.2;
        
        float c6=texture(tex6,cam_pos).x/255.;
        
        
        if (rec) {
            if (c0==0) {
                fragColor=vec4(vec3(0.25*texture(bg,q).x/255),1.0);
            } else {
                fragColor = vec4(c0,0.0,0.0,1.0);
            }
        } else {
            if (c2*c4*c6>0) {
                fragColor = vec4(vec3(0.0),1.0);
            }
            else if (c2+c4+c6==0) {
                fragColor=vec4(vec3(0.25*texture(bg,q).x/255),1.0);
            } else if (c2*c4>0) {
                fragColor = vec4(vec3(0.,0.,1.2*c6*c5.z),1.0);
            } else if (c4*c6>0) {
                fragColor = vec4(c1*c2,1.0);
            } else if (c6*c2>0) {
                fragColor = vec4(c3*c4,1.0);
            } else {
                fragColor = vec4(c1*c2+c3*c4+vec3(0.,0.,1.2*c6*c5.z),1.0);
                //fragColor = vec4(vec3(c2+c4+c6),1.0);
            }    
        }
        
    }
"""

fragment_shader_simple="""
    #version 330
    out vec4 fragColor;
    uniform usampler2D tex1; 
    uniform ivec2 view_size;
    uniform ivec2 tex_size;
    //uniform ivec2 cam_size;
    uniform bool rec;
    in vec2 uv0;

    void main() {
        vec2 q=(vec2(1.)-uv0);
        ivec2 p=ivec2(q*view_size);
       // vec2 cam_pos=vec2(q.x,q.y*cam_size.y/cam_size.x+float(view_size.y-cam_size.y)/view_size.y);
        
        //float c0=texture(tex0,cam_pos).x/255.;
        vec3 c1=texture(tex1, vec2(p)/tex_size).xyz/255.;
        //float c2=texture(tex2,cam_pos).x/255.;
        
        
        
        if (rec) {
            fragColor = vec4(c1.x,0.0,0.0,1.0);
        } else {
            fragColor = vec4(c1,1.0);
        }
       
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
        settings.WINDOW['fullscreen'] = True
        settings.WINDOW['cursor'] = False
        self.wnd = moderngl_window.create_window_from_settings()
        self.ctx = self.wnd.ctx
        self.quad = geometry.quad_fs()
        self.prog = self.ctx.program(vertex_shader=vertex_shader,fragment_shader=fragment_shader)
        self.vid1=VideoTexture(self.ctx,self.tex_size,3,1,self.prog,'tex1',video='textures/21.mp4')
        self.vid2=VideoTexture(self.ctx,self.cam_size,1,2,self.prog,'tex2')
        self.vid3=VideoTexture(self.ctx,self.tex_size,3,3,self.prog,'tex3',video='textures/22.mp4')
        self.vid4=VideoTexture(self.ctx,self.cam_size,1,4,self.prog,'tex4')
        self.vid5=VideoTexture(self.ctx,self.tex_size,3,5,self.prog,'tex5',video='textures/20.mp4')
        self.vid6=VideoTexture(self.ctx,self.cam_size,1,6,self.prog,'tex6')
        bg=cv2.imread('textures/bg.png',cv2.IMREAD_GRAYSCALE)
        bg_size=bg.shape[::-1]
        self.bg=Texture(self.ctx,bg_size,1,7,self.prog,'bg')
        self.bg.load(bg)


        self.videos=[f for f in os.listdir('videos') if f.endswith('.mp4')]
        self.tex_players=[self.vid1,self.vid3,self.vid5]
        self.vid_players=[self.vid2,self.vid4,self.vid6]

        self.sounds=[f for f in os.listdir('sounds') if f.endswith('.wav')]
         
        bags=[f'data/{b}.bag' for b in ['20221225_193047','20230116_174627','20230116_190137','20230116_190429']]
        self.cam=DepthCamera(self.ctx,self.cam_size,1,0,self.prog,'tex0') # ,path=bags[3])
        self.rec=VideoRecorder(self.cam_size)
       
        self.prog['view_size'].value=self.view_size
        self.prog['tex_size'].value=self.tex_size
        self.prog['cam_size'].value=self.cam_size
        self.prog['rec'].value=False
        
        self.recording_duration=10
        self.playback_duration=10
        self.minimum_recording=7

        self.last_visible=time.time()
        self.record_time=time.time()
        self.play_time=time.time()
        self.recording=False
        
    def update(self):
        [v.update() for v in self.tex_players]
        [v.update() for v in self.vid_players]

        if self.cam.is_ready() and not self.rec.is_recording() and len(self.videos):
            # for v in self.vid_players:
            #     if not v.is_playing():
            #         v.play(f'videos/{np.random.choice(self.videos)}',False) 
            if not self.vid2.is_playing():
                self.vid2.play(f'videos/{np.random.choice(self.videos)}',False) 

            if not self.vid4.is_playing():
                self.vid4.play(f'videos/{np.random.choice(self.videos)}',False) 
                

        is_visible=self.cam.is_visible() 
        
        frame=self.cam.update()

        if self.cam.is_ready():
            if self.cam.is_visible():
                self.last_visible = time.time()
                if not self.recording and not self.rec.is_recording() and (time.time()-self.play_time>self.playback_duration):
                    self.current_video=f'{time.strftime("%Y%m%d_%H%M%S")}.mp4'
                    self.record_time=time.time()
                    print(f'start recording: {self.current_video}')
                    self.rec.start(f'videos/{self.current_video}')
                    self.recording=True
                    self.vid2.stop()
                    self.vid4.stop()
                    self.vid6.stop()
                    subprocess.Popen(['aplay',f'sounds/{np.random.choice(self.sounds)}'])

            if self.recording and ((time.time()-self.last_visible>0.5) or (time.time()-self.record_time>self.recording_duration)):
                print(f'stop recording: {self.current_video}')
                self.rec.stop()
                self.recording=False
                
            if self.rec.is_recording() and self.recording and type(frame)!=type(None):
                self.rec.add_frame(frame)

        recording=self.rec.is_recording()
        self.rec.update()
        if recording and not self.rec.is_recording():
            if (time.time()-self.record_time)>self.minimum_recording:
                print(f'append: {self.current_video}')
                self.vid6.play(f'videos/{self.current_video}',True)
                self.play_time=time.time()
                self.videos.append(self.current_video)

            else:
                print(f'remove: {self.current_video}')
                os.remove(f'videos/{self.current_video}')

        
    def render(self, time_: float, frame_time: float):
        self.prog['rec'].value=self.recording or not self.cam.is_ready()
        self.ctx.clear()
        self.quad.render(self.prog)

    def run(self):
        timer = Timer()
        timer.start()

        while not self.wnd.is_closing:
            self.wnd.clear()
            time_, frame_time = timer.next_frame()
            # print(f'{time_*1000:.0f}, {frame_time*1.e6:.0f}')
            self.update()
            self.render(time_, frame_time)
            self.wnd.swap_buffers()
            time.sleep(0.01)

        self.wnd.destroy()


if __name__ == '__main__':
    app=QuadFullscreen((1920,1200))
    # app=QuadFullscreen((1280,800))
    # app=QuadFullscreen((1024,768))
    app.run()
    
    
