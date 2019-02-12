#!/usr/bin/env python
#
# Create SavedModel from freezed model

from __future__ import print_function

import os

import tensorflow as tf
from tensorflow.python.framework import graph_util,graph_io
from tensorflow.python.platform import gfile

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

restore_graph = tf.Graph()
with tf.Session() as sess:
    with gfile.FastGFile('results/frozen_model.pb', 'rb') as f:
      # Read the graph from freezed model.
      graph_def = tf.GraphDef()
      graph_def.ParseFromString(f.read())
      # Imports the graph from `graph_def` into the current default `Graph`.
      sess.graph.as_default()
      tf.import_graph_def(graph_def, name='')

    input_tensor = {}
    input_tensor['inputs_1'] = sess.graph.get_tensor_by_name(
      'Placeholder/inputs_placeholder:0')
    output_tensor = {}
    output_tensor['output1'] = sess.graph.get_tensor_by_name(
      'Accuracy/predictions:0')

    tf.saved_model.simple_save(
      sess, export_dir='/tmp/tffrmodel',
      inputs=input_tensor, outputs=output_tensor)
