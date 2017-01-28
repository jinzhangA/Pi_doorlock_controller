# This nice pygame menu is edited base on code by garthvh from 
# https://github.com/garthvh/pitftmenu/blob/master/menu_8button.py

# the original code was for screen of size 480*320 with 8 buttons
# this project is using piTFT of size 320*240 and 4 buttons
import cv2

import sys, pygame
from pygame.locals import *
import time
import subprocess
import os
import argparse
import pickle
import numpy
from qr_package import *
from parcel_tools import * 


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--threshold", default=90.0, help="Threshold of the recognizer, default 150")
parser.add_argument("-T", "--test_mode", action="store_true",help="Flag for testing mode")
parser.add_argument("-F", "--check_courier_face", action="store_true",help="Flag for checking the courier's face")

args = vars(parser.parse_args())

threshold = float(args['threshold'])
testing_mode = args['test_mode']
check_courier_face = args['check_courier_face']

os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_VIDEODRIVER','fbcon')

# Initialize pygame and hide mouse
pygame.init()
pygame.mouse.set_visible(0)

# define function for printing text in a specific place with a specific width and height with a specific colour and border
def make_button(text, xpo, ypo, height, width, colour):
	font=pygame.font.Font(None,30)
	label=font.render(str(text), 1, (colour))
	screen.blit(label,(xpo,ypo))
	pygame.draw.rect(screen, blue, (xpo-10,ypo-10,width,height),3)


# Define each button press action
def button(number):
	print "You pressed button ",number

	if number == 1:
		check = unlock_with_face()
		if not check:
			warning = 'Warning, an unauthorised person is trying to open your door with face recognization' 
			print "Send message: ", warning
			qr_tools.send_text_message(warning)
		else:
			print 'Door opened'

	if number == 2:
		if testing_mode:
			print 'Using testing mode of the parcel functions'
		res_data = qr_tools.camstream_QR_nested(pygame, screen)

		check_code = Parcel_tools.check_tracking_number(res_data, testing_mode)
		if check_code == False:
			warning = 'Warning, someone is trying to scan an invalid tracking number to open your door.'
			print "Send message: ", warning
			qr_tools.send_text_message(warning)
		else:
			number, courier = check_code
			if check_courier_face:
				check_face = check_deliver_face()
				if check_face == False:
					warning = 'Warning, an unauthorised courier is trying to deliver a package to your home.'
					print "Send message: ", warning
					qr_tools.send_text_message(warning)
				else:
					print 'Door open'
					message = 'Your package No. %s has been delivered by %s'%(number, courier)
					print "Send message: ", message
					qr_tools.send_text_message(message)
			else:
				print 'Door open'
				message = 'Your package No. %s has been delivered by %s'%(number, courier)
				print "Send message: ", message
				qr_tools.send_text_message(message)
		

	if number == 3:
		res_data = qr_tools.camstream_QR_nested(pygame, screen)
		check = qr_tools.check_qr_code(res_data)
		if not check:
			warning = 'Warning, someone is trying to scan an invalid QR pass code to open your door.'
			print "Send message: ", warning
			qr_tools.send_text_message(warning)
		else:
			message = 'Your guest with phone number %s has opened your door'%(check)
			print "Send message: ", message
			qr_tools.send_text_message(message)

	if number == 4:
		pass

#colors     R    G    B
blue    = (  0,   0, 255)
black   = (  0,   0,   0)
cyan    = ( 50, 255, 255)


# Set up the base menu you can customize your menu with the colors above

#set size of the screen
size = width, height = 320, 240
screen = pygame.display.set_mode(size)


def recognize_face(timeout = 30):
	camera = cv2.VideoCapture(0)
	camera.set(3,320)
	camera.set(4,240)
	cascade_path = 'cascades/haarcascade_frontalface_default.xml'
	facedetector = cv2.CascadeClassifier(cascade_path)
	face_reconizer=cv2.createLBPHFaceRecognizer(threshold=threshold)
	face_reconizer.load('recognizers/default_recognizer.model')
	with open('recognizers/default_recognizer.pickle', 'rb') as f:
		name_dict=pickle.load(f)
	f.close()
	result_count = 0
	name = None
	start_time = time.time()
	while time.time() - start_time <= timeout and name == None:
		(grabbed, frame) = camera.read()
		if not grabbed:
			break

		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faceRects = facedetector.detectMultiScale(gray)
	 
		if len(faceRects):
			(x, y, w, h) = max(faceRects, key=lambda b:(b[2] * b[3]))
			face = gray[y:y + h, x:x + w]
			index, confidence = face_reconizer.predict(face)
			print index, name_dict[index], confidence
			if index != -1:
				name = name_dict[index]
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			result_count += 1
			if result_count >= 10:
				name = 'Unknown'
		pyimage=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
		pyimage=numpy.rot90(pyimage)
		pyimage=pygame.surfarray.make_surface(pyimage)
		screen.blit(pyimage, (0,0))
		pygame.display.flip()

		key = cv2.waitKey(1)
	camera.release()
	cv2.destroyAllWindows()
	return name

def unlock_with_face():
	name = recognize_face()
	if not name: return False
	if 'master' in name:
		return True
	else:
		return False

def check_deliver_face():
	name = recognize_face()
	if not name: return False
	if 'courier' in name:
		return True
	else:
		return False

qr_tools = QR_tools()
go = True
while go:
	try:
		screen.fill(black)
		
		make_button("Reconize face", 10, 10, 110, 150, cyan)
		make_button("Parcel", 170, 10, 110, 150, cyan)
		make_button("QR code", 10, 130, 110, 150, cyan)
		make_button("Others", 170, 130, 110, 150, cyan)

		for event in pygame.event.get():
			if event.type == pygame.MOUSEBUTTONDOWN:
				
				touch_position = pygame.mouse.get_pos()
				
				if 10 <= touch_position[0] <= 160 and 10 <= touch_position[1] <= 120:
					button(1)
				if 170 <= touch_position[0] <= 310 and 10 <= touch_position[1] <= 120:
					button(2)
				if 10 <= touch_position[0] <= 160 and 130 <= touch_position[1] <=230:
					button(3)
				if 170 <= touch_position[0] <= 310 and 130 <= touch_position[1] <=230:
					button(4)
		pygame.display.update()

	except KeyboardInterrupt:
		go = False
pygame.quit()
sys.exit()
	