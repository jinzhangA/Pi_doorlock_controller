import cv2
camera = cv2.VideoCapture(0)

for i in range(100):
    (grabbed, frame) = camera.read()
    print grabbed