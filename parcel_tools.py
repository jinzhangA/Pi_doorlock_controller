# from packagetrack import Package
import pickle
import subprocess
import json
import datetime
import os
from setting import settings
import argparse
TRACKING_NUMBERS = 'tracking_numbers.pickle'
ShippoToken = settings['ShippoToken']

class Parcel_tools(object):
	"""docstring for Parcel_tools"""

	# The user can add a tracking number to the database with this function
	# Courier name, e.g. fedex, and tracking number is needed for this function
	@staticmethod
	def add_tracking_number(number, courier):
		f = open(TRACKING_NUMBERS, 'rb')
		tracking_numbers = pickle.load(f)
		f.close()

		tracking_numbers = Parcel_tools.clean_tracking_numbers(tracking_numbers)
		tracking_numbers.append( (number, courier) )
		f = open(TRACKING_NUMBERS, 'wb')
		pickle.dump(tracking_numbers, f)
		f.close()

	# clean the loaded tracking numbers
	# 2 types of tracking numbers will be removed
	# 1: Out of date
	# 2: Just used to open the door
	@staticmethod
	def clean_tracking_numbers(tracking_numbers, clean_specific_number=None):
		temp_tracking_numbers = []
		for number, courier in tracking_numbers:
			if Parcel_tools.validate_tracking_number(number, courier) and number != clean_specific_number:
				temp_tracking_numbers.append( (number, courier) )
		return temp_tracking_numbers


	# validate a tracking number
	# if check_today is false, this function will check if the tracking number still valid(still in transit)
	# if check_today is True, this function will also check if the tracking number says the package will be delivered today
	@staticmethod
	def validate_tracking_number(number, courier, check_today = False):
		# Only package in transit will be considered as valid
		cmd = "curl https://api.goshippo.com/v1/tracks/%s/%s -H 'Authorization: ShippoToken %s'"\
		%(courier, number, ShippoToken)
		
		try:
			ret = subprocess.check_output(cmd, shell=True)
			ret_dict = json.loads(ret)

			# get the last(latest) tracking history
			status = ret_dict[u'tracking_history'][-1][u'status']
			# print status
			eta = str(ret_dict[u'eta'])
			eta_date = datetime.datetime.strptime( str(eta), "%Y-%m-%dT%H:%M:%SZ" ).date()
			print eta_date, status
			# print eta_date
			today_date = datetime.datetime.now().date()
			if check_today:
				if status == 'TRANSIT' and eta_date == today_date:
					return True
				else:
					return False
			else:
				if status == 'TRANSIT':
					return True
				else:
					return False
		except:
			return False

	# this is the function to check the received tracking number from the camera
	# return True iff:
	# 	the number is in the library(entered by the user)
	#	the number is valid
	@staticmethod
	def check_tracking_number(number_to_check, testing = False):
		if not testing:
			found = False
			f = open(TRACKING_NUMBERS, 'rb')
			tracking_numbers = pickle.load(f)
			f.close()

			for number, courier in tracking_numbers:
				if number == number_to_check:
					found = (number, courier)
					break

			if found == False:
				return False

			if Parcel_tools.validate_tracking_number(number, courier, True):
				f = open(TRACKING_NUMBERS, 'wb')
				tracking_numbers = Parcel_tools.clean_tracking_numbers(tracking_numbers, number)
				tracking_numbers = pickle.dump(tracking_numbers, f)
				f.close()
				return number, courier
			return False
		else:
			if number_to_check == 'test_true':
				return "testing_mode_code", "testing_courier"
			else:
				return False


		
if __name__ == '__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-n", "--track_number", required=True, help="Tracking number to be added")
	parser.add_argument("-c", "--courier", required=True, help="Courier of the tracking number to be added")
	args = vars(parser.parse_args())	
	tracking_number = args["track_number"]
	courier = args["courier"]
	if not os.path.exists(TRACKING_NUMBERS):
		tracking_numbers = []
		f = open(TRACKING_NUMBERS, 'w+b')
		pickle.dump(tracking_numbers, f)
		f.close()
	Parcel_tools.add_tracking_number(tracking_number, courier)
	f = open(TRACKING_NUMBERS, 'rb')
	tracking_numbers = pickle.load(f)
	f.close()
	print 'Current tracking numbers in the database: \n', tracking_numbers
	Parcel_tools.validate_tracking_number(tracking_number, courier)
	