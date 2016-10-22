import pygame
import pygame.camera
import os
import RPi.GPIO as GPIO
from sys import argv
import zbar
import subprocess
import threading

from pygame.locals import *

from qrtools import QR

DEVICE = '/dev/video0'
SIZE = (320, 240)
FILENAME = 'capture.png'

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_VIDEODRIVER','fbcon')
GPIO.setmode(GPIO.BCM)   # Set for broadcom numbering not board numbers...
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def GPIO27_callback(channel):
    print "Button 27 pressed, quit"
    capture = False
    exit()

# http://blog.danielkerris.com/?p=225 
def camstream():
    pygame.init()
    pygame.camera.init()
    display = pygame.display.set_mode(SIZE, 0)
    camera = pygame.camera.Camera(DEVICE, SIZE)
    camera.start()
    screen = pygame.surface.Surface(SIZE, 0, display)
    capture = True
    while capture:
        screen = camera.get_image(screen)
        display.blit(screen, (0,0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == QUIT:
                capture = False
            elif event.type == KEYDOWN and event.key == K_s:
                pygame.image.save(screen, FILENAME)
    camera.stop()
    pygame.quit()
    return

def camstream_QR():
pygame.init()
pygame.camera.init()
display = pygame.display.set_mode(SIZE, 0)
camera = pygame.camera.Camera(DEVICE, SIZE)
camera.start()
screen = pygame.surface.Surface(SIZE, 0, display)
capture = True
while capture:
screen = camera.get_image(screen)
pygame.image.save(screen, FILENAME)
myCode = QR(filename=unicode(FILENAME))
if myCode.decode():
    print myCode.data_type
    print myCode.data_to_string()
    capture = False
display.blit(screen, (0,0))
pygame.display.flip()

camera.stop()
pygame.quit()
return myCode.data_type, myCode.data_to_string()

if __name__ == '__main__':
    GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime = 300)
    camstream_QR()
    

