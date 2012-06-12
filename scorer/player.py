'''
Created on Apr 22, 2012

@author: Jimmy
'''
import pygame
import sys, re
from pygame.locals import *
import math
import splits

from frame import Frame

'''
Handles all player information including name and frame data.

There is one instantiation of this object per player. There are also shortcut
methods here to draw player information to the screen with ease.
'''
class Player(object):
    '''
    classdocs
    '''
    
    score_font = None;

    '''
    Create a new player object with the following attributes:
    name - The name of the player
    number - The number of the player (mostly auto-generated by caller)
    bowling_scorer - The bowling scorer instance to reference for data
    blacklight - Whether or not this player uses a blacklight
    '''
    def __init__(self, name, number, bowling_scorer, blacklight):
        '''
        Constructor
        '''
        
        # Make proper casing on the name
        
        name = name[0].capitalize() + name[1:]
        
        self.name = name
        self.number = number
        self.frames = []
        self.current_frame = 0
        self.current_roll = 0
        self.score_font = pygame.font.SysFont("Arial", 36, True)
        self.bowling_scorer = bowling_scorer
        self.current_score = ""
        self.blacklight = blacklight
        self.truScore = 0
        self.frames_completed_this_turn = 0
        
        self.rolls = [-1] * 21
        
        for i in range(10):
            f = Frame(i + 1)
            self.frames.append(f)
    
    '''
    Resets all player data to default settings. This is used to clear
    player data for a new game
    '''
    def reset(self):
        del self.frames[:]
        self.current_frame = 0
        self.current_roll = 0
        self.current_score = ""
        self.frames_completed_this_turn = 0
        self.rolls = [-1] * 21
        self.truScore = 0
        # Blank out all frame data
        for i in range(10):
            f = Frame(i + 1)
            self.frames.append(f)
        
    '''
    Adds a shot to the current player's game.
    
    The argument 'pinCount' is the number of pins scored to add to the current frame.
    
    Since the sum of 'shots' in a frame can only equal a max of 10, this function
    handles the logic of making sure each frame's shots only sum to ten.
    IE: a 9/ shows up here as '9 1'
    '''
    def addShot(self, pinCount, deck_state):
        self.rolls[self.current_roll] = pinCount
        
        if (self.current_frame == 9):
            if self.frames[self.current_frame].shots[0] == -1:
                self.frames[self.current_frame].shots[0] = pinCount
                self.frames[self.current_frame].isSplit = splits.isSplit(deck_state)
            elif self.frames[self.current_frame].shots[1] == -1:
                if pinCount == 10 and self.frames[self.current_frame].shots[0] != 10:
                    self.frames[self.current_frame].shots[1] = 10 - self.frames[self.current_frame].shots[0]
                else:
                    self.frames[self.current_frame].shots[1] = pinCount
            elif self.frames[self.current_frame].shots[2] == -1:
                if pinCount == 10 and self.frames[self.current_frame].shots[1] != 10 and \
                self.frames[self.current_frame].shots[0] + self.frames[self.current_frame].shots[1] != 10 and \
                self.frames[self.current_frame].shots[0] != 0:
                    self.frames[self.current_frame].shots[2] = 10 - self.frames[self.current_frame].shots[1]
                else:
                    self.frames[self.current_frame].shots[2] = pinCount
        else:
            if (self.frames[self.current_frame].shots[0] != -1 and \
                self.frames[self.current_frame].shots[0] != 10 and \
                pinCount == 10):
                self.frames[self.current_frame].shots[1] = 10 - self.frames[self.current_frame].shots[0]
            elif (self.frames[self.current_frame].shots[0] == -1):
                self.frames[self.current_frame].shots[0] = pinCount
                self.frames[self.current_frame].isSplit = splits.isSplit(deck_state)
            elif (self.frames[self.current_frame].shots[1] == -1):
                self.frames[self.current_frame].shots[1] = pinCount
            elif (self.current_frame == 9):
                self.frames[self.current_frame].shots[2] = pinCount
            
        if (self.frames[self.current_frame].hasBowled()):
            self.bowling_scorer.is_first_ball = True
            self.current_score = str(self.score(self.getGameString()))
            #self.frames[self.current_frame].score = self.current_score
            self.UpdateFrameScores()
            
            self.frames_completed_this_turn += 1
            if (self.frames_completed_this_turn == self.bowling_scorer.frames_per_turn or self.current_frame == 9):
                self.bowling_scorer.next_player()
                self.frames_completed_this_turn = 0
                
            self.bowling_scorer.end_game_if_over()
        elif self.current_frame == 9 and \
        self.frames[self.current_frame].shots[0] == 10 and \
        self.frames[self.current_frame].shots[1] == -1:
            self.bowling_scorer.is_first_ball = True
        elif self.current_frame == 9 and \
        self.frames[self.current_frame].shots[0] == 10 and \
        self.frames[self.current_frame].shots[1] == 10 and \
        self.frames[self.current_frame].shots[2] == -1:
            self.bowling_scorer.is_first_ball = True
        elif self.current_frame == 9 and \
        self.frames[self.current_frame].shots[0] + self.frames[self.current_frame].shots[1] == 10 and \
        self.frames[self.current_frame].shots[2] == -1:
            self.bowling_scorer.is_first_ball = True
        else:
            self.bowling_scorer.is_first_ball = False
            
        if (self.current_frame < 9 and self.frames[self.current_frame].hasBowled()):
            self.current_frame += 1
            
        self.current_roll += 1
        
    '''
    A half-assed attempt at score calculation 'per-frame'. This needs to be re-written.
    
    Basically calculates the score through a given frame. This screws up on marks
    but works otherwise.
    '''
    def calcScoreThruFrame(self, thru_frame):
        game_str = self.getGameString(thru_frame)
        return self.score(game_str)
    
    '''
    Get the visual representation of the game optionally through the given frame.
    '''
    def getGameString(self, thru_frame = 10):
        frame_str = []
        for f in self.frames:
            if not f.hasBowled() or f.number > thru_frame:
                continue
            
            current_frame = f.getFrameString()
            current_frame = current_frame.replace(' ', '')
            frame_str.append(current_frame)
            
        return ''.join(frame_str)
        
    '''
    Refreshes the players information (such as the current score)
    
    This is useful for refreshing player information on-screen after a score correction
    is made.
    '''
    def Refresh(self):
        self.current_score = str(self.score(self.getGameString()))
        
    '''
    Iterates through all frames and sets the score at that particular point in the game
    for each frame.
    
    This needs to be re-written... badly.
    '''
    def UpdateFrameScores(self):
        self.calculate()
        #for f in self.frames:
        #    if (f.hasBowled()):
        #        f.score = self.calcScoreThruFrame(f.number)
        #        if not f.isStrike() and not f.isSpare():
        #            f.score = self.calcScoreThruFrame(f.number)
                            
    def GetFrameMarkBonus(self, current_frame_idx, frames):
        if (current_frame_idx < 8):
            next_frame = frames[current_frame_idx + 1]
            next_frame_2 = frames[current_frame_idx + 2]
            if (next_frame.hasBowled()):
                if (next_frame.isStrike()):
                    if (next_frame_2.hasBowled()):
                        return 10 + next_frame_2.shots[0]
                    else:
                        return -1
                elif (next_frame.isSpare()):
                    return 10
                
                            
                        
    '''
    Draws the players frames and optionally the total on the screen.
    
    surface - The pygame surface to draw the frames on
    xscew - How far to move the x values
    yscew - How far to move the y values (used for centering on screen in score correct mode)
    showTotal - Whether or not to include the total in the 10th frame
    current_box - Where to draw the edit box behind the frame (0 for none). This is used in score correct mode.
    '''
    def DrawFrames(self, surface, xscew=0, yscew=0, showTotal=True, current_box=0):
        i = 0;
        # Draw frames at (136, 47) for P1F1
        # Frame width 67
        # Frame height 134
        for f in self.frames:
            #if not f.hasBowled:
            #    continue
            if ((current_box >= 20) and f.number == 10):
                # Draw a rect here
                if (current_box == 20):
                    box_pos = 28
                elif (current_box == 21):
                    box_pos = 50
                px = 136 + (i * 62) + xscew + box_pos
                py = 47 + (self.number * 133) + yscew
                
                pygame.draw.rect(surface, pygame.color.Color("blue"), (px,py,20,36))
            elif (current_box == (2 * f.number) or current_box == (2 * f.number) - 1):
                # Draw a rect here
                if (current_box == (2 * f.number)):
                    box_pos = 20
                else:
                    box_pos = 0
                px = 136 + (i * 62) + xscew + box_pos
                py = 47 + (self.number * 133) + yscew
                
                pygame.draw.rect(surface, pygame.color.Color("blue"), (px,py,20,36))
            
            if (f.isSplit == True):
                pygame.draw.circle(surface, pygame.color.Color("blue"), (135 + (i * 62) + xscew + 16, 50 + (self.number * 133) + yscew + 16), 18)
            
            text = self.score_font.render(f.getFrameString(), 1, (255, 255, 255))
            textpos = text.get_rect(x=136 + (i * 62) + xscew, y=47 + (self.number * 133) + yscew)
            surface.blit(text, textpos)
            
            # This is broken as crap, so we're not going to enable it
            if (f.shouldDisplay and f.number != 10):
                text = self.score_font.render(str(f.score), 1, (255, 255, 255))
                textpos = text.get_rect(x=136 + (i * 62) + xscew, y=92 + (self.number * 133) + yscew)
                surface.blit(text, textpos)
            
            i += 1
            
            if (f.number == 10):
                pass
        
        
        if showTotal == True:
            score_text = self.score_font.render(self.current_score, 1, (255, 255, 255))
            score_text_pos = text.get_rect(x=730, y=92 + (self.number * 133))
            surface.blit(score_text, score_text_pos)
            
    '''
    A wicked cool anonymous function to parse each frame's data from a string
    using a regex.
    '''
    parse_frames = lambda self, game: re.findall('X|..|.', game)
    
    '''
    Get the integer values of a single frame.
    The values returned here will always sum to 10.
    '''
    def frame_values(self, frame):
        if frame == "X":
            return [10]
        elif frame[-1] == "/":
            val = int(frame[0])
            return [val, 10 - val]
        else:
            return [int(s) for s in frame]
    
    '''
    Calculate the integer score of a given game string.
    '''
    def score(self, game):
        score = 0
        max_turns = 10 * 2 + 3
        bonus = [1] * max_turns
        i = 0
        
        game = game.replace('-', '0')
        frames = self.parse_frames(game)
        
        for count, frame in enumerate(frames):
            for v in self.frame_values(frame):
                score += v * bonus[i]
                i += 1
                
            if count < 9:
                if frame == "X":
                    bonus[i] += 1
                    bonus[i+1] += 1
                elif frame[-1] == "/":
                    bonus[i] += 1
                    
        return score
    
    
    def calculate(self):
        nextBall = None        # Hold value of next ball
        thirdBall = None       # Hold value of 3rd ball
        b2 = 0              # Hold index of next ball
        b3 = 0              # Hold index of 3rd ball
        totalScore = 0      # Total current score
        truScore = 0        # Total true score
        
        frameRolls = [""] * 21
        
        # First, clear out all of our score fields
        i = 0
        for f in self.frames:
            f.score = 0
            f.shouldDisplay = False
            if (f.isStrike()):
                frameRolls[i] = "x"
                i += 2
            elif (f.isSpare()):
                frameRolls[i] = f.shots[0]
                frameRolls[i+1] = "/"
                i += 2
            else:
                for s in f.shots:
                    if s != -1:
                        frameRolls[i] = s
                    i+=1
            
        for j in range(0,19,2):
            frameScore = 0
            shouldDisplay = False            
            
            # Check strike, and since j is even, it only checks the first ball of each frame
            if (frameRolls[j] == "x"):
                frameScore += 10
                truScore += 10
                if (j < 16): # Regular frame
                    b2 = j+1
                    b3 = j+2
                    nextBall = frameRolls[b3]
                    if (nextBall == "x"): # If the next ball is a strike, then take the third
                        b3 = j+4
                        thirdBall = frameRolls[b3]
                    else:
                        b3 = j+3
                        thirdBall = frameRolls[b3] # Otherwise, its the second ball in the next frame
                if (j == 16): # 9th frame
                    b2 = j+2
                    b3 = j+3
                    nextBall = frameRolls[b2] # Next ball is first ball in next frame
                    thirdBall = frameRolls[b3] # Third ball is 2nd ball in next frame
                if (j == 18): # 10th frame
                    b2 = j+1
                    b3 = j+2
                    nextBall = frameRolls[b2] # Next ball is actually next ball
                    thirdBall = frameRolls[b3] # Third ball is actually third ball
                    
                if (nextBall != "" and thirdBall != ""): # Next two balls have a value
                    if (nextBall == "x"): # Is the next ball a strike?
                        frameScore += 10
                        truScore += 10
                        if (thirdBall == "x"): # Is the third ball a strike too?
                            frameScore += 10
                            truScore += 10
                        else:
                            frameScore += int(thirdBall)    # Not a strike, just take thevalue
                            truScore += int(thirdBall)
                    else: # Must be a regular number
                        if (thirdBall == "/"): # Is it a spare?
                            frameScore += 10
                            truScore += 10
                        else: # Just an open frame
                            frameScore += int(nextBall) + int(thirdBall)
                            truScore += int(nextBall) + int(thirdBall)
                            
                    shouldDisplay = True
            else:
                b2 = j+1
                b3 = j+2
                if (frameRolls[j] != "" and frameRolls[b2] == ""):
                    truScore += int(frameRolls[j])
                else:
                    if (frameRolls[j] != "" and frameRolls[b2] != ""): # Not a strike, so we get a spare or open frame
                        if (frameRolls[b2] == "/"): #We got a spare
                            frameScore += 10
                            truScore += 10
                            if (frameRolls[b3] != ""): # Check the next ball
                                if (frameRolls[b3] == "x"): # Next ball is a strike
                                    frameScore += 10
                                    truScore += 10
                                    shouldDisplay = True
                                else: # Next ball isn't a strike, just take the value
                                    frameScore += int(frameRolls[b3])
                                    truScore += int(frameRolls[b3])
                                    shouldDisplay = True
                        else: # This frame is an open frame, just add the two values
                            frameScore += int(frameRolls[j]) + int(frameRolls[b2])
                            truScore += int(frameRolls[j]) + int(frameRolls[b2])
                            shouldDisplay = True
            totalScore += frameScore # Keep running total of our score
            self.truScore = truScore
            if (shouldDisplay):
                k = math.ceil(j / 2.0)
                k = int(k)
                self.frames[k].score = totalScore
                self.frames[k].shouldDisplay = True
