'''
Created on May 21, 2012

@author: Jimmy
'''

import serial


'''
Interfaces to all of our arduino pins. The function of this class is very simple.
It only serves to set pins high/low and read the state of the I/O pins.

This class can also send/recv data over the serial interface to the Arduino.
'''
class Arduino(object):

    '''
    Create a new Arduino interface on the given COM port at the given baud rate
    '''
    def __init__(self, comport, baudrate=9600):
        '''
        Constructor
        '''
        try:
            self.connection = serial.Serial(comport,baudrate)
            print "Hardware initialized."
        except:
            self.connection = None
            print "Hardware initialization failed. Running without hardware controller."
        
    '''
    Sets the given pin to the given mode (0 = low, 1 = high)
    '''
    def SetDigitalPin(self, pin, mode):
        spin = str(pin)
        spin = spin.zfill(2)
        self.Writeln("WD" + spin + str(mode))
        
    '''
    Returns True if the Arduino's serial bus has data ready to be read.
    '''
    def HasData(self):
        return (self.connection != None and self.connection.inWaiting() > 0)
    
    '''
    Sends a reset command to the Arduino and restarts the interface communication.
    '''
    def Reset(self):
        self.Writeln("RS")
        
    '''
    Write a command to the Arduino over the serial bus.
    '''
    def Writeln(self, data):
        if (self.connection == None): return
        self.connection.write(data)
        self.connection.write('\n')
        
    '''
    Close communication with the Arduino. This attempts to send a reset command to
    reset the Arduino to a known state before terminating.
    '''
    def Close(self):
        self.Reset()
        if (self.connection != None):
            self.connection.close()