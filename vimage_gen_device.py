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
                 mean_particles = 10,
                 sizex = 512,
                 sizey = 256):
        """We would connect to the real-world here
        if this were a real device
        """
        self.noise_amplitude = noise_amplitude
        self.signal_amplitude = signal_amplitude
        self.mean_particles = mean_particles
        self.sizex = sizex
        self.sizey = sizey
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
        
    def write_sizex(self, sizex):
        self.sizex = sizex 

    def write_sizey(self, sizey):
        self.sizey = sizey


    def write_mean_particles(self, mean_particles):
        """
        A write function to change the device's mean number of particles
        normally this would talk to the real-world to change
        a setting on the device
        """
        self.mean_particles = mean_particles    

    def start_acquisition(self):
        self.frame_idx = 0
        pass

    def stop_acquisition(self):
        self.frame_idx = 0
        pass
           
    def get_frame(self):
        
        noise = np.random.rand(self.sizey, self.sizex) * self.noise_amplitude
        x = np.linspace(-self.sizex/2, self.sizex/2, self.sizex)
        y = np.linspace(-self.sizey/2, self.sizey/2, self.sizey)
        X, Y = np.meshgrid(x, y)
        # 2D Gaussian
        z = np.zeros((self.sizey, self.sizex))
        for _ in range(np.random.randint(self.mean_particles//2, self.mean_particles*3//2)):
            X0 = np.random.normal(scale=self.sizex/8.0)
            Y0 = np.random.normal(scale=self.sizey/8.0)
            sigma = np.random.normal(loc=self.sizex/128.0, scale=self.sizex/128.0)                
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
    