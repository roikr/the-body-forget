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
        self.channels=channels
        self.tex = ctx.texture(size,channels,dtype='u1')
        self.tex.repeat_x = False
        self.tex.repeat_y = False
        self.tex.filter == (moderngl.NEAREST, moderngl.NEAREST)
        self.tex.use(location=location)
        prog[tex_name].value = location

    def load(self,I):
        self.tex.write(I.tobytes())
        

class VideoTexture(Texture):
    def __init__(self,*args,video=None):
        super().__init__(*args)
        
        self.load(np.zeros((*self.size,self.channels),dtype='u1'))
        self.repeat=False
        self.q=queue.Queue()
        self.frame_q=queue.Queue()

        self.worker = threading.Thread(target=self.startThread,args=(self.q,self.frame_q,),daemon=True)
        self.worker.start()

        if video:
            self.repeat=True
            self.play(video,True)

    def play(self,video,now):
        # print(f'start play: {video}, now: {now}')
        self.q.put((video,now))
        
    
    def startThread(self,q,frame_q):
        reader=None
        list=[]
        push=False
        while True:
            try:
                video,now=q.get(False)
                list.append(video)
                if now:
                    push=True
                
            except queue.Empty:
                pass

            if push or (reader==None and len(list)):
                if self.repeat:
                    next_video=list[0]
                else:
                    next_video=list.pop() if push else list.pop(0)

                push=False

                if reader!=None:
                    reader.close()
                
                print(f'playing: {next_video}')
                reader=skvideo.io.FFmpegReader(next_video,outputdict={'-c:v':'h264_videotoolbox'})
                gen=reader.nextFrame()
                
                start=time.time()
                counter=-1

            if reader:
                if 30*(time.time()-start)>counter:
                    counter+=1
                    try:
                        frame_q.put(next(gen))
                    except StopIteration:
                        frame_q.put(np.zeros((*self.size,self.channels),dtype='u1'))
                        reader.close()
                        reader=None
                    
            time.sleep(0.0001)
            
            

    def update(self):
        try:
            frame= self.frame_q.get(False)
            if type(frame)!=type(None):
                if self.channels==3:
                    self.load(frame)
                else:
                    self.load(frame[:,:,0])
                    
                        
        except queue.Empty:
            pass

        


class VideoRecorder:
    def __init__(self,size):
        self.size=size
        self.q=queue.Queue()
        self.frame_q=queue.Queue()
        self.worker = threading.Thread(target=self.startThread,args=(self.q,self.frame_q,),daemon=True)
        self.worker.start()
        

    def startThread(self,q,frame_q):
        options={'-c:v':'libx264','-r':'30','-crf':'0'}
        record=False

        while True:
            try:
                frame=frame_q.get(False)
                if record:
                    writer.writeFrame(frame)
            except queue.Empty:
                pass

            try:
                msg,path=q.get(False)
                
                if msg:
                    writer=skvideo.io.FFmpegWriter(path,outputdict=options)
                    record=True
                else:
                    if record:
                        writer.close()

                    record=False

            except queue.Empty:
                pass
            
            time.sleep(0.0001)
    
    def start(self,path):
        self.q.put((True,path))

    def stop(self):
        self.q.put((False,None))

    def update(self,frame):
        self.frame_q.put(frame)


