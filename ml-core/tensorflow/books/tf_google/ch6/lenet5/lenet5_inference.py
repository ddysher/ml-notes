#!/usr/bin/env python

import tensorflow as tf

NUM_CHANNELS = 1
NUM_LABELS = 10

# layer1 convolution depth is 32
# layer1 convolution feature map is 5x5 matrix
CONV1_DEEP = 32
CONV1_SIZE = 5

CONV2_DEEP = 64
CONV2_SIZE = 5

FC_SIZE = 512


def inference(input_tensor, train, regularizer):
  with tf.variable_scope('layer1-conv1'):
    # The weight here is the size (CONV1_DEEP) of feature map, or filter.
    # It does not have any relationship with input size.
    conv1_weights = tf.get_variable(
      "weight", [CONV1_SIZE, CONV1_SIZE, NUM_CHANNELS, CONV1_DEEP],
      initializer=tf.truncated_normal_initializer(stddev=0.1))
    # Each feature map has a bias.
    conv1_biases = tf.get_variable(
      "bias", [CONV1_DEEP],
      initializer=tf.constant_initializer(0.0))
    # Here we are using 1 stride.
    conv1 = tf.nn.conv2d(
      input_tensor, conv1_weights, strides=[1, 1, 1, 1], padding='SAME')
    # 'bias_add' is used to add bias to convolution output of a filter.
    relu1 = tf.nn.relu(tf.nn.bias_add(conv1, conv1_biases))

  with tf.name_scope("layer2-pool1"):
    # Here we are using 2 strides. The first and last dimension is batch
    # size and channels, therefore it must be 1.
    pool1 = tf.nn.max_pool(
      relu1, ksize = [1,2,2,1], strides=[1,2,2,1], padding="SAME")

  with tf.variable_scope("layer3-conv2"):
    conv2_weights = tf.get_variable(
      "weight", [CONV2_SIZE, CONV2_SIZE, CONV1_DEEP, CONV2_DEEP],
      initializer=tf.truncated_normal_initializer(stddev=0.1))
    conv2_biases = tf.get_variable(
      "bias", [CONV2_DEEP],
      initializer=tf.constant_initializer(0.0))
    conv2 = tf.nn.conv2d(
      pool1, conv2_weights, strides=[1, 1, 1, 1], padding='SAME')
    relu2 = tf.nn.relu(tf.nn.bias_add(conv2, conv2_biases))

  with tf.name_scope("layer4-pool2"):
    pool2 = tf.nn.max_pool(
      relu2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    # Find the shape of tensor 'pool2' and reshape it to [batch, nodes].
    pool_shape = pool2.get_shape().as_list()
    nodes = pool_shape[1] * pool_shape[2] * pool_shape[3]
    reshaped = tf.reshape(pool2, [pool_shape[0], nodes])

  with tf.variable_scope('layer5-fc1'):
    fc1_weights = tf.get_variable(
      "weight", [nodes, FC_SIZE],
      initializer=tf.truncated_normal_initializer(stddev=0.1))
    if regularizer != None:
      tf.add_to_collection('losses', regularizer(fc1_weights))
    fc1_biases = tf.get_variable(
      "bias", [FC_SIZE],
      initializer=tf.constant_initializer(0.1))

    fc1 = tf.nn.relu(tf.matmul(reshaped, fc1_weights) + fc1_biases)
    if train:
      fc1 = tf.nn.dropout(fc1, 0.5)

  with tf.variable_scope('layer6-fc2'):
    fc2_weights = tf.get_variable(
      "weight", [FC_SIZE, NUM_LABELS],
      initializer=tf.truncated_normal_initializer(stddev=0.1))
    if regularizer != None:
      tf.add_to_collection('losses', regularizer(fc2_weights))

    fc2_biases = tf.get_variable(
      "bias", [NUM_LABELS],
      initializer=tf.constant_initializer(0.1))
    logit = tf.matmul(fc1, fc2_weights) + fc2_biases

  return logit
