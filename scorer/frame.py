'''
Created on Apr 22, 2012

@author: Jimmy
'''

class Frame(object):
    '''
    classdocs
    '''

    #hasBowled = False   # Have we bowled this frame yet?
    #number = 1          # Frame number
    #shots = []          # List of shots

    def __init__(self, number):
        '''
        Constructor
        '''
        self.number = number
        self.shots = []
        self.score = 0
        self.shouldDisplay = False
        
        if (number == 10):
            self.shots.append(-1)
            self.shots.append(-1)
            self.shots.append(-1)
        else:
            self.shots.append(-1)
            self.shots.append(-1)
            
            
    def hasBowled(self):
        if self.number == 10:
            if (self.shots[0] == 10 and (self.shots[1] == -1 or self.shots[2] == -1)):
                return False
            if (self.shots[0] == 10 and self.shots[1] != -1 and self.shots[2] != -1):
                return True
            if (self.shots[0] != 10 and self.shots[1] + self.shots[0] == 10 and self.shots[2] != -1):
                return True
            if (self.shots[0] != -1 and self.shots[1] != -1 and self.shots[2] != -1):
                return True
            if (self.shots[0] != -1 and self.shots[1] != -1 and self.shots[0] + self.shots[1] != 10):
                return True
            
            return False        
        
        if self.shots[0] == 10:
            return True
        
        return self.shots[0] != -1 and self.shots[1] != -1
        
            
    def setFirstBall(self, pinCount):
        self.shots[0] = pinCount
        
    def setSecondBall(self, pinCount):
        self.shots[1] = pinCount
        
    def setThirdBall(self, pinCount):
        if (self.number == 10):
            self.shots[2] = pinCount
            
    def getFirstBall(self):
        return self.shots[0]
    
    def getSecondBall(self):
        return self.shots[1]
    
    def getThirdBall(self):
        if (self.number == 10):
            return self.shots[2]
        else:
            return -1
        
    def getFrameString(self):
        frame_str = []
        
        if (self.shots[0] == -1):
            return ""
        
        if (self.number != 10):
        
            if (self.shots[0] == 10):
                frame_str.append("X")
            else:
                if (self.shots[0] == 0):
                    frame_str.append("-")
                else:
                    frame_str.append(str(self.shots[0]))
                
                
                if (self.shots[0] + self.shots[1] == 10):
                    frame_str.append("/")
                elif (self.shots[1] == 0):
                    frame_str.append("-")
                elif (self.shots[1] != -1):
                    frame_str.append(str(self.shots[1]))
                else:
                    frame_str.append("")
        else:
            # 10th frame possibilities
            # --
            # -/X
            # X9/
            # X-/
            # If the sum of the first 2 shots is a 10, we have a mark somewhere
            
            # [--]
            # [9-]
            # [-9]
            
            # First, account for all 10th frames where there's no mark
            if (self.shots[0] + self.shots[1] < 10):
                frame_str.append(self.getSymbol(self.shots[0]))
                frame_str.append(self.getSymbol(self.shots[1]))
            else:
                # We had a mark somewhere
                # First, was the first ball a strike?
                if (self.shots[0] == 10):
                    # The first ball was a strike
                    frame_str.append(self.getSymbol(self.shots[0]))
                    # Was the second ball a strike?
                    if (self.shots[1] == 10):
                        # The second ball was a strike, put it in and slap on the last frame
                        frame_str.append(self.getSymbol(self.shots[1]))
                        frame_str.append(self.getSymbol(self.shots[2]))
                    else:
                        # The second ball was not a strike, check for count and spare
                        frame_str.append(self.getSymbol(self.shots[1]))
                        # Was the third a spare from the second ball?
                        if (self.shots[1] + self.shots[2] == 10):
                            frame_str.append("/")
                        else:
                            # Nope, just another count
                            frame_str.append(self.getSymbol(self.shots[2]))
                    pass
                else:
                    # The first two balls were a count and spare
                    frame_str.append(str(self.shots[0]))
                    frame_str.append("/")
                    frame_str.append(self.getSymbol(self.shots[2]))
            
                
            
        return ' '.join(frame_str)
    
    def isSpare(self):
        return (self.shots[0] + self.shots[1] == 10 and self.shots[0] != 10)
    
    def isStrike(self):
        return (self.shots[0] == 10)
    
    def makeSpare(self):
        self.shots[1] = 10 - self.shots[0]
        
    def makeStrike(self):
        self.shots[0] = 10
        self.shots[1] = -1
    
    def getSymbol(self, pinCount):
        if (pinCount == 0):
            return "-"
        elif (pinCount == 10):
            return "X"
        elif (pinCount == -1):
            return ""
        else:
            return str(pinCount)

