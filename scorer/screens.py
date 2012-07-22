'''
Created on May 1, 2012

@author: Compy
'''

import os, sys, platform, math
import pygame
import pygame.camera
import pygame.time
import splits
from pygame.locals import *
from ui_components import *
from functools import partial
from scorer import ui_components

SCREEN_MODE_FADEIN = 0
SCREEN_MODE_FADEOUT = 1
SCREEN_MODE_DISPLAY = 2

'''
Abstract representation of a screen. All screens extend this class.

This class maintains several internal references for convenience as well as handles
the underlying fade effects for screen transitions. Underlying UI components such as
text boxes, check boxes, etc are maintained within this class.

This class also dispatches events to the underlying components.
'''
class Screen(object):
    screen_manager = None
    bowling_scorer = None
    
    '''
    Create a new screen object with the given priority
    
    manager - The screen manager to reference
    priority - The layer position of the screen
    '''
    def __init__(self, manager, priority):
        self.screen_manager = manager
        self.bowling_scorer = manager.bowling_scorer
        self.priority = priority
        self.components = []
        self.mode = SCREEN_MODE_FADEIN
        self.fade_step = 0
        self.transition_length = 10
        self.alpha = 0
        
    '''
    Draw the screen on the given surface
    '''
    def Draw(self, screen_surface):
        for component in self.components:
            component.Draw(screen_surface)
    
    '''
    Update the display logic. This is run once every tick in the game loop... keep this
    moving along quickly otherwise general slowness will occur.
    
    This mostly handles underlying transition effects (updating alpha values for fade ins/outs)
    '''
    def Update(self, game_time):
        for component in self.components:
            component.Update(game_time)
            
        if self.mode != SCREEN_MODE_DISPLAY:
            self.fade_step += 1
            
        if self.fade_step > self.transition_length:
            if self.mode != SCREEN_MODE_FADEOUT:
                self.alpha = 255
                self.mode = SCREEN_MODE_DISPLAY
            else:
                self.alpha = 0
        else:
            self.alpha = int(round((float(self.fade_step)/self.transition_length)*255.0))
            if self.mode == SCREEN_MODE_FADEOUT:
                self.alpha = 255 - self.alpha
            
    
    '''
    Dispatch the pygame event to this screen's underlying components.
    This method dispatches mostly key press events and mouse movements.
    '''
    def HandleEvent(self, e):
        if (e.type == KEYDOWN):
            for component in self.components:
                component.HandleKeyPress(e.key)
    
    '''
    A method to be overridden in extended classes that is fired when the screen
    manager shows this screen.
    '''    
    def ScreenShown(self):
        pass
    
    '''
    A method to be overridden in extended classes that is fired when the program
    is shutting down to eliminate any data structures or memory hogging objects.
    '''
    def Cleanup(self):
        pass
    
    '''
    A generic method that tells the screen to start fading in.
    '''
    def FadeIn(self):
        self.alpha = 0
        self.fade_step = 0
        self.mode = SCREEN_MODE_FADEIN
    
    '''
    A generic method that tells the screen to start fading out.
    '''
    def FadeOut(self):
        self.alpha = 255
        self.fade_step = 0
        self.mode = SCREEN_MODE_FADEOUT
        
    def _getMaxComponentID(self):
        max_component_id = 0
        for e in self.components:
            if e.taborder > max_component_id:
                max_component_id = e.taborder
        return max_component_id
    
'''
The boot screen that shows the splash imagery while the system boots up
'''
class ErrorScreen(Screen):
    error_string = ""
    def __init__(self, screen_manager):
        super(ErrorScreen, self).__init__(screen_manager, 8)
        self.error_font = pygame.font.SysFont("Arial", 18, False, True)
        self.title_font = pygame.font.SysFont("Arial", 48, True)
        
    def Draw(self, screen_surface):
        super(ErrorScreen, self).Draw(screen_surface)
        
        pygame.draw.rect(screen_surface, pygame.color.Color("red"), (0,0,800,600), 5)
        
        text = self.title_font.render("Fatal Error", 1, (255, 0, 0))
        textpos = text.get_rect(centerx=400, y=10)
        screen_surface.blit(text, textpos)
        
        text = self.error_font.render(ErrorScreen.error_string, 1, (255, 255,255))
        textpos = text.get_rect(centerx=400, y=100)
        screen_surface.blit(text, textpos)
        
    def Update(self, game_time):
        super(ErrorScreen, self).Update(game_time)
        
    
'''
The boot screen that shows the splash imagery while the system boots up
'''
class BootScreen(Screen):
    def __init__(self, screen_manager):
        super(BootScreen, self).__init__(screen_manager, 8)
        self.bg = pygame.image.load("splash.jpg")
        self.version_font = pygame.font.SysFont("Arial", 18, False, True)
        self.welcome_font = pygame.font.SysFont("Arial", 48, True)
        self.display_time = 8000 # 8000ms = 8s
        self.time_shown = 0
        self.center_name = self.bowling_scorer.config.getvalue("System","center_name")
        
    def Draw(self, screen_surface):
        super(BootScreen, self).Draw(screen_surface)
        self.bg.set_alpha(self.alpha, RLEACCEL)
        
        screen_surface.blit(self.bg, (0,0))
        
        text = self.version_font.render("1.1 BETA", 1, (255, 255, 255))
        textpos = text.get_rect(x=700, y=550)
        screen_surface.blit(text, textpos)
        
    def Update(self, game_time):
        super(BootScreen, self).Update(game_time)
        
        if game_time - self.time_shown > self.display_time and self.mode != SCREEN_MODE_FADEOUT:
            self.FadeOut()
        if self.mode == SCREEN_MODE_FADEOUT and self.bg.get_alpha() == 0:
            self.screen_manager.RemoveScreen(self)
            self.screen_manager.score.FadeIn()
            self.screen_manager.AddScreen(self.screen_manager.score)
        
    def ScreenShown(self):
        self.time_shown = self.screen_manager.game_time
        self.FadeIn()
        
        
'''
This is the main screen that shows the players and their scores. This is the "beef" of
the program's display.

This also dispatches key events to switch to the menu option screen when the space
bar is pressed.
'''
class ScoreScreen(Screen):
    '''
    classdocs
    '''
    # PATH SETUP
    if (platform.system() == "Windows"):
        SCOREGRID_PATH = "scoregrids\\"
    else:
        SCOREGRID_PATH = "scoregrids/"
    
    # THEME SETUP
    THEME = "blue"

    def __init__(self, screen_manager):
        '''
        Constructor
        '''
        
        super(ScoreScreen, self).__init__(screen_manager, 10)
        
        # If the current system is Windows, load up the paths with back slashes
        if (platform.system() == "Windows"):
            self.bg_noPlayer = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "\\noplayer.png").convert()
            self.bg_p1 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "\\p1.png").convert()
            self.bg_p2 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "\\p2.png").convert()
            self.bg_p3 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "\\p3.png").convert()
            self.bg_p4 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "\\p4.png").convert()
        # If the current system is Linux, load up the assets with forward slashes
        else:
            self.bg_noPlayer = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "/noplayer.png").convert()
            self.bg_p1 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "/p1.png").convert()
            self.bg_p2 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "/p2.png").convert()
            self.bg_p3 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "/p3.png").convert()
            self.bg_p4 = pygame.image.load(self.SCOREGRID_PATH + self.THEME + "/p4.png").convert()
        
        # Set up display fonts for this screen
        self.score_font = pygame.font.SysFont("Arial", 36, True)
        self.name_font = pygame.font.SysFont("Arial", 36, True, True)
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        
        # The default background is one with no player since none have been added
        self.current_bg = self.bg_noPlayer
        
        # Default to showing the help text
        # The marquee will only be shown at the end of the game
        self.show_help_text = True
        self.show_marquee = False
        self.show_pindicator = False
        
        # The start position of the scrolling marquee seen at the end of each game
        self.marquee_x = 800
        self.marquee_y = 565
        # Number in ms to slide the marquee. Leave this as is.
        self.marquee_update_interval = 50
        self.last_marquee_update = 0
        self.marquee_width = 800
        self.marquee_text = self.text_font.render(self.bowling_scorer.config.getvalue("System","end_of_game_marquee"), 1, (0, 0, 0))
        self.marquee_width = -1 * self.marquee_text.get_rect().width

        
    def Draw(self, screen_surface):
        super(ScoreScreen, self).Draw(screen_surface)
        
        if (self.bowling_scorer.current_player == -1):
            if (self.mode != SCREEN_MODE_DISPLAY):
                self.bg_noPlayer.set_alpha(self.alpha, RLEACCEL)
            screen_surface.blit(self.bg_noPlayer, (0,0))
        elif (self.bowling_scorer.current_player == 0):
            if (self.mode != SCREEN_MODE_DISPLAY):
                self.bg_p1.set_alpha(self.alpha, RLEACCEL)
            screen_surface.blit(self.bg_p1, (0,0))
        elif (self.bowling_scorer.current_player == 1):
            if (self.mode != SCREEN_MODE_DISPLAY):
                self.bg_p2.set_alpha(self.alpha, RLEACCEL)
            screen_surface.blit(self.bg_p2, (0,0))
        elif (self.bowling_scorer.current_player == 2):
            if (self.mode != SCREEN_MODE_DISPLAY):
                self.bg_p3.set_alpha(self.alpha, RLEACCEL)
            screen_surface.blit(self.bg_p3, (0,0))
        elif (self.bowling_scorer.current_player == 3):
            if (self.mode != SCREEN_MODE_DISPLAY):
                self.bg_p4.set_alpha(self.alpha, RLEACCEL)
            screen_surface.blit(self.bg_p4, (0,0))
        
        
        # Draw the players' names and frame data
        i = 0
        for p in self.bowling_scorer.players:
            text = self.name_font.render(p.name, 1, (255, 255, 255))
            textpos = text.get_rect(centerx=59, centery=98 + (i * 132))
            screen_surface.blit(text, textpos)
            p.DrawFrames(screen_surface)
            i += 1
            
        # Show the help text at the bottom of the screen if we're supposed to
        if self.show_help_text:
            text = self.text_font.render("[SPACE] - Access Menu Options", 1, (0, 0, 0))
            textpos = text.get_rect(centerx=400, y=565)
            screen_surface.blit(text, textpos)
            
        # Show the marquee if we're supposed to at its current position
        if self.show_marquee:
            textpos = self.marquee_text.get_rect(x=self.marquee_x,y=self.marquee_y)
            screen_surface.blit(self.marquee_text, textpos)
    
    def Update(self, game_time):
        super(ScoreScreen,self).Update(game_time)
        
        # If the marquee slide interval has passed, nudge it along the sliding track
        if (game_time - self.last_marquee_update >= self.marquee_update_interval):
            self.marquee_x -= 2
            
            if self.marquee_x <= self.marquee_width:
                self.marquee_x = 800
                
            self.last_marquee_update = game_time
            
    
    def HandleEvent(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_s and self.bowling_scorer.current_player != -1:
                self.ScoreFromCamera()
            if (e.key == K_SPACE):
                self.screen_manager.RemoveScreen(self)
                self.screen_manager.AddScreen(self.screen_manager.mainmenu)
                
    def ScoreFromCamera(self):
        player = self.bowling_scorer.players[self.bowling_scorer.current_player]
        if self.bowling_scorer.is_first_ball == True:
            pinCount = self.bowling_scorer.pinCounter.getPinCount(False)
            
            '''
            If this is the first ball, AND we're doing no-tap, check things out here
            and adjust the count as needed.
            '''
            if (pinCount >= self.bowling_scorer.min_pincount_strike):
                pinCount = 10
            
            if (pinCount < 10):
                
                self.screen_manager.pindication.show_pins = self.bowling_scorer.pinCounter.pin_display
                self.screen_manager.pindication.FadeIn()
                self.screen_manager.AddScreen(self.screen_manager.pindication)
                self.screen_manager.RemoveScreen(self)
        else:
            pinCount = self.bowling_scorer.pinCounter.getPinCount(True)
            
        player.addShot(pinCount,self.bowling_scorer.pinCounter.pin_display)
        
    def RefreshPlayerInfo(self):
        for p in self.bowling_scorer.players:
            p.UpdateFrameScores()
            p.Refresh()

class MainMenuScreen(Screen):
    '''
    classdocs
    '''


    def __init__(self,screen_manager):
        '''
        Constructor
        '''
        super(MainMenuScreen, self).__init__(screen_manager, 9)
        self.menu_font = pygame.font.SysFont("Arial", 24, True)
        self.menu = Menu(self.onMenuClosed, (230,230,230), 250, 250)
        #self.menu.AddMenuItem("Reset Pins", self.onResetPinsSelected)
        self.menu.AddMenuItem("Add Bowler", self.onAddBowlerSelected)
        self.menu.AddMenuItem("Remove Bowler", self.onRemoveBowlerSelected)
        self.menu.AddMenuItem("Skip Bowler", self.onSkipBowlerSelected)
        self.menu.AddMenuItem("Score Correction", self.onScoreCorrectionSelected)
        self.menu.AddMenuItem("New Game", self.onNewGameSelected)
        self.menu.AddMenuItem("Manager Functions", self.onAdvancedSelected)
        self.menu.AddMenuItem("Exit Menu", self.onMenuClosed)
        
        self.components.append(self.menu)
    
    def onScoreCorrectionSelected(self):
        if (len(self.bowling_scorer.players) == 0): return
        self.screen_manager.AddScreen(self.screen_manager.score_correct_select)
        self.Close()
    
    def onNewGameSelected(self):
        if (len(self.bowling_scorer.players) == 0): return
        self.bowling_scorer.new_game()
        self.screen_manager.score.show_help_text = True
        self.screen_manager.score.show_marquee = False
        self.screen_manager.score.FadeIn()
        self.screen_manager.AddScreen(self.screen_manager.score)
        self.Close()
    
    def onSkipBowlerSelected(self):
        if (len(self.bowling_scorer.players) == 0): return
        self.screen_manager.skip_bowler.FadeIn()
        self.screen_manager.AddScreen(self.screen_manager.skip_bowler)
        self.Close()
    
    def onRemoveBowlerSelected(self):
        if (len(self.bowling_scorer.players) <= 1): return
        self.screen_manager.remove_bowler.FadeIn()
        self.screen_manager.AddScreen(self.screen_manager.remove_bowler)
        self.Close()
    
    def onAddBowlerSelected(self):
        if (len(self.bowling_scorer.players) == 4): return
        self.screen_manager.add_bowler.FadeIn()
        self.screen_manager.AddScreen(self.screen_manager.add_bowler)
        self.Close()
    
    def onAdvancedSelected(self):
        #advanced_screen = advanced.AdvancedScreen(self.screen_manager)
        self.screen_manager.AddScreen(self.screen_manager.advanced)
        self.Close()
    
    def onMenuClosed(self):
        self.screen_manager.score.FadeIn()
        self.screen_manager.AddScreen(self.screen_manager.score)
        self.Close()
        
    def onResetPinsSelected(self):
        print "Crap, we've got to reset the pins!"
        self.Close()
        
    def Draw(self, screen_surface):
        super(MainMenuScreen, self).Draw(screen_surface)
    
    def Update(self, game_time):
        super(MainMenuScreen, self).Update(game_time)
        
    def Close(self):
        self.screen_manager.RemoveScreen(self)
        #self.screen_manager.AddScreen(self.screen_manager.score)

class AdvancedScreen(Screen):
    def __init__(self, screen_manager):
        super(AdvancedScreen, self).__init__(screen_manager,8)
        self.menu_font = pygame.font.SysFont("Arial", 24, True)
        self.menu = Menu(self.onMenuClosed, (230,230,230), 250, 250)
        self.menu.AddMenuItem("Restart Scorer", self.onRestartScorerSelected)
        self.menu.AddMenuItem("Calibrate Scorer Camera", self.onCalibrateCameraSelected)
        self.menu.AddMenuItem("Exit Scorer System", self.onExitScorerSelected)
        self.menu.AddMenuItem("Exit Menu", self.onMenuClosed)
        
        self.components.append(self.menu)
        
    def onExitScorerSelected(self):
        self.bowling_scorer.doExit = True
    
    def onRestartScorerSelected(self):
        del self.screen_manager.screens[:]
        del self.bowling_scorer.players[:]
        self.bowling_scorer.current_player = -1
        self.bowling_scorer.current_frame = 0
        self.bowling_scorer.current_ball = 0
        
        self.screen_manager.boot.FadeIn()
        self.screen_manager.AddScreen(self.screen_manager.boot)
        
    def onCalibrateCameraSelected(self):
        self.screen_manager.AddScreen(self.screen_manager.calibrate_camera)
        self.Close()
        
    def onMenuClosed(self):
        self.screen_manager.AddScreen(self.screen_manager.mainmenu)
        self.screen_manager.RemoveScreen(self)
        
    def Draw(self, screen_surface):
        super(AdvancedScreen, self).Draw(screen_surface)
        
    
    def Update(self, game_time):
        super(AdvancedScreen, self).Update(game_time)
        
    def Close(self):
        self.screen_manager.RemoveScreen(self)
        
class RemoveBowlerScreen(Screen):
    def __init__(self, screen_manager):
        super(RemoveBowlerScreen, self).__init__(screen_manager,8)
        self.title_font = pygame.font.SysFont("Arial", 36, True, True)
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        
        self.menu = Menu(None, (230,230,230), 30, 90)
        #self.menu.AddMenuItem("Reset Pins", self.onResetPinsSelected)
        count = 0
        for p in self.bowling_scorer.players:
            self.menu.AddMenuItem(p.name, lambda: self.onBowlerSelected(count))
            count += 1
        
        self.components.append(self.menu)
        
    def Draw(self, screen_surface):
        screen_surface.set_alpha(self.alpha,RLEACCEL)
        
        screen_surface.fill((220,220,220))
        
        text = self.title_font.render("Remove Bowler", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=10)
        screen_surface.blit(text, textpos)
        
        text = self.text_font.render("Select the bowler you wish to remove:", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=50)
        screen_surface.blit(text, textpos)
        
        super(RemoveBowlerScreen, self).Draw(screen_surface)
        
    def ScreenShown(self):
        self.menu.ClearMenuItems()
        
        count = 0
        for p in self.bowling_scorer.players:
            self.menu.AddMenuItem(p.name, partial(self.onBowlerSelected, count))
            count += 1
            
        self.menu.current_selection = 0
        
    def onBowlerSelected(self, bowler_num):
        print "Removing bowler %d" % bowler_num
        
        self.bowling_scorer.players.pop(bowler_num)
        
        if self.bowling_scorer.current_player >= len(self.bowling_scorer.players):
            self.bowling_scorer.current_player = 0
            
        count = 0
        for p in self.bowling_scorer.players:
            p.number = count
            count += 1
        
        self.screen_manager.RemoveScreen(self)
        self.screen_manager.AddScreen(self.screen_manager.score)

class ScoreCorrectionSelectScreen(Screen):
    def __init__(self, screen_manager):
        super(ScoreCorrectionSelectScreen, self).__init__(screen_manager,8)
        self.title_font = pygame.font.SysFont("Arial", 36, True, True)
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        
        self.menu = Menu(None, (230,230,230), 30, 90)
        #self.menu.AddMenuItem("Reset Pins", self.onResetPinsSelected)
        count = 0
        for p in self.bowling_scorer.players:
            self.menu.AddMenuItem(p.name, lambda: self.onBowlerSelected(count))
            count += 1
        
        self.components.append(self.menu)
        
    def Draw(self, screen_surface):
        screen_surface.set_alpha(self.alpha,RLEACCEL)
        screen_surface.fill((220,220,220))
        
        text = self.title_font.render("Score Correction", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=10)
        screen_surface.blit(text, textpos)
        
        text = self.text_font.render("Select the bowler you wish to correct scores for:", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=50)
        screen_surface.blit(text, textpos)
        
        super(ScoreCorrectionSelectScreen, self).Draw(screen_surface)
        
    def ScreenShown(self):
        self.menu.ClearMenuItems()
        
        count = 0
        for p in self.bowling_scorer.players:
            self.menu.AddMenuItem(p.name, partial(self.onBowlerSelected, count))
            count += 1
            
        self.menu.current_selection = 0
        
    def onBowlerSelected(self, bowler_num):
        self.screen_manager.score_correct.selected_player = bowler_num
        self.screen_manager.RemoveScreen(self)
        self.screen_manager.AddScreen(self.screen_manager.score_correct)
    
class ScoreCorrectionScreen(Screen):
    def __init__(self, screen_manager):
        super(ScoreCorrectionScreen, self).__init__(screen_manager,8)
        self.title_font = pygame.font.SysFont("Arial", 36, True, True)
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        self.current_box_pos = 1
        
        self.menu = Menu(None, (230,230,230), 30, 90)
        #self.menu.AddMenuItem("Reset Pins", self.onResetPinsSelected)
        count = 0
        self.selected_player = 0
        
    def Draw(self, screen_surface):
        screen_surface.set_alpha(self.alpha,RLEACCEL)
        screen_surface.fill((220,220,220))
        
        text = self.title_font.render("Score Correction", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=10)
        screen_surface.blit(text, textpos)
        
        text = self.text_font.render("Select the frame to correct. Use the arrows to move left/right", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=50)
        screen_surface.blit(text, textpos)
        
        text = self.text_font.render("Hit ESC to exit", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=500)
        screen_surface.blit(text, textpos)
        
        self.bowling_scorer.players[self.selected_player].DrawFrames(surface=screen_surface,yscew=50,showTotal=False,current_box=self.current_box_pos)
        
        super(ScoreCorrectionScreen, self).Draw(screen_surface)
    
    def HandleEvent(self, event):
        super(ScoreCorrectionScreen, self).HandleEvent(event)
        
        if (event.type == KEYDOWN and event.key == K_ESCAPE):
            self.screen_manager.RemoveScreen(self)
            self.screen_manager.score.RefreshPlayerInfo()
            self.screen_manager.AddScreen(self.screen_manager.score)
        elif (event.type == KEYDOWN and event.key == K_RIGHT):
            if (self.current_box_pos >= 21):
                self.current_box_pos = 1
            else:
                self.current_box_pos += 1
        elif (event.type == KEYDOWN and event.key == K_LEFT):
            if (self.current_box_pos <= 1):
                self.current_box_pos = 21
            else:
                self.current_box_pos -= 1
        elif (event.type == KEYDOWN and ((event.key >= 48 and event.key <= 57) or (event.key >= 256 and event.key <= 265) or event.key == K_x or event.key == K_SLASH)):
            self.HandleScoreCorrection(chr(event.key))
            
    def HandleScoreCorrection(self, key):
        if (self.current_box_pos >= 19):
            frame = 9
            shot = self.current_box_pos - 19;
        else:
            if (self.current_box_pos <= 2):
                frame = 0
            else:
                frame = int(math.ceil((self.current_box_pos / 2.0))) - 1
                
            if (self.current_box_pos % 2 == 0):
                shot = 1
            else:
                shot = 0
            
        #self.bowling_scorer.players[self.selected_player].DrawFrames(surface=screen_surface,yscew=50,showTotal=False,current_box=self.current_box_pos)
        if (key == "X" or key == "x"):
            if (self.current_box_pos >= 19):
                self.bowling_scorer.players[self.selected_player].frames[frame].shots[shot] = 10
            else:
                self.bowling_scorer.players[self.selected_player].frames[frame].makeStrike()
            
            self.bowling_scorer.pinCounter.last_ball_score = 10
        elif (key == "/"):
            if (self.current_box_pos >= 19):
                self.bowling_scorer.players[self.selected_player].frames[frame].shots[shot] = 10 - self.bowling_scorer.players[self.selected_player].frames[frame].shots[shot - 1]
            else:
                self.bowling_scorer.players[self.selected_player].frames[frame].makeSpare()
        else:
            self.bowling_scorer.players[self.selected_player].frames[frame].shots[shot] = int(key)
            self.bowling_scorer.pinCounter.last_ball_score = int(key)
        
class SkipBowlerScreen(Screen):
    def __init__(self, screen_manager):
        super(SkipBowlerScreen, self).__init__(screen_manager,8)
        self.title_font = pygame.font.SysFont("Arial", 36, True, True)
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        
        self.menu = Menu(None, (230,230,230), 30, 90)
        #self.menu.AddMenuItem("Reset Pins", self.onResetPinsSelected)
        count = 0
        for p in self.bowling_scorer.players:
            self.menu.AddMenuItem(p.name, lambda: self.onBowlerSelected(count))
            count += 1
        
        self.components.append(self.menu)
        
    def Draw(self, screen_surface):
        screen_surface.set_alpha(self.alpha,RLEACCEL)
        screen_surface.fill((220,220,220))
        
        text = self.title_font.render("Skip to Bowler", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=10)
        screen_surface.blit(text, textpos)
        
        text = self.text_font.render("Select the bowler you wish to skip to:", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=50)
        screen_surface.blit(text, textpos)
        
        super(SkipBowlerScreen, self).Draw(screen_surface)
        
    def ScreenShown(self):
        self.menu.ClearMenuItems()
        
        count = 0
        for p in self.bowling_scorer.players:
            self.menu.AddMenuItem(p.name, partial(self.onBowlerSelected, count))
            count += 1
            
        self.menu.current_selection = 0
        
    def onBowlerSelected(self, bowler_num):
        print "Skipping to bowler %d" % bowler_num
        self.bowling_scorer.current_player = bowler_num
        self.screen_manager.RemoveScreen(self)
        self.screen_manager.AddScreen(self.screen_manager.score)
        
class AddBowlerScreen(Screen):
    def __init__(self, screen_manager):
        self.current_tab = 1
        super(AddBowlerScreen, self).__init__(screen_manager,8)
        self.bowler_name1 = TextBox(30, 100, 1)
        self.bowler_blacklight1 = CheckBox(180, 100, 2)
        
        self.bowler_name2 = TextBox(30, 130, 3)
        self.bowler_blacklight2 = CheckBox(180, 130, 4)
        
        self.bowler_name3 = TextBox(30, 160, 5)
        self.bowler_blacklight3 = CheckBox(180, 160, 6)
        
        self.bowler_name4 = TextBox(30, 190, 7)
        self.bowler_blacklight4 = CheckBox(180, 190, 8)
        
        self.mode_10pin = CheckBox(30, 220, 9)
        self.mode_9pin = CheckBox(150, 220, 10)
        self.mode_8pin = CheckBox(270, 220, 11)
        self.mode_7pin = CheckBox(390, 220, 12)
        
        self.add_button = Button(100, 250, "Add Bowlers", self.onAddBowlerSelected, 13)
        
        self.title_font = pygame.font.SysFont("Arial", 36, True, True)
        self.field_name_font = pygame.font.SysFont("Arial", 24, True)
        
        self.bowler_name1.selected = True
        self.mode_10pin.checked = True
        
        self.components.append(self.bowler_name1)
        self.components.append(self.bowler_blacklight1)
        self.components.append(self.bowler_name2)
        self.components.append(self.bowler_blacklight2)
        self.components.append(self.bowler_name3)
        self.components.append(self.bowler_blacklight3)
        self.components.append(self.bowler_name4)
        self.components.append(self.bowler_blacklight4)
        self.components.append(self.mode_10pin)
        self.components.append(self.mode_9pin)
        self.components.append(self.mode_8pin)
        self.components.append(self.mode_7pin)
        self.components.append(self.add_button)
        
    def onAddBowlerSelected(self):
        if (len(self.bowling_scorer.players) == 4): return
        if (self.bowler_name1.value == ""): return
        
        current_num_bowlers = len(self.bowling_scorer.players)
        
        bowler_name = self.bowler_name1.value
        bowler_blacklight = self.bowler_blacklight1.checked
        
        if (self.bowler_name1.value != "" and current_num_bowlers < 1):
            self.bowling_scorer.addPlayer(bowler_name, bowler_blacklight)
        if (self.bowler_name2.value != "" and current_num_bowlers < 2):
            self.bowling_scorer.addPlayer(self.bowler_name2.value, self.bowler_blacklight2.checked)
        if (self.bowler_name3.value != "" and current_num_bowlers < 3):
            self.bowling_scorer.addPlayer(self.bowler_name3.value, self.bowler_blacklight3.checked)
        if (self.bowler_name4.value != "" and current_num_bowlers < 4):
            self.bowling_scorer.addPlayer(self.bowler_name4.value, self.bowler_blacklight4.checked)
        
        #print "Adding bowler %s (blacklight: %s)" % (str(bowler_name),str(bowler_blacklight))
        
        self.bowling_scorer.current_player = 0
        if (bowler_blacklight == True):
            self.bowling_scorer.decklight.Blacklight()
        else:
            self.bowling_scorer.decklight.Whitelight()
            
        self.bowling_scorer.min_pincount_strike = 10
        if (self.mode_9pin.checked): self.bowling_scorer.min_pincount_strike = 9
        elif (self.mode_8pin.checked): self.bowling_scorer.min_pincount_strike = 8
        elif (self.mode_7pin.checked): self.bowling_scorer.min_pincount_strike = 7
        
        self.screen_manager.AddScreen(self.screen_manager.score)
        self.Close()
        
    def Draw(self, screen_surface):
        screen_surface.set_alpha(self.alpha,RLEACCEL)
        # Draw partially transparent background
        screen_surface.fill((220,220,220))
        
        text = self.title_font.render("Add Bowlers", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=10)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("1.", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=100)
        screen_surface.blit(text, textpos)
        text = self.field_name_font.render("2.", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=130)
        screen_surface.blit(text, textpos)
        text = self.field_name_font.render("3.", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=160)
        screen_surface.blit(text, textpos)
        text = self.field_name_font.render("4.", 1, (0,0,0))
        textpos = text.get_rect(x=10, y=190)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("Name:", 1, (0,0,0))
        textpos = text.get_rect(x=30, y=70)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("Blacklight?", 1, (0,0,0))
        textpos = text.get_rect(x=180, y=70)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("[DOWN] - Advance to next field   [SPACE] - Toggles selection value", 1, (0,0,0))
        textpos = text.get_rect(centerx=400, y=540)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("Regular", 1, (0,0,0))
        textpos = text.get_rect(x=60, y=220)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("9 Pin", 1, (0,0,0))
        textpos = text.get_rect(x=180, y=220)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("8 Pin", 1, (0,0,0))
        textpos = text.get_rect(x=300, y=220)
        screen_surface.blit(text, textpos)
        
        text = self.field_name_font.render("7 Pin", 1, (0,0,0))
        textpos = text.get_rect(x=420, y=220)
        screen_surface.blit(text, textpos)
        
        super(AddBowlerScreen, self).Draw(screen_surface)
        
    def HandleEvent(self, event):
        super(AddBowlerScreen, self).HandleEvent(event)
        
        if (event.type == KEYDOWN and event.key == K_DOWN):
            self.selectNextItem()
        elif (event.type == KEYDOWN and event.key == K_UP):
            self.selectPrevItem()
        
        return False
    
    def selectNextItem(self):
        self.current_tab += 1
        
        selection_changed = False
        for e in self.components:
            e.selected = False
            
        for e in self.components:
            if e.taborder == self.current_tab and e.selected != None:
                e.selected = True
                selection_changed = True
                break
            
        if not selection_changed:
            self.current_tab = 1
            for e in self.components:
                if e.selected != None:
                    e.selected = True
                    break
                
    def selectPrevItem(self):
        self.current_tab -= 1
        
        selection_changed = False
        for e in self.components:
            e.selected = False
            
        for e in self.components:
            if e.taborder == self.current_tab and e.selected != None:
                e.selected = True
                selection_changed = True
                break
            
        if not selection_changed:
            self.current_tab = self._getMaxComponentID()
            for e in self.components:
                if e.selected != None:
                    e.selected = True
                    break
        
    
    def Update(self, game_time):
        super(AddBowlerScreen, self).Update(game_time)
        
        
    def Close(self):
        self.screen_manager.RemoveScreen(self)
        
class CalibrateCameraScreen(Screen):
    def __init__(self, screen_manager):
        super(CalibrateCameraScreen, self).__init__(screen_manager,7)
        
        self.camera_size = self.bowling_scorer.config.gettuple("Camera","size");
        
        self.font = pygame.font.SysFont("Arial", 24, True)
        self.small_font = pygame.font.SysFont("Arial", 16, True)
        self.deck_count_font = pygame.font.SysFont("Arial", 96, True)
        self.detected_pin_count = -1
        
        self.current_edit = 0
        
        self.points = []
        
        self.current_add_pin = -1
        
        self.edit_bl = False
        
        self.draw_text_color = (255,255,255)
        
        for i in range(1,11):
            if self.bowling_scorer.config.gettuple("Calibration", "point_"+str(i)) != None:
                self.points.append(self.bowling_scorer.config.gettuple("Calibration", "point_"+str(i)))
            else:
                self.points.append((-1,-1))
                
        self.sr = ui_components.Slider((0,290), 24)
        self.sg = ui_components.Slider((0,310), 24)
        self.sb = ui_components.Slider((0,330), 24)
        
    def start_camera(self):
        self.camera = self.bowling_scorer.pinCounter
        
    def Draw(self, screen_surface):
        screen_surface.fill((50,50,50))
        
        snapshot = self.bowling_scorer.pinCounter.getDeckSnapshot()
        screen_surface.blit(snapshot, (0,0))
        
        for px,py in self.points:
            if (px == -1 or py == -1): continue
            pygame.draw.rect(screen_surface, pygame.color.Color("red"), (px,py,5,5),1)
        
        
        text = self.small_font.render("C - Clear Points     BKSP - Exit   ENTER - Save Changes    B - Toggle Blacklight/White light edit", 1, self.draw_text_color)
        textpos = text.get_rect(centerx=400, y=570)
        screen_surface.blit(text, textpos)
        
        text = self.small_font.render("D - Edit Detect Color   T - Edit Threshold   N - Edit Blackout Color", 1, self.draw_text_color)
        textpos = text.get_rect(centerx=400, y=540)
        screen_surface.blit(text, textpos)
        
        text = self.font.render("Hit 'S' to score the current deck", 1, self.draw_text_color)
        textpos = text.get_rect(centerx=400, y=510)
        screen_surface.blit(text, textpos)
        
        if (self.detected_pin_count != -1):
            text = self.font.render("Current Deck Score", 1, (255,255,255))
            textpos = text.get_rect(centerx=550, y=10)
            screen_surface.blit(text, textpos)
            
            text = self.deck_count_font.render(str(self.detected_pin_count), 1, (0,255,0))
            textpos = text.get_rect(centerx=550, y=50)
            screen_surface.blit(text, textpos)
            
        if (self.current_add_pin != -1):
            text = self.font.render("Click camera area to add " + str(self.current_add_pin) + " pin scan area", 1, (0,255,0))
            textpos = text.get_rect(centerx=400, y=350)
            screen_surface.blit(text, textpos)
            
        text = self.font.render("Press the number 0-9 of the point you wish to add.", 1, self.draw_text_color)
        textpos = text.get_rect(centerx=400, y=400)
        screen_surface.blit(text, textpos)
        text = self.font.render("Then click to add a scanning area. (Note: 0 is the 10 pin)", 1, self.draw_text_color)
        textpos = text.get_rect(centerx=400, y=430)
        screen_surface.blit(text, textpos)
        
        text = self.small_font.render("R: " + str(self.sr.value), 1, self.draw_text_color)
        textpos = text.get_rect(x=280, y=290)
        screen_surface.blit(text, textpos)
        text = self.small_font.render("G: " + str(self.sg.value), 1, self.draw_text_color)
        textpos = text.get_rect(x=280, y=310)
        screen_surface.blit(text, textpos)
        text = self.small_font.render("B: " + str(self.sb.value), 1, self.draw_text_color)
        textpos = text.get_rect(x=280, y=330)
        screen_surface.blit(text, textpos)
        
        if (self.edit_bl):
            prefix = "B/L "
            detect_color = self.bowling_scorer.pinCounter.bl_detect_color
            threshold_detect = self.bowling_scorer.pinCounter.bl_threshold_detect
            other_colors_nondetect = self.bowling_scorer.pinCounter.bl_other_colors_nondetect
        else:
            prefix = ""
            detect_color = self.bowling_scorer.pinCounter.detect_color
            threshold_detect = self.bowling_scorer.pinCounter.threshold_detect
            other_colors_nondetect = self.bowling_scorer.pinCounter.other_colors_nondetect
        
        text = self.small_font.render(prefix + "Detect Color: " + str(detect_color), 1, self.draw_text_color)
        textpos = text.get_rect(x=400, y=290)
        screen_surface.blit(text, textpos)
        text = self.small_font.render(prefix + "Threshold Color: " + str(threshold_detect), 1, self.draw_text_color)
        textpos = text.get_rect(x=400, y=310)
        screen_surface.blit(text, textpos)
        text = self.small_font.render(prefix + "Pixel color nondetect: " + str(other_colors_nondetect), 1, self.draw_text_color)
        textpos = text.get_rect(x=400, y=330)
        screen_surface.blit(text, textpos)
        
        if (self.current_edit != 0):
            if (self.current_edit == 1):
                text = self.small_font.render("Editing " + prefix + " detect color:", 1, self.draw_text_color)
                if (self.edit_bl):
                    self.bowling_scorer.pinCounter.bl_detect_color = (self.sr.value, self.sg.value, self.sb.value)
                else:
                    self.bowling_scorer.pinCounter.detect_color = (self.sr.value, self.sg.value, self.sb.value)
            elif (self.current_edit == 2):
                text = self.small_font.render("Editing " + prefix + " threshold color:", 1, self.draw_text_color)
                if (self.edit_bl):
                    self.bowling_scorer.pinCounter.bl_threshold_detect = (self.sr.value, self.sg.value, self.sb.value)
                else:
                    self.bowling_scorer.pinCounter.threshold_detect = (self.sr.value, self.sg.value, self.sb.value)
            else:
                text = self.small_font.render("Editing " + prefix + " blackout color: (colors not within range are defaulted to this value)", 1, self.draw_text_color)
                if (self.edit_bl):
                    self.bowling_scorer.pinCounter.bl_other_colors_nondetect = (self.sr.value, self.sg.value, self.sb.value)
                else:
                    self.bowling_scorer.pinCounter.other_colors_nondetect = (self.sr.value, self.sg.value, self.sb.value)
            textpos = text.get_rect(x=0, y=260)
            screen_surface.blit(text, textpos)
        
        self.sr.render(screen_surface)
        self.sg.render(screen_surface)
        self.sb.render(screen_surface)
        
        super(CalibrateCameraScreen, self).Draw(screen_surface)
        
    
    def HandleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (event.pos[0] > self.camera_size[0]) or \
            (event.pos[1] > self.camera_size[1]) or \
            self.current_add_pin == -1:
                return
            
            print "Adding calibration marker at (%d, %d)" % event.pos
            
            
            posx = event.pos[0] - 2
            posy = event.pos[1] - 2
            
            
            if len(self.points) == 0:
                for i in range(10):
                    self.points.append((-1,-1))
            self.points[self.current_add_pin - 1] = (posx,posy)
            
            self.writePointsToConfig()
            
            self.bowling_scorer.pinCounter.reloadCalibration()
            
            #deck_surface = self.bowling_scorer.pinCounter.getDeckSnapshot()
            #deck_px_array = pygame.PixelArray(deck_surface)
            #xpos,ypos = event.pos
            #color = deck_px_array[xpos][ypos]
            
            #if color == deck_surface.map_rgb((255,255,255)):
            #    print "Hit at (%d,%d)" % event.pos
            #else:
            #    print "Miss at (%d,%d) (%s)" % (xpos, ypos, str(deck_surface.unmap_rgb(color)))
            
        elif event.type == pygame.KEYDOWN:
            if event.key == K_c:
                print "Clearing all calibration markers"
                del self.points[:]
                self.writePointsToConfig()
                return False
            elif event.key == K_BACKSPACE:
                self.screen_manager.AddScreen(self.screen_manager.mainmenu)
                self.Close()
                return False
            elif event.key == K_s:
                self.detected_pin_count = self.bowling_scorer.pinCounter.getPinCount()
            elif event.key == K_0:
                self.current_add_pin = 10
            elif event.key == K_1:
                self.current_add_pin = 1
            elif event.key == K_2:
                self.current_add_pin = 2
            elif event.key == K_3:
                self.current_add_pin = 3
            elif event.key == K_4:
                self.current_add_pin = 4
            elif event.key == K_5:
                self.current_add_pin = 5
            elif event.key == K_6:
                self.current_add_pin = 6
            elif event.key == K_7:
                self.current_add_pin = 7
            elif event.key == K_8:
                self.current_add_pin = 8
            elif event.key == K_9:
                self.current_add_pin = 9
            elif event.key == K_d:
                self.current_edit = 1
                b_d_c = self.bowling_scorer.config.gettuple("Camera", "bl_detect_color")
                d_c = self.bowling_scorer.config.gettuple("Camera", "detect_color")
                if (self.edit_bl):
                    self.sr.setvalue(b_d_c[0])
                    self.sg.setvalue(b_d_c[1])
                    self.sb.setvalue(b_d_c[2])
                else:
                    self.sr.setvalue(d_c[0])
                    self.sg.setvalue(d_c[1])
                    self.sb.setvalue(d_c[2])
            elif event.key == K_t:
                self.current_edit = 2
                b_t_d = self.bowling_scorer.config.gettuple("Camera", "bl_threshold_detect")
                t_d = self.bowling_scorer.config.gettuple("Camera", "threshold_detect")
                if (self.edit_bl):
                    self.sr.setvalue(b_t_d[0])
                    self.sg.setvalue(b_t_d[1])
                    self.sb.setvalue(b_t_d[2])
                else:
                    self.sr.setvalue(t_d[0])
                    self.sg.setvalue(t_d[1])
                    self.sb.setvalue(t_d[2])
            elif event.key == K_n:
                self.current_edit = 3
                o_c_n = self.bowling_scorer.config.gettuple("Camera", "other_colors_nondetect")
                b_o_c_n = self.bowling_scorer.config.gettuple("Camera", "bl_other_colors_nondetect")
                if self.edit_bl:
                    self.sr.setvalue(b_o_c_n[0])
                    self.sg.setvalue(b_o_c_n[1])
                    self.sb.setvalue(b_o_c_n[2])
                else:
                    self.sr.setvalue(o_c_n[0])
                    self.sg.setvalue(o_c_n[1])
                    self.sb.setvalue(o_c_n[2])
            elif event.key == K_RETURN:
                if (self.edit_bl):
                    self.bowling_scorer.config.setvalue("Camera", "bl_detect_color", self.bowling_scorer.pinCounter.bl_detect_color)
                    self.bowling_scorer.config.setvalue("Camera", "bl_threshold_detect", self.bowling_scorer.pinCounter.bl_threshold_detect)
                    self.bowling_scorer.config.setvalue("Camera", "bl_other_colors_nondetect", self.bowling_scorer.pinCounter.bl_other_colors_nondetect)
                else:
                    self.bowling_scorer.config.setvalue("Camera", "detect_color", self.bowling_scorer.pinCounter.detect_color)
                    self.bowling_scorer.config.setvalue("Camera", "threshold_detect", self.bowling_scorer.pinCounter.threshold_detect)
                    self.bowling_scorer.config.setvalue("Camera", "other_colors_nondetect", self.bowling_scorer.pinCounter.other_colors_nondetect)
                    
                self.bowling_scorer.config.save()
                self.screen_manager.ShowMessageBox("Changes Saved")
                self.bowling_scorer.pinCounter.reloadCalibration()
            elif event.key == K_b:
                self.edit_bl = not self.edit_bl
                self.current_edit = 0
                if (self.edit_bl):
                    self.bowling_scorer.decklight.Blacklight()
                    self.bowling_scorer.pinCounter.use_blacklight = True
                    self.draw_text_color = (102,51,255)
                    self.bowling_scorer.pinCounter.reloadCalibration()
                else:
                    self.bowling_scorer.decklight.Whitelight()
                    self.bowling_scorer.pinCounter.use_blacklight = False
                    self.draw_text_color = (255,255,255)
                    self.bowling_scorer.pinCounter.reloadCalibration()
            else:
                self.current_edit = 0
            
    def writePointsToConfig(self):
        for i in range(1,11):
            if (i > len(self.points)):
                point = None
            else:
                point = self.points[i-1]
                
            self.bowling_scorer.config.setvalue("Calibration", "point_"+str(i), point)
            
        self.bowling_scorer.config.save()
        self.bowling_scorer.pinCounter.reloadCalibration()
        
    def ScreenShown(self):
        self.current_add_pin = -1
    
    def Update(self, game_time):
        super(CalibrateCameraScreen, self).Update(game_time)
        
        self.sr.update()
        self.sg.update()
        self.sb.update()
        
    def Close(self):
        self.screen_manager.RemoveScreen(self)
        
class PindicationScreen(Screen):
    def __init__(self, screen_manager):
        super(PindicationScreen, self).__init__(screen_manager,6)
        self.show_pins = []
        for i in range(10):
            self.show_pins.append(True)
        
        self.pos_1 = (390, 480)
        
        self.pos_2 = (310, 340)
        self.pos_3 = (470, 340)
        
        self.pos_4 = (230, 200)
        self.pos_5 = (390, 200)
        self.pos_6 = (550, 200)
        
        self.pos_7 = (150,60)
        self.pos_8 = (310, 60)
        self.pos_9 = (470, 60)
        self.pos_10 = (630, 60)
        
        self.font = pygame.font.SysFont("Arial", 48, True)
            
        self.pin_radius = 40
        self.pin_color = (255,255,255,255)
        self.number_color = (0,0,255,255)
        
        self.time_shown = 0
        self.display_time = int(self.bowling_scorer.config.getvalue("System","pindicator_display_time"))
        
        self.pin_surface = pygame.Surface((800,600), SRCALPHA)
        
    def Draw(self, screen_surface):
        self.pin_surface.fill((0,0,0))
        if (self.mode != SCREEN_MODE_DISPLAY):
            self.pin_color = (255,255,255,self.alpha)
            self.number_color = (0,0,255,self.alpha)
            self.pin_surface.set_alpha(self.alpha)
            
        if (self.show_pins[6] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_7, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_7, "7", self.number_color)
        if (self.show_pins[7] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_8, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_8, "8", self.number_color)
        if (self.show_pins[8] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_9, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_9, "9", self.number_color)
        if (self.show_pins[9] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_10, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_10, "10", self.number_color)
        
        if (self.show_pins[3] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_4, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_4, "4", self.number_color)
        if (self.show_pins[4] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_5, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_5, "5", self.number_color)
        if (self.show_pins[5] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_6, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_6, "6", self.number_color)
        
        if (self.show_pins[1] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_2, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_2, "2", self.number_color)
        if (self.show_pins[2] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_3, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_3, "3", self.number_color)
            
        if (self.show_pins[0] == True):
            pygame.draw.circle(self.pin_surface, self.pin_color, self.pos_1, self.pin_radius)
            self.RenderText(self.pin_surface, self.pos_1, "1", self.number_color)
            
        screen_surface.blit(self.pin_surface, (0,0))
            
    def Update(self, game_time):
        super(PindicationScreen, self).Update(game_time)
        if game_time - self.time_shown >= self.display_time and self.mode != SCREEN_MODE_FADEOUT:
            self.FadeOut()        
        if self.mode == SCREEN_MODE_FADEOUT and self.pin_surface.get_alpha() == 0:
            self.screen_manager.RemoveScreen(self)
            self.screen_manager.score.FadeIn()
            self.screen_manager.AddScreen(self.screen_manager.score)
        
    def RenderText(self, surface, centerpos, text, color):
        text = self.font.render(text, 1, color)
        text.set_alpha(self.alpha)
        textpos = text.get_rect(centerx=centerpos[0], centery=centerpos[1])
        surface.blit(text, textpos)
        
    def show_pin(self, pin_number, show=True):
        self.show_pins[pin_number] = show
        
    def ScreenShown(self):
        self.time_shown = self.screen_manager.game_time
        self.FadeIn()
        
class ScreenManager(object):
    
    bowling_scorer = None
    screen_surface = None
    screens = []
    
    def __init__(self, scorer, screen_surface):
        self.screen_surface = screen_surface
        self.bowling_scorer = scorer
        self.calibrate_camera = CalibrateCameraScreen(self)
        
        self.score_correct = ScoreCorrectionScreen(self)
        self.score_correct_select = ScoreCorrectionSelectScreen(self)
        self.skip_bowler = SkipBowlerScreen(self)
        self.add_bowler = AddBowlerScreen(self)
        self.remove_bowler = RemoveBowlerScreen(self)
        self.error_screen = ErrorScreen(self)
        
        self.pindication = PindicationScreen(self)
        
        self.boot = BootScreen(self)
        
        self.advanced = AdvancedScreen(self)
        self.mainmenu = MainMenuScreen(self)
        self.score = ScoreScreen(self)
        self.game_time = 0
        self.display_modal = False
        self.expire_modal_time = 0
        self.modal_message = ""
        
        self.modal_font = pygame.font.SysFont("Arial", 24, True)
    
    '''
    Draw the current screen to the surface
    '''
    def Draw(self):
        for screen in self.screens:
            screen.Draw(self.screen_surface)
            
        if (self.display_modal):
            self.DrawModal()
    
    def DrawModal(self):
        text = self.modal_font.render(self.modal_message, 1, (255, 255, 255))
        textpos = text.get_rect(centerx=400,centery=300)
        text_width = text.get_rect().width
        text_height = text.get_rect().height
        pygame.draw.rect(self.screen_surface, (0,0,0), (395 - (0.5 * text_width), (295 - 0.5 * text_height), text_width + 10, text_height + 10))
        pygame.draw.rect(self.screen_surface, (0,0,255), (395 - (0.5 * text_width), (295 - 0.5 * text_height), text_width + 10, text_height + 10), 5)
        self.screen_surface.blit(text, textpos)
    
    '''
    Update any game logic
    '''
    def Update(self, game_time):
        self.game_time = game_time
        for screen in self.screens:
            screen.Update(game_time)
            
        if (self.display_modal):
            if self.game_time >= self.expire_modal_time:
                self.display_modal = False
            
    def HandleEvent(self, e):
        for screen in self.screens:
            if screen.HandleEvent(e) == False:
                break
            
    def Cleanup(self):
        for screen in self.screens:
            screen.Cleanup()
            
    def ShowMessageBox(self,message,display_time=2000):
        self.display_modal = True
        self.modal_message = message
        self.expire_modal_time = self.game_time + display_time
            
    def AddScreen(self, screen):
        screen.ScreenShown()
        self.screens += [screen]
        self.screens.sort(lambda x, y: y.priority - x.priority)
        
    def RemoveScreen(self, screen):
        #self.screens.pop(screen.priority)
        self.screens.remove(screen)
        
    def RemoveAllScreens(self):
        self.screens = []