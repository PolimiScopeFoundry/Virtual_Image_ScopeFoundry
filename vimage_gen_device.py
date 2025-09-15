import numpy as np
import time
import pyqtgraph as pg

class VirtualImageGenDevice(object):
    """
    This is the low level dummy device object.
    Typically when instantiated it will connect to the real-world
    Methods allow for device read and write functions
    """
        
    def __init__(self, 
                 noise_amplitude = 100.0,
                 signal_amplitude = 200.0,
                 size = 512):
        """We would connect to the real-world here
        if this were a real device
        """
        self.noise_amplitude = noise_amplitude
        self.signal_amplitude = signal_amplitude
        self.size = size
        self.frame_idx = 0

    def write_signal_amp(self, amplitude):
        """
        A write function to change the device's amplitude
        normally this would talk to the real-world to change
        a setting on the device
        """
        self.signal_amplitude = amplitude

    
    def write_noise_amp(self, amplitude):
        """
        A write function to change the device's amplitude
        normally this would talk to the real-world to change
        a setting on the device
        """
        self.noise_amplitude = amplitude
        
    def write_size(self, size):
        """
        A write function to change the device's size
        normally this would talk to the real-world to change
        a setting on the device
        """
        self.size = size 


    def start_acquisition(self):
        self.frame_idx = 0
        pass

    def stop_acquisition(self):
        self.frame_idx = 0
        pass
           
    def get_frame(self):
        
        noise = np.random.rand(self.size, self.size) * self.noise_amplitude
        x = np.linspace(-self.size/2, self.size/2, self.size)
        y = np.linspace(-self.size/2, self.size/2, self.size)
        X, Y = np.meshgrid(x, y)
        # 2D Gaussian
        z = np.zeros((self.size, self.size))
        for _ in range(np.random.randint(5,10)):
            X0 = np.random.normal(scale=self.size/8.0)
            Y0 = np.random.normal(scale=self.size/8.0)
            sigma = np.random.normal(loc=self.size/128.0, scale=self.size/128.0)                
            z += np.exp(-((X-X0)**2 + (Y-Y0)**2) / (2*sigma**2))
        if self.frame_idx%2==0:
            img = z *self.signal_amplitude + noise + 1
        elif self.frame_idx%2==1:
            img = noise + 1
        self.frame_idx += 1
        return np.uint16(img)
    
    def store_frame(self):
        self._frame = self.get_frame()
    
    def get_stored_frame(self):
        return(self._frame)
    
if __name__ == '__main__':
    
    vig = VirtualImageGenDevice(signal_amplitude=100, noise_amplitude=10,size = 300)
    acquired_im = vig.get_frame()
    print (np.amax(acquired_im))
    