'''
Created on Aug 03, 2018

@author: Andrea Bassi
'''

from ScopeFoundry.base_app import BaseMicroscopeApp


# Define your App that inherits from BaseMicroscopeApp
class VirtualImageGenTestApp(BaseMicroscopeApp):
    
    # this is the name of the microscope that ScopeFoundry uses 
    # when displaying your app and saving data related to it    
    name = 'vimage_gen_app'

    # You must define a setup() function that adds all the 
    # capabilities of the microscope and sets default settings    
    def setup(self):
        
        #Add Hardware components
        from vimage_gen_hw import VirtualImageGenHW
        self.add_hardware(VirtualImageGenHW(self))

        #Add Measurement components
        from vimage_gen_measure import VirtualImageGenMeasure
        self.add_measurement(VirtualImageGenMeasure(self))
        
        
if __name__ == '__main__':
    
    import sys
    app = VirtualImageGenTestApp(sys.argv)
    sys.exit(app.exec_())
    