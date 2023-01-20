import numpy as np
import cv2


def extract_max_contour(frame,min_area):
    C, hierarchy = cv2.findContours(frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
    areas=[np.abs(np.dot(c[:,0,0],np.roll(c[:,0,1],1))-np.dot(c[:,0,1],np.roll(c[:,0,0],1))) for c in C]
    filtered_areas=[(i,a) for i,a in enumerate(areas) if a>min_area]
    
    if len(filtered_areas):
        f_indices,f_areas=zip(*filtered_areas)
        return C[f_indices[np.argmax(f_areas)]]
        

    return np.empty((0,1,2),dtype='i2')
         
def extract_contours(frame,min_area):
    C, hierarchy = cv2.findContours(frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
    areas=[np.abs(np.dot(c[:,0,0],np.roll(c[:,0,1],1))-np.dot(c[:,0,1],np.roll(c[:,0,0],1))) for c in C]
    return [C[i] for i,a in enumerate(areas) if a>min_area]
    




            
    