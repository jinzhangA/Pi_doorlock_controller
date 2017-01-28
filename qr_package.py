from qrtools import QR
import qrcode
import pygame
import pygame.camera
import os
from pygame.locals import *
import RPi.GPIO as GPIO
import boto
from twilio.rest import TwilioRestClient
import time
from setting import settings
import pickle
import string
import random
import hashlib
from string import printable
import argparse


S3_ACCESS_KEY = settings["S3_ACCESS_KEY"]
S3_SECRET_KEY = settings["S3_SECRET_KEY"]
BUCKET_NAME = settings["BUCKET_NAME"]
TWILIO_SID = settings["TWILIO_SID"]
TWILIO_AUTH = settings["TWILIO_AUTH"]
TO = settings["TO"]
FROM = settings["FROM"]

DEVICE = '/dev/video0'
SIZE = (320, 240)
FILENAME = 'capture.png'
QR_PASSCODE_DICT = 'qr_pwd.pickle'

def GPIO27_callback(channel):
    print "Button 27 pressed, quit"
    capture = False
    exit()

class QR_tools:
	# def read_from_camera(self, display = False, kill_key = True):
	# 	if kill_key:
	# 		GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime = 300)
	# 	proc = zbar.Processor()
	# 	proc.parse_config('enable')
	# 	device = '/dev/video0'
	# 	proc.init(device)
	# 	if display: proc.visible = True

	# 	try:
	# 		proc.process_one()
	# 	except KeyboardInterrupt:
	# 		return 'None', 'None'
	# 	# proc.visible = Fasle
	# 	for symbol in proc.results:
	# 		res_type = symbol.type
	# 		res_data = symbol.data
	# 	return res_type, res_data

	def gen_qr(self, data = 'test_data', filename = '/home/pi/Pi_doorlock_controller/qr_code/test_qr.png'):
		my_code = qrcode.make(data)
		my_code.save(filename)
		return filename

	def camstream_QR(self, kill_key = False):

		# this part is a backup bail out incase the function cannot end properly
		if kill_key:
			GPIO.setmode(GPIO.BCM)   # Set for broadcom numbering not board numbers...
			GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime = 300)

		# setup the pygame environement
		pygame.init()
		pygame.camera.init()
		pygame.mouse.set_visible(False)

		# setup the display
		display = pygame.display.set_mode(SIZE, 0)

		# setup the pygame camera with the size 320*240
		camera = pygame.camera.Camera(DEVICE, SIZE)
		camera.start()
		screen = pygame.surface.Surface(SIZE, 0, display)
		capture = True
		while capture:
			# get a picture from the camera
			screen = camera.get_image(screen)
			# save the picture to file
			pygame.image.save(screen, FILENAME)
			# load the file and dectect any QR code in it with QR() function
			myCode = QR(filename=unicode(FILENAME))

			# if any code dectected, stop the loop by setting the caputure to false
			if myCode.decode():
				capture = False

			# display the picture on the screen
			display.blit(screen, (0,0))
			pygame.display.flip()

		camera.stop()
		pygame.quit()
		return myCode.data_to_string()


	def camstream_QR_nested(self, pygame, screen, timeout = 30):
		pygame.camera.init()
		camera = pygame.camera.Camera(DEVICE, SIZE)
		camera.start()
		capture = True
		start_time = time.time()

		while capture and (time.time() - start_time <= timeout):
			pic = camera.get_image()
			pygame.image.save(pic, FILENAME)
			myCode = QR(filename=unicode(FILENAME))
			if myCode.decode():
				capture = False
			screen.blit(pic, (0,0))
			pygame.display.flip()

		camera.stop()
		text = ''.join(char for char in myCode.data_to_string() if char in printable)
		
		return text

	def gen_and_upload_QR(self, 
		data = 'test_data',
		bucket_name = BUCKET_NAME,
		s3_file_name = 'test_qr.png',
		url_lifetime = 0):

		file_name = self.gen_qr(data=data)
		s3 = boto.connect_s3(S3_ACCESS_KEY, S3_SECRET_KEY)
		bucket = s3.get_bucket(bucket_name)
		key = bucket.new_key('qrcode/%s'%(s3_file_name))
		key.set_contents_from_filename(file_name)
		key.set_acl('public-read')
		return  key.generate_url(expires_in=url_lifetime, query_auth=False, force_http=True)


	def send_QR(self, 
		QR_data = 'test_data', 
		message_body = "Hello!",
		url_lifetime = 0,
		sender = FROM,
		receiver = TO,
		s3_file_name = 'test_qr.png',
		twilio_SID = TWILIO_SID,
		twilio_AUTH = TWILIO_AUTH):

		url = self.gen_and_upload_QR(data = QR_data, url_lifetime = url_lifetime, s3_file_name = s3_file_name)
		client = TwilioRestClient(twilio_SID, twilio_AUTH)
		client.messages.create(to=receiver, from_=sender, body=message_body,
                       media_url=url)

	def send_text_message(self, 
		message_body = "Hello!",
		sender = FROM,
		receiver = TO,
		twilio_SID = TWILIO_SID,
		twilio_AUTH = TWILIO_AUTH):

		client = TwilioRestClient(twilio_SID, twilio_AUTH)
		client.messages.create(to=receiver, from_=sender, body=message_body)
	# this function is refered from page: http://davidsj.co.uk/blog/python-generate-random-password-strings/
	def gen_random_password(self, pwdSize):
		# letters, digits and punctuation
		chars = string.letters + string.digits + string.punctuation
		return ''.join(random.sample(chars, pwdSize))

	def send_QR_passcode(self,
		phone_number_of_guest,
		valid_hours=1,
		pwdSize=16):
		passcode = self.gen_random_password(pwdSize)
		f = open(QR_PASSCODE_DICT, 'rb')
		pwd_dict = pickle.load(f)
		f.close()
		pwd_dict = self.clean_QR_dict(pwd_dict)
		now = int(time.time())
		pwd_dict[passcode] = (now, phone_number_of_guest, now+valid_hours*3600)
		f = open(QR_PASSCODE_DICT, 'wb')
		pickle.dump(pwd_dict, f)
		f.close()
		

		message_body = "This is your QR passcode, it will be valid for %d hours."%(valid_hours)
		s3_file_name = 'QR_pass.png'
		self.send_QR(QR_data = passcode, 
			message_body = message_body, 
			receiver = phone_number_of_guest, 
			url_lifetime = valid_hours*3600,
			s3_file_name = s3_file_name)

	def check_qr_code(self, text):
		check = False	
		text = ''.join(char for char in text if char in printable)
		f = open(QR_PASSCODE_DICT, 'rb')
		pwd_dict = pickle.load(f)
		f.close()
		pwd_dict = self.clean_QR_dict(pwd_dict)
		if pwd_dict.has_key(text):
			check = True
			number = pwd_dict[text][1]
			pwd_dict = self.clean_QR_dict(pwd_dict, text)
		f = open(QR_PASSCODE_DICT, 'wb')
		pickle.dump(pwd_dict, f)
		f.close()
		if not check:
			return False
		else:
			return number
		# print 'cleaned passcode %s, length %d, type %s\n'%(text, len(text), type(text))
		# print 'received passcode %s, length %d, type %s\n'%(text, len(text), type(text))


	def clean_QR_dict(self, qr_dict, clean_key=None):
		temp_qr_dict = {}
		for key, value in qr_dict.iteritems():
			if value[2] >= time.time() and key != clean_key:
				temp_qr_dict[key] = value
		return temp_qr_dict




if __name__ == "__main__":


	os.putenv('SDL_FBDEV', '/dev/fb1')
	os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
	os.putenv('SDL_MOUSEDRV', 'TSLIB')
	os.putenv('SDL_VIDEODRIVER','fbcon')
	GPIO.setmode(GPIO.BCM)   # Set for broadcom numbering not board numbers...
	GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	# res_type, res_data = QR_tools.read_from_camera(display = True)
	qr_tools = QR_tools()
	# res_type, res_data = qr_tools.camstream_QR()
	# print res_type, res_data

	# qr_tools.gen_qr(data="Test drive for QR package")
	# qr_tools.gen_and_upload_QR()
	qr_tools.send_QR(QR_data="test_true")
	# time.sleep(5)
	# qr_tools.send_QR_passcode('6073191283')
	# f = open(QR_PASSCODE_DICT, 'rb')
	# pwd_dict = pickle.load(f)
	# f.close()
	# print 'from main function, print ',pwd_dict
	# res_data = qr_tools.camstream_QR()
	# print res_data
	# check = qr_tools.check_qr_code(res_data)
	# print check






