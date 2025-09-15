from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import os
from image_data import ImageManager

class VirtualImageGenMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "vimage_gen_measure_objects_recognition"
    
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
        self.ui_filename = sibling_path(__file__, "camera.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface

        self.settings.New('saving_type', dtype=str, initial='None', choices=['None', 'Roi', 'Stack'])
        self.settings.New('roi_size', dtype=int, initial=20, vmin=2)
        self.settings.New('min_object_area', dtype=int, initial=10, vmin=4)
        self.settings.New('selected_channel', dtype=int, initial=0, vmin=0, vmax=1)
        self.settings.New('captured_objects', dtype=int, initial=0, ro=True)
        
        self.settings.New('frame_num', dtype=int, initial=50., vmin=1)
        self.settings.New('channel_num', dtype=int, initial=2, vmin=1)
        
        self.settings.New('xsampling', dtype=float, unit='um', initial=0.5)
        self.settings.New('ysampling', dtype=float, unit='um', initial=0.5)
        self.settings.New('zsampling', dtype=float, unit='um', initial=3.0)
    
        self.settings.New('auto_range', dtype=bool, initial=True)
        self.settings.New('auto_levels', dtype=bool, initial=True)
        self.settings.New('level_min', dtype=int, initial=60)
        self.settings.New('level_max', dtype=int, initial=4000)

        self.settings.New('measure', dtype=bool, initial=False)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        
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

        self.settings.measure.connect_to_widget(self.ui.measure_checkBox)
        self.settings.saving_type.connect_to_widget(self.ui.save_comboBox)

        self.settings.auto_levels.connect_to_widget(self.ui.autoLevels_checkbox)
        self.settings.auto_range.connect_to_widget(self.ui.autoRange_checkbox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) 
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) 
                
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
        self.display_update_period = self.settings['sampling_period']
        
        #time0 = time.time()
        ch = self.settings.selected_channel.val
        im = self.im.image[ch,...]
        if self.settings['auto_levels']:
            # if autolevel is ON, normalize the image to its max and min     
            level_min = np.amin(im)
            level_max = np.amax(im)
            self.settings['level_min'] = level_min    
            self.settings['level_max'] = level_max
        
        else:
            # if autolevel is OFF, normalize the image to the choosen values     
            level_min = self.settings['level_min']
            level_max = self.settings['level_max']
        
        # thresolding is required if autolevel is OFF; it could be avoided if autolevel is ON
        img_thres = np.clip(im, level_min, level_max)
        
        # conversion to 8bit is done here for compatibility with opencv    
        image8bit_normalized = ((img_thres-level_min+1)/(level_max-level_min+1)*255).astype('uint8') 
        
        # creation of the image with open cv annotations, ready to be displayed
        displayed_image = self.im.draw_contours_on_image(image8bit_normalized)
        
        self.imv.setImage(displayed_image,
                    autoLevels=False,
                    autoRange = self.settings.auto_range.val,
                    levels=(0,255))
        
        # print(f'Image displayed in {time.time()-time0:.3f} s')

        if self.settings['save_stack']:
            z_idx = self.frame_index
            c_idx = self.channel_index
            frames=self.settings['frame_num']
            channels=self.settings['channel_num']
            progress = (c_idx+z_idx*channels)*100/(frames*channels)
            self.settings['progress'] = progress # Set progress bar percentage complete
        
    def pre_run(self):
        # Acquire initial image (1 for each channel) to set up the Image Manager
        self.camera.camera_device.start_acquisition()    
        self.channel_index = 0
        while self.channel_index < self.settings.channel_num.val:
            img = self.camera.camera_device.get_frame()
            if self.channel_index == 0:
                self.im = ImageManager(
                            img.shape[1], img.shape[0],
                                self.settings.roi_size.val,
                                min_object_area = self.settings.min_object_area.val,
                                Nchannels=self.settings.channel_num.val,
                                dtype=img.dtype
                                )
            self.im.image[self.channel_index,...] = img
            self.channel_index +=1


    def run(self):
        
        while not self.interrupt_measurement_called:
            
            self.channel_index = 0

            while self.channel_index < self.settings.channel_num.val:
                img = self.camera.camera_device.get_frame()
                self.im.image[self.channel_index,...] = img
                self.channel_index +=1   
                
            if self.settings['measure'] and self.settings['saving_type'] == 'Roi':
                self.save_roi()
                break
            elif self.settings['measure'] and self.settings['saving_type'] == 'Stack':
                self.save_stack()
                break
            elif self.settings['measure']:
                self.measure()        
                break
            
            
            if self.interrupt_measurement_called:
                break

        self.camera.camera_device.stop_acquisition()  

    def save_roi(self):
        pass
    

    def measure(self):
        
        self.settings['captured_objects'] = 0

        while not self.interrupt_measurement_called:
            self.channel_index = 0
            
            while self.channel_index < self.settings.channel_num.val:
                
                img = self.camera.camera_device.get_frame()

                self.im.image[self.channel_index,...] = img

                time0 = time.time()
                if self.channel_index == self.settings.selected_channel.val:
                    self.im.find_object(self.settings.selected_channel.val)
        
                rois = self.im.roi_creation(self.channel_index, self.im.cx, self.im.cy)
                    
                self.settings['captured_objects'] = len(rois)

                self.channel_index +=1
                print(f'Channel {self.channel_index} acquired in {time.time()-time0:.3f} s')
                
            if self.interrupt_measurement_called or self.settings['measure'] == False:
                self.camera.camera_device.stop_acquisition()
                break
        
        self.settings['measure'] = False


    def save_stack(self):

        cnum=self.settings['channel_num']
        znum=self.settings['frame_num']

        try:
            images_h5 = self.init_h5_datasets(channels_number=cnum,
                                        z_number=znum)

            self.camera.camera_device.start_acquisition()
    

            
            self.frame_index = 0
            while self.frame_index < self.settings.frame_num.val:
                self.channel_index = 0 
                while self.channel_index < self.settings.channel_num.val:
                    
                    img = self.camera.camera_device.get_frame() # camera specific function
                    
                    self.im.image[self.channel_index,...] = img 
                    images_h5[self.channel_index][self.frame_index,:,:] = img
                    self.channel_index +=1
                    self.h5file.flush() # introduces a slight time delay but assures that images are stored continuosly 
                    if self.interrupt_measurement_called:
                        self.camera.camera_device.stop_acquisition()
                        break  
                self.frame_index +=1  

        finally:
            self.camera.camera_device.stop_acquisition()
            self.h5file.close()
            delattr(self, 'h5file')
            delattr(self, 'h5_group')
            self.settings['measure'] = False

    def create_group(self):

        if not os.path.isdir(self.app.settings['save_dir']):
            os.makedirs(self.app.settings['save_dir'])
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)


    def init_h5_datasets(self,channels_number=1,z_number=1,
                     imshape=None,dtype=None,name='image'):
        
        if not hasattr(self, 'h5_group'):
            self.create_group()

        if imshape is None:
            imshape = self.im.image.shape[1:]  # shape is [channels, height, width]
        shape=[z_number, imshape[0], imshape[1]]
    
        if dtype is None:
            dtype = self.im.image.dtype

        images_h5 = [] # image_h5 is a list of lists of h5 datasets
        
        for ch_idx in range(channels_number):
            dataset = self.h5_group.create_dataset(name  = f't0/c{ch_idx}/{name}', 
                                                        shape = shape,
                                                        dtype = dtype)  
            dataset.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
            images_h5.append(dataset)
        
        return images_h5