
import os, sys, platform, traceback
import pygame
import pygame.camera
import random
import hardware
import pickle
import time
from pygame.locals import *
from screens import *
from player import *
from frame import *
from config import *
from log import *
from hardware import arduino
from hardware import decklight

class BowlingScorer(object):

    PIXEL_DISTANCE_COUNT = 10 # Number of pixels that must be contiguously white to count as a pin
    
    # Variable declarations
    doExit = False
    screenManager = None
    clock = None
    players = []
    redraw_screen = True
    current_player = -1
    current_frame = 0
    current_ball = 0    # 0: first 1: second 2: third (tenth frame only)
    instance = None
    
    def __init__(self):
        logger.info("Created BowlingScorer object")
        self.mode = "GAME_OVER"
        BowlingScorer.instance = self
        self.is_first_ball = True
        self.min_pincount_strike = 10
    
    def cleanup(self):
        logger.info("BowlingScorer.cleanup()")
        self.screenManager.Cleanup()
        self.pinCounter.cleanup()
        self.hw.Close()
        print "Cleanup finished"
        
    def changeFooterText(self):
        
        self.redraw_screen = True
    
    def addPlayer(self, name, blacklight = False):
        if len(self.players) == 4:
            return
        self.players.append(Player(name, len(self.players), self, blacklight))
    
    def main(self):
        # END GLOBAL DECLARATIONS ========================================
        
        logger.info("Creating config object...")
        self.config = Config()
        #self.config.reset()
        try:
            logger.info("Loading config file...")
            self.config.load()
        except:
            logger.critical("Config file not loaded")
            logger.exception('')
            return
        
        logger.info("Creating hardware interface...")
        self.hw = arduino.Arduino(self.config.getvalue("Hardware","port"))
        
        logger.info("Creating decklight controller...")
        self.decklight = decklight.DeckLight(self.hw, int(self.config.getvalue("Hardware","decklight_port")))
        
        self.frames_per_turn = int(self.config.getvalue("System","frames_per_turn"))
        
        # Initialize the pygame framework
        logger.info("Initializing pygame display system...")
        pygame.init()
        
        self.restore_state()
        
        self.clock = pygame.time.Clock()
        
        self.current_ball = 0
        
        # Set up our screen
        if (self.config.getboolean("Screen", "fullscreen")):
            screen_flags = pygame.FULLSCREEN
        else:
            screen_flags = 0
            
        
        try:
            logger.info("Creating screen display...")
            self.screen = pygame.display.set_mode(self.config.gettuple("Screen", "size"), screen_flags)
            pygame.display.set_caption("Scorer")
        except:
            logger.critical("Could not create display")
            logger.exception('')
            return
        #pygame.display.toggle_fullscreen()
        
        try:
            logger.info("Creating screen manager...")
            self.screenManager = ScreenManager(self, self.screen)
        except:
            logger.critical("Could not create screen manager")
            logger.exception('')
            return
        
        self.screenManager.AddScreen(self.screenManager.boot)
        random.seed()
        
        try:
            logger.info("Creating pinCounter...")
            self.pinCounter = PinCounter(self.screen)
            self.pinCounter.getPinCount(False)
        except:
            logger.critical("Could not create pincounter")
            logger.exception('')
            ErrorScreen.error_string = "Could not create pin counter. This usually means we couldn't connect to your camera."
            self.showErrorScreen()
            return        
        
        # Main game loop
        while not self.doExit:
            self.clock.tick(40)
            
            self.screenManager.Update(pygame.time.get_ticks())
            self.screen.fill((0,0,0))
            
            self.screenManager.Draw()
            
            
            # Event loop
            for e in pygame.event.get():
                if (e.type == QUIT):
                    self.doExit = True
                self.screenManager.HandleEvent(e)
    
            # Update screen
            pygame.display.flip()
        
        # If we get here, do cleanup
        self.cleanup()
        
    def showErrorScreen(self):
        self.screenManager.RemoveAllScreens()
        self.screenManager.AddScreen(self.screenManager.error_screen)
        while not self.doExit:
            self.clock.tick(40)
            self.screenManager.Update(pygame.time.get_ticks())
            self.screen.fill((0,0,0))
            self.screenManager.Draw()
            for e in pygame.event.get():
                if (e.type == QUIT):
                    self.doExit = True
            pygame.display.flip()
        
    def next_player(self):
        if (len(self.players)) == 0: return;
        self.current_player += 1
        if self.current_player > len(self.players) - 1:
            self.current_player = 0
            
        if self.players[self.current_player].blacklight == True:
            self.decklight.Blacklight()
            self.pinCounter.use_blacklight = True
        else:
            self.decklight.Whitelight()
            self.pinCounter.use_blacklight = False
            
    def end_game_if_over(self):
        is_game_over = True
        for p in self.players:
            if (p.current_frame < 9):
                is_game_over = False
                break
            if (p.current_frame == 9 and not p.frames[p.current_frame].hasBowled()):
                is_game_over = False
        
        if (is_game_over):
            self.current_player = -1
            self.screenManager.score.show_marquee = True
            self.screenManager.score.show_help_text = False
            self.remove_state()
            
    def new_game(self):
        if len(self.players) == 0: return
        
        if (os.path.exists("current.state")):
            os.remove("current.state")
        
        for p in self.players:
            p.reset()
            
        self.current_player = 0
        self.current_frame = 0
        self.current_ball = 0
        self.screenManager.score.show_marquee = False
        self.screenManager.score.show_help_text = True
        
        self.pinCounter.use_blacklight = self.players[self.current_player].blacklight
        
    def dump_current_state(self):
        try:
            outfile = open("current.state", "wb")
            pickle.dump(self.players, outfile)
            outfile.close()
        except:
            logger.error("Crap, couldn't save state.")
            logger.exception('')
            
    def remove_state(self):
        try:
            os.remove("current.state")
        except:
            logger.error("Could not remove saved state")
            logger.exception('')
        
    def restore_state(self):
        try:
            if (os.path.exists("current.state")):
                infile = open("current.state", "rb")
                self.players = pickle.load(infile)
                infile.close()
                for player in self.players:
                    player.bowling_scorer = self
        except:
            logger.error("Crap, couldn't load saved state. Skipping")
            logger.exception('')
            self.remove_state()

class PinCounter:
    camera = None
    snapshot = None
    thresholded = None
    isStreaming = False
    screen = None
    def __init__(self, screen):
        self.screen = screen
        
        try:
            logger.info("Initializing camera...")
            pygame.camera.init()
            
            self.last_ball_score = 0
            
            cam_size = BowlingScorer.instance.config.gettuple("Camera", "size")
            self.detect_color = BowlingScorer.instance.config.gettuple("Camera", "detect_color")
            self.other_colors_nondetect = BowlingScorer.instance.config.gettuple("Camera", "other_colors_nondetect")
            self.threshold_detect = BowlingScorer.instance.config.gettuple("Camera", "threshold_detect")
            
            self.bl_detect_color = BowlingScorer.instance.config.gettuple("Camera", "bl_detect_color")
            self.bl_other_colors_nondetect = BowlingScorer.instance.config.gettuple("Camera", "bl_other_colors_nondetect")
            self.bl_threshold_detect = BowlingScorer.instance.config.gettuple("Camera", "bl_threshold_detect")
            self.camera_idx = int(BowlingScorer.instance.config.getvalue_default("Camera", "camera_number", 0))
            
            # Initialize the camera, using the 0 (first) device
            # Also specify the size as 320x240
            # On linux, instead of '0' we should use /dev/video0
            
            self.camera_list = pygame.camera.list_cameras()
            
            logging.info("Creating camera at size %s" % str(cam_size))
            if (platform.system() == "Windows"):
                self.camera = pygame.camera.Camera(device=self.camera_list[self.camera_idx], size=cam_size, mode = "YUV")
            else:
                self.camera = pygame.camera.Camera(self.camera_list[self.camera_idx], cam_size, "YUV")
            self.camera.start()
                
            self.snapshot = pygame.Surface(cam_size, 0, screen)
            self.thresholded = pygame.Surface(cam_size, 0, screen)
            
            self.use_blacklight = False
            
            self.points = []
            self.point_size = 0
            self.min_points_to_trigger = 0
            self.reloadCalibration()
            
            
        except:
            logging.critical("Camera initialization failed. Make sure the scoring camera is plugged in.")
            logging.exception('')
            raise Exception("Camera init failed")
    
        self.pin_display = []
        self.resetPinDisplay()
            
    def resetPinDisplay(self):
        del self.pin_display[:]
        for i in range(10):
            self.pin_display.append(False)
    
    '''
    Gets the pin count of the current pindeck by taking a threshold image
    and counting objects. Returns 0-10 (number of pins hit)
    '''
    def getPinCount(self, use_last_ball_score = False):
        deck_surface = self.getDeckSnapshot()
        retry_count = 0
        while deck_surface == None and retry_count < 3:
            self.cleanup()
            time.sleep(5)
            self.__init__(self.screen)
            deck_surface = self.getDeckSnapshot()
            retry_count += 1
            
        self.resetPinDisplay()
        # Always assume there are 0 pins standing
        num_pins_standing = 0
        
        #self.screen.blit(self.thresholded, (0,0))
        deck_px_array = pygame.PixelArray(deck_surface)
        counter = 0
        
        if (self.use_blacklight):
            detect_color = self.bl_detect_color
        else:
            detect_color = self.detect_color
            
        for px,py in self.points:
            num_points_triggered = 0
            for x in range(px, px + self.point_size + 1):
                for y in range(py, py + self.point_size + 1):
                    if (deck_px_array[x][y] == deck_surface.map_rgb(detect_color)):
                        # This pixel is white, so count that as a triggered pixel
                        num_points_triggered += 1
            
            # If we're over the threshold, count it as a pin standing
            if num_points_triggered >= self.min_points_to_trigger:
                num_pins_standing += 1
                self.pin_display[counter] = True
                
            counter += 1
        
        # If we're not using the last ball score, set the last ball score as the current score
        # (This happens on first ball)
        if not use_last_ball_score:
            self.last_ball_score = 10 - num_pins_standing
            logger.info("num_pins_standing: %d       last_ball_score: %d" % (num_pins_standing, self.last_ball_score))
            return (10 - num_pins_standing)
        else:
            current_ball_score = 10 - num_pins_standing
            if (current_ball_score == 10):
                return 10 - self.last_ball_score
            elif (current_ball_score == self.last_ball_score):
                return 0
            elif (current_ball_score > self.last_ball_score):
                return current_ball_score - self.last_ball_score
            else:
                return self.last_ball_score - current_ball_score
            #print "using last ball score: %d   current_ball_score: %d" % (self.last_ball_score, current_ball_score)
            #return (self.last_ball_score + (10 - current_ball_score))
        
    def getDeckSnapshot(self):
        #logger.info("Getting deck snapshot")
        if self.camera == None: return
        #logger.info("Capturing image from camera...")
        try:
            self.camera.get_image(self.snapshot)
        except Exception, e:
            self.snapshot = None
            
        if self.snapshot == None:
            retry_count = 0
            while self.snapshot == None and retry_count < 3:
                self.cleanup()
                time.sleep(5)
                self.__init__(self.screen)
                self.snapshot = self.camera.get_image(self.snapshot)
                retry_count += 1
            
        #logger.info("Thresholding image...")
        if (self.use_blacklight):
            pygame.transform.threshold(self.thresholded, self.snapshot, self.bl_detect_color, self.bl_threshold_detect, self.bl_other_colors_nondetect, 1)
        else:
            pygame.transform.threshold(self.thresholded, self.snapshot, self.detect_color, self.threshold_detect, self.other_colors_nondetect, 1)
        
        #logger.info("Creating resized surface for processing")
        resized = pygame.Surface((320,240), 0, self.screen)
            
        if self.thresholded != None:
            pygame.transform.scale(self.thresholded, (320,240), resized)
            
        return resized
        
    '''
    Reloads the calibration points from the configuration file as well as
    point sizes and threshold information for each point
    '''
    def reloadCalibration(self):
        logger.info("Reloading calibration points...")
        del self.points[:]
        for i in range(10):
            self.points.append((-1,-1))
        for i in range(1,11):
            if (BowlingScorer.instance.config.gettuple("Calibration", "point_" + str(i)) != None):
                self.points[i - 1] = BowlingScorer.instance.config.gettuple("Calibration", "point_" + str(i))
        
        logger.info("Reloading calibration point info from file...")
        self.point_size = int(BowlingScorer.instance.config.getvalue("Calibration", "point_size"))
        self.min_points_to_trigger = int(BowlingScorer.instance.config.getvalue("Calibration", "min_points_to_trigger"))
        
        self.detect_color = BowlingScorer.instance.config.gettuple("Camera", "detect_color")
        self.other_colors_nondetect = BowlingScorer.instance.config.gettuple("Camera", "other_colors_nondetect")
        self.threshold_detect = BowlingScorer.instance.config.gettuple("Camera", "threshold_detect")
        
        self.bl_detect_color = BowlingScorer.instance.config.gettuple("Camera", "bl_detect_color")
        self.bl_other_colors_nondetect = BowlingScorer.instance.config.gettuple("Camera", "bl_other_colors_nondetect")
        self.bl_threshold_detect = BowlingScorer.instance.config.gettuple("Camera", "bl_threshold_detect")
        
    def cleanup(self):
        if self.camera != None:
            self.camera.stop()
