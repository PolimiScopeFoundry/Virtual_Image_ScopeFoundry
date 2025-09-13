import numpy as np
import time
import pyqtgraph as pg

class VirtualImageGenDevice(object):
    """
    This is the low level dummy device object.
    Typically when instantiated it will connect to the real-world
    Methods allow for device read and write functions
    """
        
    def __init__(self, amplitude=1.0, size = 500):
        """We would connect to the real-world here
        if this were a real device
        """
        self.write_amp(amplitude)
        self.write_size(size)
        
    
    def write_amp(self, amplitude):
        """
        A write function to change the device's amplitude
        normally this would talk to the real-world to change
        a setting on the device
        """
        self._amplitude = amplitude
        
    def write_size(self, size):
        """
        A write function to change the device's size
        normally this would talk to the real-world to change
        a setting on the device
        """
        self._size = size 


    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass
           
    def get_frame(self):
        """ Acts like the device is measuring random images
                """
        noise = np.random.normal(size=(self._size, self._size)) * self._amplitude 
        img = pg.gaussianFilter(np.random.normal(size=(self._size, self._size)), (5, 5)) * 20 + 100
        tot = img+noise
        time.sleep(0.0001)
        return np.uint16(tot)
    
    def store_frame(self):
        self._frame = self.get_frame()
    
    def get_stored_frame(self):
        return(self._frame)
    
if __name__ == '__main__':
    
    vig = VirtualImageGenDevice(amplitude=2.0, size = 10)
    acquired_im = vig.get_frame()
    print (acquired_im)
        