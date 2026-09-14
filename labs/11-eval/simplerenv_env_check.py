import sys

import cv2
import numpy
import simpler_env

print("Python:", sys.executable)
print("NumPy:", numpy.__version__)
print("OpenCV:", cv2.__version__)
print("Number of tasks:", len(simpler_env.ENVIRONMENTS))
print(simpler_env.ENVIRONMENTS)
