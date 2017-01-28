from parcel_tools import *
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-n", "--track_number", required=True, help="Tracking number to be added")
parser.add_argument("-c", "--courier", required=True, help="Courier of the tracking number to be added")
args = vars(parser.parse_args())	
tracking_number = args["track_number"]
courier = args["courier"]

Parcel_tools.add_tracking_number(tracking_number, courier)
print Parcel_tools.validate_tracking_number(tracking_number, courier)