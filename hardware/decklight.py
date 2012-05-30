'''
Created on May 21, 2012

@author: Jimmy
'''

from hwobject import *

'''
Represents a piece of decklight hardware that switches between black and white
deck lights.
'''
class DeckLight(HWObject):
    
    '''
    Create a new DeckLight controller
    hw - Hardware controller (Arduino class) to reference/send commands to
    controlport - The pin on the control board that connects to the control box for the deck lights.
    '''
    def __init__(self, hw, controlport=8):
        '''
        Constructor
        '''
        self.controlport = controlport
        super(DeckLight, self).__init__(hw)
        self.is_currently_blacklight = False
        
    def Blacklight(self):
        if (not self.is_currently_blacklight):
            self.hw.SetDigitalPin(self.controlport, 1)
            self.is_currently_blacklight = True
        
    def Whitelight(self):
        if (self.is_currently_blacklight):
            self.hw.SetDigitalPin(self.controlport, 0)
            self.is_currently_blacklight = False
        