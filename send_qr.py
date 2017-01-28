from qr_package import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--number", required=True, help="Phone number of the receiver")
parser.add_argument("-t", "--valid_time", default=1, help="Valid hours of the QR code")
args = vars(parser.parse_args())
number = str(args['number'])
valid_hours = int(args['valid_time'])

if not os.path.exists('qr_pwd.pickle'):
	qr_pwd = {}
	f = open('qr_pwd.pickle', 'w+b')
	pickle.dump(qr_pwd, f)
	f.close()
qr_tools = QR_tools()
qr_tools.send_QR_passcode(phone_number_of_guest=number, valid_hours=valid_hours)

print 'A QR passcode has been send to %s, valid for %d hour(s)'%(number, valid_hours)

