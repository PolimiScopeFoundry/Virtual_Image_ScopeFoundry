from ScopeFoundry import HardwareComponent
from vimage_gen_device import VirtualImageGenDevice
import numpy as np


class VirtualImageGenHW(HardwareComponent):
    
    ## Define name of this hardware plug-in
    name = 'virtual_image_gen'
    
    def setup(self):
        # Define your hardware settings here.
        # These settings will be displayed in the GUI and auto-saved with data files
                
        self.settings.New(name='signal_amplitude', initial=500.0, dtype=float, ro=False, reread_from_hardware_after_write=True)
        self.settings.New(name='noise_amplitude', initial=100.0, dtype=float, ro=False, reread_from_hardware_after_write=True)
        self.settings.New(name='size', initial=520, dtype=int, ro=False, reread_from_hardware_after_write=True)    
 
    def connect(self):
        # Open connection to the device:
        self.camera_device = VirtualImageGenDevice(
            signal_amplitude = self.settings.signal_amplitude.val,
            noise_amplitude = self.settings.noise_amplitude.val,
            size = self.settings.size.val               
            )
        
        # Connect settings to hardware:
        self.settings.signal_amplitude.connect_to_hardware(
            write_func = self.camera_device.write_signal_amp
            )
        
        self.settings.noise_amplitude.connect_to_hardware(
            write_func = self.camera_device.write_noise_amp
            )

        self.settings.size.connect_to_hardware(
            write_func  = self.camera_device.write_size
            )
                            
        #Take an initial sample of the data.
        self.read_from_hardware()
        
    def disconnect(self):
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        # Don't just stare at it, clean up your objects when you're done!
        if hasattr(self, 'camera_device'):
            del self.camera_device