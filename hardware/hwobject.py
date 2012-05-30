'''
Created on May 21, 2012

@author: Jimmy
'''

'''
An abstract representation of a hardware object. Hardware objects are commonly
physical objects such as:

 - Deck light controller
 - Sweep Motor
 
Most hardware objects extend this class
'''
class HWObject(object):
    '''
    Create a new hardware object with a hardware controller interface reference (hw)
    '''
    def __init__(self, hw):
        '''
        Constructor
        '''
        self.hw = hw
        