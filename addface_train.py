import cv2
import os
import numpy
from imutils import encodings
import argparse
import pickle
import glob
import random
import imutils
import time



parser = argparse.ArgumentParser()
parser.add_argument("-a", "--add_face", action="store_true",help="Flag for adding face")
parser.add_argument("-n", "--user_name", help="Name of the person to add")
parser.add_argument("-t", "--user_type", default="master", help="Type of the user: normal or courier")
parser.add_argument("-T", "--train", action="store_true",help="Flag for training the model")
parser.add_argument("-p", "--recognizer_path", default='recognizers/', help="Path to the face recognizer")
parser.add_argument('-N', "--recognizer_name", default='default_recognizer',help='Recognizer name')
args = vars(parser.parse_args())

name = args["user_name"]
if name == None:
	time_stamp = str(int(time.time()))
	name = 'someone_'+time_stamp
user_type=args['user_type']
train=args['train']
add_face = args['add_face']
recognizer_name = args['recognizer_name']
recognizer_path = args['recognizer_path']

if add_face:
	if user_type=='courier':
		name = name+'_courier'
	else:
		name = name+'_master'

	camera = cv2.VideoCapture(0)
	camera.set(3,500)
	cascade_path = 'cascades/haarcascade_frontalface_default.xml'
	face_detector = cv2.CascadeClassifier(cascade_path)
	file_name='faces/'+name+'.txt'
	f = open(file_name, 'a+')

	total = 0
	green = (0, 255, 0)
	red = (0, 0, 255)

	while True:
		(has_frame, frame) = camera.read()
		if not has_frame:
			break
		gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		detected_faces_positions = face_detector.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=9, minSize=(100, 100))

		if len(detected_faces_positions):
			(x, y, w, h) = max(detected_faces_positions, key=lambda b:(b[2] * b[3]))
			face = gray_frame[y:y + h, x:x + w].copy(order="C")
			f.write("{}\n".format(encodings.base64_encode_image(face)))
			total += 1
			color=green
		else:
			color=red

		cv2.circle(frame, (20, 20), 10,color,-1)
		cv2.imshow("Face capturing", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			break

	# close the output file, cleanup the camera, and close any open windows
	print '%d frames of %s captured'%(total, name)
	f.close()
	camera.release()
	cv2.destroyAllWindows()

if train:
	face_recognizer = cv2.createLBPHFaceRecognizer()
	name_dict = {}
	for (i, path) in enumerate(glob.glob("faces/*.txt")):
		name = path[path.rfind("/") + 1:].replace(".txt", "")
		print 'No.%d, %s'%(i, name)

		# the following two lines of code is referred from the pyimage research course. 
		samples = open(path).read().strip().split("\n")
		samples=random.sample(samples, min(len(samples),100))

		faces = []

		# loop over the faces in the sample
		for face in samples:
			# decode the face and update the list of faces
			faces.append(encodings.base64_decode_image(face))
		if i==0:
			face_recognizer.train(faces, numpy.array([i]*len(faces)))
		else:
			face_recognizer.update(faces, numpy.array([i]*len(faces)))
		name_dict[i]=name
	name_dict[-1]='Unknown'

	if not os.path.exists(recognizer_path+recognizer_name+".model"):
			os.system('sudo touch %s%s.model'%(recognizer_path, recognizer_name))

	face_recognizer.save(recognizer_path+recognizer_name+".model")
	with open(recognizer_path+recognizer_name+".pickle", "wb") as f:
		pickle.dump(name_dict, f)
	f.close()




