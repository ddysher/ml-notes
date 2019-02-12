#!/usr/bin/env python
#
# Train a LeNet5 CNN network.

import numpy as np
import os
import tensorflow as tf

import lenet5_inference

from tensorflow.examples.tutorials.mnist import input_data

INPUT_NODE = 784              # 28 x 28 image = 784 input nodes
OUTPUT_NODE = 10              # 10 classes for MNIST = 10 output nodes
IMAGE_SIZE = 28               # 28 x 28 image
NUM_CHANNELS = 1              # grayscale image, thus channel is 1
BATCH_SIZE = 100
LEARNING_RATE_BASE = 0.01
LEARNING_RATE_DECAY = 0.99
REGULARIZATION_RATE = 0.0001
TRAINING_STEPS = 6000
MOVING_AVERAGE_DECAY = 0.99


def train(mnist):
  # Define the input placeholder as 4-D tensor:
  #   [batch_size, width, height, channels]
  shape = [BATCH_SIZE, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS]
  x = tf.placeholder(tf.float32, shape, name='x-input')
  y_ = tf.placeholder(tf.float32, [None, OUTPUT_NODE], name='y-input')

  # The following training steps are similar to training steps in ch5.
  regularizer = tf.contrib.layers.l2_regularizer(REGULARIZATION_RATE)
  y = lenet5_inference.inference(x, False, regularizer)
  global_step = tf.Variable(0, trainable=False)

  variable_averages = tf.train.ExponentialMovingAverage(
    MOVING_AVERAGE_DECAY, global_step)
  variables_averages_op = variable_averages.apply(tf.trainable_variables())
  cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
    logits=y, labels=tf.argmax(y_, 1))
  cross_entropy_mean = tf.reduce_mean(cross_entropy)
  loss = cross_entropy_mean + tf.add_n(tf.get_collection('losses'))
  learning_rate = tf.train.exponential_decay(
    LEARNING_RATE_BASE,
    global_step,
    mnist.train.num_examples / BATCH_SIZE, LEARNING_RATE_DECAY,
    staircase=True)

  train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(
    loss, global_step=global_step)
  with tf.control_dependencies([train_step, variables_averages_op]):
    train_op = tf.no_op(name='train')

  saver = tf.train.Saver()
  with tf.Session() as sess:
    tf.global_variables_initializer().run()
    for i in range(TRAINING_STEPS):
      xs, ys = mnist.train.next_batch(BATCH_SIZE)

      # Note is important here to reshape the input.
      reshaped_xs = np.reshape(
        xs, (BATCH_SIZE, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS))
      _, loss_value, step = sess.run(
        [train_op, loss, global_step], feed_dict={x: reshaped_xs, y_: ys})

      if i % 1000 == 0:
        print("After %d training step(s), loss on training batch is %g." %
              (step, loss_value))


def main(argv=None):
  mnist = input_data.read_data_sets("/tmp/MNIST_data", one_hot=True)
  train(mnist)


if __name__ == '__main__':
  main()
