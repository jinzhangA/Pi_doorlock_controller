import zbar
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


S3_ACCESS_KEY = settings.["S3_ACCESS_KEY"]
S3_SECRET_KEY = settings.["S3_SECRET_KEY"]
BUCKET_NAME = settings.["BUCKET_NAME"]
TWILIO_SID = settings.["TWILIO_SID"]
TWILIO_AUTH = settings.["TWILIO_AUTH"]
TO = settings.["TO"]
FROM = settings.["FROM"]

DEVICE = '/dev/video0'
SIZE = (320, 240)
FILENAME = 'capture.png'

def GPIO27_callback(channel):
    print "Button 27 pressed, quit"
    capture = False
    exit()

class QR_tools:
	@deprecated
	def read_from_camera(self, display = False, kill_key = True):
		if kill_key:
			GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime = 300)
		proc = zbar.Processor()
		proc.parse_config('enable')
		device = '/dev/video0'
		proc.init(device)
		if display: proc.visible = True

		try:
			proc.process_one()
		except KeyboardInterrupt:
			return 'None', 'None'
		# proc.visible = Fasle
		for symbol in proc.results:
			res_type = symbol.type
			res_data = symbol.data
		return res_type, res_data

	def gen_qr(self, data = 'test_data', filename = '/home/pi/Pi_doorlock_controller/qr_code/test_qr.png'):
		my_code = qrcode.make(data)
		my_code.save(filename)
		return filename

	def camstream_QR(self, kill_key = True):
		if kill_key:
			GPIO.setmode(GPIO.BCM)   # Set for broadcom numbering not board numbers...
			GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.add_event_detect(27, GPIO.FALLING, callback = GPIO27_callback, bouncetime = 300)

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
				capture = False
			display.blit(screen, (0,0))
			pygame.display.flip()

		camera.stop()
		pygame.quit()
		return myCode.data_type, myCode.data_to_string()

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
		twilio_SID = TWILIO_SID,
		twilio_AUTH = TWILIO_AUTH):

		url = self.gen_and_upload_QR(data = QR_data, url_lifetime = url_lifetime)
		client = TwilioRestClient(twilio_SID, twilio_AUTH)
		client.messages.create(to=receiver, from_=sender, body=message_body,
                       media_url=url)


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
	qr_tools.send_QR(QR_data="Test drive for QR package")
	time.sleep(5)
	res_type, res_data = qr_tools.camstream_QR()
	print res_type, res_data





