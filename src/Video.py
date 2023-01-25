import moderngl
import time
import threading
import queue
import skvideo.io
import numpy as np
# https://medium.datadriveninvestor.com/the-most-simple-explanation-of-threads-and-queues-in-python-cbc206025dd1
# https://docs.python.org/3/library/queue.html
# https://medium.com/fullstackai/concurrency-in-python-cooperative-vs-preemptive-scheduling-5feaed7f6e53
# https://www.dataquest.io/blog/multithreading-in-python/


class Texture:
    def __init__(self,ctx,size,channels,location,prog,tex_name):
        self.size=size
        self.location=location
        self.channels=channels
        self.tex = ctx.texture(size,channels,dtype='u1')
        self.tex.repeat_x = False
        self.tex.repeat_y = False
        self.tex.filter == (moderngl.NEAREST, moderngl.NEAREST)
        self.tex.use(location=location)
        prog[tex_name].value = location

    def load(self,I):
        self.tex.write(I.tobytes())


class VideoCache(Texture):
    def __init__(self,*args):
        super().__init__(*args)
        self.reset()
        self.q=queue.Queue()
        self.frame_q=queue.Queue()
        self.is_loading_=False
        
        self.worker = threading.Thread(target=self.startThread,args=(self.q,self.frame_q,),daemon=True)
        self.worker.start()
        

    def startThread(self,q,frame_q,):
        while True:
            try:
                video=q.get(False)
                start=time.time()
                frames=skvideo.io.vread(video) #,inputdict={'-c:v':'libx264'})
                frame_q.put(frames)
                print(f'{self.location} loading time: {time.time()-start:.2f}, video: {video}, shape: {frames.shape}')
            except queue.Empty:
                pass
            time.sleep(0.02)
        
    def play(self,video):
        if not self.is_loading_:
            self.is_loading_=True
            self.q.put(video)
            print(f'{self.location} play {video}')

    def reset(self):
        self.load(np.zeros((*self.size,self.channels),dtype='u1'))
        self.is_playing_=False
        self.is_loading_=False

    def stop(self):
        if self.is_playing_:
            self.reset()
            

    def update(self):
        if not self.is_playing_:
            try:
                self.frames=self.frame_q.get(False)
                # print(f'{self.location} start playing')
                if self.is_loading_:
                    self.is_playing_=True
                    self.start=time.time()
                    self.counter=-1
                    self.is_loading_=False
                
            except queue.Empty:
                pass

        if self.is_playing_:
            if 30.*(time.time()-self.start)>float(self.counter):
                self.counter+=1

                if self.counter<len(self.frames):
                    if self.channels==3:
                        self.load(self.frames[self.counter])
                    else:
                        self.load(self.frames[self.counter,:,:,0])
                else:
                    self.reset()
            
    def is_playing(self):
        return self.is_playing_

   
        
    
class VideoStreamer(Texture):
    def __init__(self,*args,video=None):
        super().__init__(*args)
        
        self.load(np.zeros((*self.size,self.channels),dtype='u1'))
        self.repeat=True if video else False
        self.q=queue.Queue()
        self.frame_q=queue.Queue()
        self.status_q=queue.Queue()

        self.worker = threading.Thread(target=self.startThread,args=(self.q,self.frame_q,self.status_q,),daemon=True)
        self.worker.start()
        self.is_playing_=False
        self.is_loading_=False

        if video:
            self.play(video)

    def play(self,video):
        if not self.is_loading_:
            self.is_loading_=True
            # print(f'start play: {video}, now: {now}')
            self.q.put(video)
        
    def stop(self):
        if self.is_playing_:
            self.q.put(None)
    
    def startThread(self,q,frame_q,status_q,):
        reader=None
        play_video=False
        stop_video=False
        video=None
        while True:
            
            # print(f'{self.location} {frame_q.qsize()}')
            try:
                video=q.get(False)
                if video:
                    play_video=True
                else:
                    stop_video=True
                
            except queue.Empty:
                pass

            if play_video:
                play_video=False
                print(f'vid {self.location} start playing: {video}')
                if reader!=None:
                    frame_q.put(np.zeros((*self.size,self.channels),dtype='u1'))
                    reader.close()
                    
                    
                reader=skvideo.io.FFmpegReader(video) #,outputdict={'-c:v':'libx264'})
                status_q.put(True)
    
                gen=reader.nextFrame()
                    
                start=time.time()
                counter=-1

            if stop_video:
                print(f'vid {self.location} stop playing')
                stop_video=False
                if reader!=None:
                    frame_q.put(np.zeros((*self.size,self.channels),dtype='u1'))
                    status_q.put(False)
                    reader.close()
                    reader=None

            if reader:
                if 30.*(time.time()-start)>float(counter):
                    
                    try:
                        # start_read=time.time()
                        frame=next(gen)
                        counter+=1
                        # print(f'{1000*(time.time()-start_read):.0f}')
                        frame_q.put(frame)
                        
                    except StopIteration:
                        frame_q.put(np.zeros((*self.size,self.channels),dtype='u1'))
                        status_q.put(False)
                        reader.close()
                        reader=None
                        print(f'vid {self.location} done playing, repeat: {self.repeat}')

                        if self.repeat:
                            play_video=True
                        

            time.sleep(0.01)
            
        

    def update(self):
       
        try:
            
            frame=None
            while True: # drop frames ensure queue not inflate
                frame = self.frame_q.get(False)   

        except queue.Empty:
            if type(frame)!=type(None):
                if self.channels==3:
                    self.load(frame)
                else:
                    self.load(frame[:,:,0])
            
        try:
            self.is_playing_=self.status_q.get(False)
            self.is_loading_ = False
            # print(f'vid {self.location} playing status changed: {self.is_playing_}')
        except queue.Empty:
            pass

    def is_playing(self):
        return self.is_playing_

        
class VideoRecorder:
    def __init__(self,size):
        self.size=size
        self.q=queue.Queue()
        self.frame_q=queue.Queue()
        self.status_q=queue.Queue()
        self.worker = threading.Thread(target=self.startThread,args=(self.q,self.frame_q,self.status_q,),daemon=True)
        self.worker.start()
        self.path=None
        self.is_recording_=False
        

    def startThread(self,q,frame_q,status_q):
        options={'-c:v':'libx264','-r':'30','-crf':'0'}
        writer=None

        while True:
            try:
                msg,path=q.get(False)
                
                if msg:
                    writer=skvideo.io.FFmpegWriter(path,outputdict=options)
                    status_q.put(True)
                else:
                    if writer:
                        writer.close()
                        status_q.put(False)
                        writer=None

            except queue.Empty:
                pass

            try:
                frame=frame_q.get(False)        
                if writer:
                    writer.writeFrame(frame)
            except queue.Empty:
                pass
            
            time.sleep(0.02)
    
    def start(self,path):
        self.q.put((True,path))

    def stop(self):
        self.q.put((False,None))

    def add_frame(self,frame):
        self.frame_q.put(frame)

    def update(self,frame=None):
        try:
            self.is_recording_=self.status_q.get(False)
            # print(f'recording status changed: {self.is_recording_}')
        
        except queue.Empty:
            pass

    def is_recording(self):
        return self.is_recording_


