#!/usr/bin/env python
#
# Common module for mnist_train.py and mnist_eval.py. The file defines forward
# propagation that can be used for both of the files.

import tensorflow as tf

INPUT_NODE = 784
OUTPUT_NODE = 10
LAYER1_NODE = 500


def get_weight_variable(shape, regularizer):
  weights = tf.get_variable(
    "weights", shape,
    initializer=tf.truncated_normal_initializer(stddev=0.1))

  # Apply regularization to the weight variable. This is only used in training;
  # for evaluation, we do not calculate regularization.
  if regularizer != None:
    tf.add_to_collection('losses', regularizer(weights))
  return weights


def inference(input_tensor, regularizer):
  # The same network structure for training and evaluation.
  with tf.variable_scope('layer1'):
    weights = get_weight_variable([INPUT_NODE, LAYER1_NODE], regularizer)
    biases = tf.get_variable("biases", [LAYER1_NODE],
                             initializer=tf.constant_initializer(0.0))
    layer1 = tf.nn.relu(tf.matmul(input_tensor, weights) + biases)

  with tf.variable_scope('layer2'):
    weights = get_weight_variable([LAYER1_NODE, OUTPUT_NODE], regularizer)
    biases = tf.get_variable("biases", [OUTPUT_NODE],
                             initializer=tf.constant_initializer(0.0))
    layer2 = tf.matmul(layer1, weights) + biases

  return layer2
