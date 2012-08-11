'''
Created on May 1, 2012

@author: Compy
'''

import pygame
import string
from pygame.locals import *

class DrawableComponent(object):
    '''
    classdocs
    '''


    def __init__(self, x=0, y=0, taborder = 0):
        '''
        Constructor
        '''
        self.x = x
        self.y = y
        self.taborder = taborder
        
    def Draw(self, surface):
        pass
    
    def Update(self, game_time):
        pass
    
    def HandleKeyPress(self, key):
        pass
    
class Button(DrawableComponent):
    def __init__(self, x=0, y=0, text="", callback = None, taborder=0):
        super(Button, self).__init__(x,y,taborder)
        self.selected = False
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        self.callback = callback
        self.text = text
        
    def HandleKeyPress(self, key):
        if self.selected != True:
            return
        
        if key == K_RETURN and self.callback != None:
            self.callback()
            
    def Draw(self, surface):
        
        if (self.selected == True):
            bgcolor = (0,0,255)
            fcolor = (255,255,255)
            border_extend = 0
        else:
            bgcolor = (128,128,128)
            fcolor = (0,0,0)
            border_extend = 1
        text = self.text_font.render(self.text, 1, fcolor)
        pygame.draw.rect(surface, bgcolor, (self.x, self.y, text.get_rect().width + 4, 26),border_extend)
        textpos = text.get_rect(x=self.x + 2, y=self.y)
        surface.blit(text, textpos)
    
class CheckBox(DrawableComponent):
    def __init__(self, x=0, y=0, taborder=0):
        super(CheckBox, self).__init__(x,y,taborder)
        self.selected = False
        self.checked = False
        self.check_font = pygame.font.SysFont("Arial", 24, True)
        
    def HandleKeyPress(self, key):
        if self.selected != True:
            return
        
        if key == K_RETURN or key == K_DOWN or key == K_UP or key == K_LEFT or key == K_RIGHT:
            return
        
        self.checked = not self.checked
        
    def Draw(self, surface):
        
        if (self.selected == True):
            bgcolor = (0,0,255)
            fcolor = (255,255,255)
        else:
            bgcolor = (255,255,255)
            fcolor = (0,0,0)
        
        pygame.draw.rect(surface, bgcolor, (self.x, self.y, 22, 26))
        if self.checked == True:
            text = self.check_font.render("X", 1, fcolor)
        else:
            text = self.check_font.render("", 1, fcolor)
        textpos = text.get_rect(x=self.x + 2, y=self.y)
        surface.blit(text, textpos)
    
class TextBox(DrawableComponent):
    def __init__(self, x=0, y=0,taborder=0):
        super(TextBox, self).__init__(x,y,taborder)
        self.selected = False
        self.value = ""
        self.list_value = []
        self.text_font = pygame.font.SysFont("Arial", 24, True)
        
    def HandleKeyPress(self, key):
        if self.selected != True:
            return
        
        if (key == K_BACKSPACE):
            self.list_value = self.list_value[0:-1]
        elif (key == K_RETURN):
            return False
        elif (key == K_MINUS):
            self.list_value.append("-")
        elif (key < 127):
            self.list_value.append(chr(key))
            
        self._updateDisplayString()
        
        return False
            
    def Draw(self, surface):
        
        if (self.selected == True):
            bgcolor = (0,0,255)
            fcolor = (255,255,255)
        else:
            bgcolor = (255,255,255)
            fcolor = (0,0,0)
        
        pygame.draw.rect(surface, bgcolor, (self.x, self.y, 128, 26))
        text = self.text_font.render(self.value, 1, fcolor)
        textpos = text.get_rect(x=self.x + 2, y=self.y)
        surface.blit(text, textpos)
    
    def _updateDisplayString(self):
        self.value = string.join(self.list_value,"")
    
class Menu(DrawableComponent):
    '''
    classdocs
    '''


    def __init__(self, menu_closed_callback, background=None, x=0, y=0):
        '''
        Constructor
        '''
        self.menu_options = []
        self.menu_font = pygame.font.SysFont("Arial", 24, True)
        self.background = background
        self.current_selection = 0
        self.onMenuClosed = menu_closed_callback
        self.dim = False
        super(Menu, self).__init__(x,y)
        
    def ClearMenuItems(self):
        del self.menu_options[:]
        
    def AddMenuItem(self, menu_text, menu_callback):
        selected = (len(self.menu_options) == 0)
        self.menu_options.append((menu_text, menu_callback, selected))
        #print self.menu_options[0][0]
        
    def HandleKeyPress(self, key):
        if (key == K_DOWN): self.NextItem()
        if (key == K_UP): self.PrevItem()
        if (key == K_RETURN): self.ItemSelected()
        if (key == K_ESCAPE): self.MenuClosed()
        
    def MenuClosed(self):
        if (self.onMenuClosed != None):
            self.onMenuClosed()
        
    def Draw(self, surface):
        if (self.dim):
            # Draw partially transparent background
            temp_surf = pygame.Surface((800,600), SRCALPHA)
            temp_surf.fill((0,0,0,128))
            surface.blit(temp_surf, (0,0))
        
        pygame.draw.rect(surface, self.background, (self.x, self.y, 300, (len(self.menu_options) * 26) + 5))
        
        count = 0
        for (menu_text, callback, selected) in self.menu_options:
            if selected == True:
                forecolor = (0,0,255)
            else:
                forecolor = (0,0,0)
                
            text = self.menu_font.render(menu_text, 1, forecolor)
            textpos = text.get_rect(x=self.x + 5, y=self.y + 5 + (count * 24))
            surface.blit(text, textpos)
            count += 1
        
    def NextItem(self):
        if self.current_selection == len(self.menu_options) - 1:
            self.current_selection = 0
        else:
            self.current_selection += 1
            
        for idx, val in enumerate(self.menu_options):
            if idx == self.current_selection:
                self.menu_options[idx] = (val[0],val[1],True)
            else:
                self.menu_options[idx] = (val[0],val[1],False)
                
    def PrevItem(self):
        if self.current_selection == 0:
            self.current_selection = len(self.menu_options) - 1
        else:
            self.current_selection -= 1
            
        for idx, val in enumerate(self.menu_options):
            if idx == self.current_selection:
                self.menu_options[idx] = (val[0],val[1],True)
            else:
                self.menu_options[idx] = (val[0],val[1],False)
                
    def ItemSelected(self):
        menu_item = self.menu_options[self.current_selection]
        if (menu_item[1] != None):
            callback = menu_item[1]
            callback()
            
#A simple slider
class Slider(object):

    #Constructs the object
    def __init__(self, pos, value=0):
        self.pos = pos
        self.bar = pygame.Surface((275, 15))
        self.bar.fill((200, 200, 200))
        self.slider = pygame.Surface((20, 15))
        self.slider.fill((230, 230, 230))
        pygame.draw.rect(self.bar, (0, 0, 0), (0, 0, 275, 15), 2)
        pygame.draw.rect(self.slider, (0, 0, 0), (-1, -1, 20, 15), 2)
        self.slider.set_at((19, 14), (0, 0, 0))
        self.brect = self.bar.get_rect(topleft = pos)
        self.srect = self.slider.get_rect(topleft = pos)
        self.srect.left = value+pos[0]
        self.clicked = False
        self.value = value

    def setvalue(self, value):
        self.value = value
        self.srect.left = value + self.pos[0]

    #Called once every frame
    def update(self):
        mousebutton = pygame.mouse.get_pressed()
        cursor = Rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 1, 1)
        if cursor.colliderect(self.brect):
            if mousebutton[0]:
                self.clicked = True
            else:
                self.clicked = False
        if not mousebutton[0]:
            self.clicked = False
        if self.clicked:
            self.srect.center = cursor.center
        self.srect.clamp_ip(self.brect)
        self.value = self.srect.left - self.brect.left

    #Draws the slider
    def render(self, surface):
        surface.blit(self.bar, self.brect)
        surface.blit(self.slider, self.srect)