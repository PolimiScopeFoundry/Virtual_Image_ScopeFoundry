from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import os

class VirtualImageGenMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "virtual_image_measure_with_file_support"
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "random_images.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_roi', dtype=bool, initial=False)
        self.settings.New('frame_num', dtype=int, initial=50)
        self.settings.New('time_lapse_num', dtype=int, initial=20)
        self.settings.New('channel_num', dtype=int, initial=2)
        self.settings.New('xsampling', dtype=float, unit='um', initial=0.5)
        self.settings.New('ysampling', dtype=float, unit='um', initial=0.5)
        self.settings.New('zsampling', dtype=float, unit='um', initial=3.0)
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
              
        # Define how often to update display during a run
        self.display_update_period = 0.05 
        
        # Convenient reference to the hardware used in the measurement
        self.camera = self.app.hardware['virtual_image_gen']

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        self.camera.settings.amplitude.connect_to_widget(self.ui.amp_doubleSpinBox)
                
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.image_groupBox.layout().addWidget(self.imv)
        colors = [(0, 0, 0),
                  (45, 5, 61),
                  (84, 42, 55),
                  (150, 87, 60),
                  (208, 171, 141),
                  (255, 255, 255)
                  ]
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
        self.imv.setColorMap(cmap)
       
    
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        if hasattr(self,'img'):
            self.imv.setImage(self.img)
        
        if self.settings['save_h5']:
            z_idx = self.frame_index
            t_idx = self.time_lapse_index
            c_idx = self.channel_index
            frames=self.settings['frame_num']
            times=self.settings['time_lapse_num']
            channels=self.settings['channel_num']
            progress = (z_idx+c_idx*frames+t_idx*frames*channels)*100/(frames*times*channels)
            self.settings['progress'] = progress # Set progress bar percentage complete

            
    
    def run(self):

        self.frame_index = 0
        self.channel_index = 0
        self.time_lapse_index = 0

        self.camera.camera_device.start_acquisition()    

        while not self.interrupt_measurement_called:
            # defines a number of acquisitions to be done, then measurement will be repeated until interrupt is pressed
            
            data = self.camera.camera_device.get_frame()
            self.img = data               
            
            if self.settings['save_h5']:
                self.measure()
                self.camera.camera_device.stop_acquisition()
                break
                    
            if self.interrupt_measurement_called:
                self.camera.camera_device.stop_acquisition()
                break

    def measure(self):
        time0 = time.time()

        tnum = self.settings['time_lapse_num'] 
        cnum=self.settings['channel_num']
        znum=self.settings['frame_num']

        try:
            
            if self.settings['save_roi']:
                roi_h5 = self.init_h5_datasets(times_number=tnum,
                                        channels_number=cnum,
                                        z_number=znum, imshape= [150,150], name='roi')
            else:
                images_h5 = self.init_h5_datasets(times_number=tnum,
                                        channels_number=cnum,
                                        z_number=znum)

            

            self.camera.camera_device.start_acquisition()
            self.camera.camera_device.store_frame()
            
            self.time_lapse_index = 0
            while self.time_lapse_index < self.settings.time_lapse_num.val:
                self.channel_index = 0
                while self.channel_index < self.settings.channel_num.val:
                    self.frame_index = 0
                    while self.frame_index < self.settings.frame_num.val:        
                        self.img = self.camera.camera_device.get_stored_frame()
                        dataset_index=self.time_lapse_index*self.settings['channel_num'] + self.channel_index
                        if self.settings['save_roi']:
                            roi = self.img[50:200,50:200]    
                            roi_h5[dataset_index][self.frame_index,:,:] = roi
                        else:
                            images_h5[dataset_index][self.frame_index,:,:] = self.img
                        self.frame_index +=1
                        self.h5file.flush() # introduces a slight time delay but assures that images are stored continuosly 
                        if self.interrupt_measurement_called:
                            self.camera.camera_device.stop_acquisition()
                            break  
                    self.channel_index +=1  
                self.time_lapse_index +=1

        finally:
            self.camera.camera_device.stop_acquisition()
            self.h5file.close()
            delattr(self, 'h5file')
            delattr(self, 'h5_group')
            self.settings['save_h5'] = False
            print('Measurement execution time:',time.time()-time0)

    def create_group(self):
        if not os.path.isdir(self.app.settings['save_dir']):
            os.makedirs(self.app.settings['save_dir'])
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)


    def init_h5_datasets(self,times_number=1,channels_number=1,z_number=1,
                     imshape=None,dtype=None,name='image'):
        
        if not hasattr(self, 'h5_group'):
            self.create_group()

        if imshape is None:
            imshape = self.img.shape
        shape=[z_number, imshape[0], imshape[1]]
    
        if dtype is None:
            dtype = self.img.dtype

        images_h5 = [] # image_h5 is a list of lists of h5 datasets
        
        for tl_idx in range(times_number):
                     
            for ch_idx in range(channels_number):
                dataset = self.h5_group.create_dataset(name  = f't{tl_idx}/c{ch_idx}/{name}', 
                                                          shape = shape,
                                                          dtype = dtype)  
                dataset.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
                images_h5.append(dataset)
        
        return images_h5
