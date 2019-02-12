# Read a color image in grayscale and display it.

import numpy as np
import cv2

# Load a color image in grayscale.
img = cv2.imread('./assets/messi5.jpg', 0)

cv2.imshow('image', img)

# Wait for any key press and exit.
cv2.waitKey(0)
cv2.destroyAllWindows()
