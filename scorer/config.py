'''
Created on May 1, 2012

@author: Compy
'''

import ConfigParser
import ast

class Config(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.config = None
        
    def load(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read("config.cfg")
        
    def getvalue(self, section, key):
        if self.config == None:
            return None
        
        return self.config.get(section, key)
    
    def getboolean(self, section, key):
        if self.config == None:
            return False
        
        try:
            return self.config.getboolean(section, key)
        except:
            return False
    
    def gettuple(self, section, key):
        if self.config == None:
            return None
        
        try:
        
            val = self.config.get(section, key)
            if (val == None): 
                return None
            
            return ast.literal_eval(str(val))
        except:
            return None
    
    def setvalue(self, section, key, value):
        if self.config == None:
            return
        
        self.config.set(section, key, value)
        
    def save(self):
        with open('config.cfg', 'wb') as configfile:
            self.config.write(configfile)
        
    def reset(self):
        if not self.config == None:
            del self.config
            
        self.config = ConfigParser.RawConfigParser()
        self.config.add_section("Camera")
        self.config.set("Camera", "size", (320,240))
        self.config.set("Camera", "detect_color", (255,255,255))
        self.config.set("Camera", "threshold_detect", (150, 150, 140))
        self.config.set("Camera", "other_colors_nondetect", (0,0,0))
        
        self.config.add_section("Screen")
        self.config.set("Screen", "size", (800, 600))
        
        self.config.add_section("Calibration")
        for i in range(1,11):
            self.config.set("Calibration", "point_" + str(i), (0,i * 15))
        
        self.config.set("Calibration", "point_size", 5)
        self.config.set("Calibration", "min_points_to_trigger", 15)
        
        self.save()
        