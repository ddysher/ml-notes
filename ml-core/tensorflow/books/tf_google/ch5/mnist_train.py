#!/usr/bin/env python

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
import mnist_inference
import os

BATCH_SIZE = 100
LEARNING_RATE_BASE = 0.8
LEARNING_RATE_DECAY = 0.99
REGULARIZATION_RATE = 0.0001
TRAINING_STEPS = 30000
MOVING_AVERAGE_DECAY = 0.99
MODEL_SAVE_PATH="/tmp/MNIST_model/"
MODEL_NAME="mnist_model"


def train(mnist):
  # Input and label placeholders; 'None' means input size is not specified.
  x = tf.placeholder(
    tf.float32, [None, mnist_inference.INPUT_NODE], name='x-input')
  y_ = tf.placeholder(
    tf.float32, [None, mnist_inference.OUTPUT_NODE], name='y-input')

  # Create network (add regularizer to losees).
  regularizer = tf.contrib.layers.l2_regularizer(REGULARIZATION_RATE)
  y = mnist_inference.inference(x, regularizer)
  global_step = tf.Variable(0, trainable=False)

  variable_averages = tf.train.ExponentialMovingAverage(
    MOVING_AVERAGE_DECAY,
    global_step)
  variables_averages_op = variable_averages.apply(tf.trainable_variables())

  # Use 'sparse_softmax_cross_entropy_with_logits' to calcute lose. 'logits' is
  # the raw output and 'labels' is the correct answers.
  cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
    logits=y, labels=tf.argmax(y_, 1))
  cross_entropy_mean = tf.reduce_mean(cross_entropy)
  # 'add_n' adds all tensors in 'losses' element wise.
  loss = cross_entropy_mean + tf.add_n(tf.get_collection('losses'))

  # Applies exponential decay to the learning rate.
  learning_rate = tf.train.exponential_decay(
    LEARNING_RATE_BASE,
    global_step,
    mnist.train.num_examples / BATCH_SIZE, LEARNING_RATE_DECAY,
    staircase=True)
  train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(
    loss, global_step=global_step)

  # Make sure both 'train_step' and 'variables_averages_op' are completed.
  with tf.control_dependencies([train_step, variables_averages_op]):
    train_op = tf.no_op(name='train')

  saver = tf.train.Saver()
  with tf.Session() as sess:
    tf.global_variables_initializer().run()
    # Start training loop; save model every 1000 steps.
    for i in range(TRAINING_STEPS):
      xs, ys = mnist.train.next_batch(BATCH_SIZE)
      _, loss_value, step = sess.run([train_op, loss, global_step],
                                     feed_dict={x: xs, y_: ys})
      if i % 1000 == 0:
        print("After %d training step(s), loss on training batch is %g." %
              (step, loss_value))
        saver.save(sess, os.path.join(MODEL_SAVE_PATH, MODEL_NAME),
                   global_step=global_step)


def main(argv=None):
  mnist = input_data.read_data_sets("/tmp/MNIST_data", one_hot=True)
  train(mnist)


if __name__ == '__main__':
  tf.app.run()
