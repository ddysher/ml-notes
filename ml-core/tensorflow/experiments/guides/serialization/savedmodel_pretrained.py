#!/usr/bin/env python
#
# Load pretrained model and run a forward pass.

from __future__ import print_function

import os

import cv2
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.python.framework import graph_util,graph_io
from tensorflow.python.platform import gfile

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

export_dir = "./pretrainedresnet/1"
image_path = "./assets/cat.jpeg"
# image_path = "./assets/dog.jpg"

# Read the image, resize to (224, 224) and then reshape to (224, 224, 3).  Since
# the model receives (64, 224, 224, 3), we repeat the first dimension (batch).
image = Image.open(image_path)
image = cv2.resize(np.array(image), (224, 224))
image_np = image.reshape((1, 224, 224, 3)).astype(np.uint8)
image_np = np.repeat(image_np, 64, axis=0)

# Run the session.
with tf.Session(graph=tf.Graph()) as sess:
  tf.saved_model.loader.load(sess, ['serve'], export_dir)
  graph = tf.get_default_graph()
  input_image = graph.get_tensor_by_name('input_tensor:0')
  classes = graph.get_tensor_by_name('ArgMax:0')
  probabilities = graph.get_tensor_by_name('softmax_tensor:0')
  cls, prob = sess.run([classes, probabilities], feed_dict={input_image: image_np})
  print(cls, prob)
