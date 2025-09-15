import numpy as np
import cv2



class ImageManager:
    '''
    Class to be used to store the acquired images split in N channels and methods useful for object identification and roi creation
    '''

    def __init__(self, dim_h, dim_v,
                 roisize, min_object_area=10,
                 Nchannels = 2, dtype=np.uint16):

        self.image = np.zeros((Nchannels,dim_v,dim_h),dtype) # original 16 bit images from the N channels   
        self.dim_h = dim_h
        self.dim_v = dim_v
        
        self.contours = []        # list of contours of the detected objects
        self.cx = []             # list of the x coordinates of the centroids of the detected object
        self.cy = []             # list of the y coordinates of the centroids of the detected object
         
        self.roisize = roisize        # roi size
        self.min_object_area = min_object_area    # minimum area that the object must have to be recognized as a object
    
    def clear_countours(self):
        self.contours = []        
        self.cx = []             
        self.cy = []
        
    def find_object(self, ch):    # ch: selected channel       
        """ Input: 
             ch: channel to use to create the 8 bit image to process
        Determines if a region avove thresold is a object, generates contours of the objects and their centroids cx and cy      
        """          
    
        image8bit = (self.image[ch]/256).astype('uint8')
        
        _ret,thresh_pre = cv2.threshold(image8bit,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # ret is the threshold that was used, thresh is the thresholded image.     
        kernel  = np.ones((3,3),np.uint8)
        thresh = cv2.morphologyEx(thresh_pre,cv2.MORPH_OPEN, kernel, iterations = 2)
        # morphological opening (remove noise)
        cnts, _hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cx = []
        cy = []            
        contours = []
        roisize = self.roisize
        l = image8bit.shape
        
       
        for cnt in cnts:
            
            M = cv2.moments(cnt)
            if M['m00'] >  int(self.min_object_area):    # (M['m00'] gives the contour area, also as cv2.contourArea(cnt)
                #extracts image center
            
                x0 = int(M['m10']/M['m00']) 
                y0 = int(M['m01']/M['m00'])
                x = int(x0 - roisize) 
                y = int(y0 - roisize)
                w = h = roisize*2
                    
        
                if x>0 and y>0 and x+w<l[1]-1 and y+h<l[0]-1:    # only rois far from edges are considered
                    cx.append(x0)
                    cy.append(y0)
                    contours.append(cnt)
        
        self.cx = cx
        self.cy = cy 
        self.contours = contours  

    
    def draw_contours_on_image(self, image8bit):        
        """ Input: 
        img8bit: monochrome image, previously converted to 8bit
            Output:
        displayed_image: RGB image with rectangle annotations
        """  
        
        cx = self.cx
        cy = self.cy 
        roisize = self.roisize
        contours = self.contours
      
        displayed_image = cv2.cvtColor(image8bit,cv2.COLOR_GRAY2RGB)      
        
        for indx, _val in enumerate(cx):       
    
            x = int(cx[indx] - roisize) 
            y = int(cy[indx] - roisize)
         
            w = h = roisize*2
            
            displayed_image = cv2.drawContours(displayed_image, [contours[indx]], 0, (0,256,0), 2) 
            
            if indx == 0:
                color = (256,0,0)
            else: 
                color = (0,0,256)
                
            cv2.rectangle(displayed_image,(x,y),(x+w,y+h),color,1)
            
        return displayed_image
    
    
    
    def roi_creation(self, ch, cx, cy):
        """ Input: 
        ch: selected channel
        args: centroids cx and cy, if specified
            Output:
        rois: list of rois in the frame
        """          
        image16bit = self.image[ch]
    
        roisize = self.roisize
        rois = []
        
        for indx, _val in enumerate(cx):
            x = int(cx[indx] - roisize) 
            y = int(cy[indx] - roisize)
            w = h = roisize*2
            detail = image16bit [y:y+w, x:x+h]
            rois.append(detail)
                    
        return rois
   
    
    def highlight_channel(self,displayed_image):
        
         cv2.rectangle(displayed_image,(0,0),(self.dim_h-1,self.dim_v-1),(255,255,0),3) 
   
            
            
        