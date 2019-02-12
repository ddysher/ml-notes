"""
A simple MNIST classifier.

python helloworld-1.py \
  --ps_hosts=localhost:2222,localhost:2223 \
  --worker_hosts=localhost:2224,localhost:2225 \
  --job_name=ps --task_index=0

python helloworld-1.py \
  --ps_hosts=localhost:2222,localhost:2223 \
  --worker_hosts=localhost:2224,localhost:2225 \
  --job_name=ps --task_index=1

python helloworld-1.py \
  --ps_hosts=localhost:2222,localhost:2223 \
  --worker_hosts=localhost:2224,localhost:2225 \
  --job_name=worker --task_index=0

python helloworld-1.py \
  --ps_hosts=localhost:2222,localhost:2223 \
  --worker_hosts=localhost:2224,localhost:2225 \
  --job_name=worker --task_index=1

From:
  http://henning.kropponline.de/2017/03/19/distributing-tensorflow/

Between-Graph, Asynchronous training.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

from tensorflow.examples.tutorials.mnist import input_data

import tensorflow as tf

FLAGS = None


def main(_):
  ps_hosts = FLAGS.ps_hosts.split(",")
  worker_hosts = FLAGS.worker_hosts.split(",")

  cluster = tf.train.ClusterSpec({
    "ps": ps_hosts,
    "worker": worker_hosts})

  server = tf.train.Server(
    cluster,
    job_name=FLAGS.job_name,
    task_index=FLAGS.task_index)

  if FLAGS.job_name == "ps":
    server.join()
  elif FLAGS.job_name == "worker":
    with tf.device(tf.train.replica_device_setter(
        worker_device="/job:worker/task:%d" % FLAGS.task_index,
        cluster=cluster)):
      global_step = tf.contrib.framework.get_or_create_global_step()

      with tf.name_scope("input"):
        mnist = input_data.read_data_sets("./input_data", one_hot=True)
        x = tf.placeholder(tf.float32, [None, 784], name="x-input")
        y_ = tf.placeholder(tf.float32, [None, 10], name="y-input")

      tf.set_random_seed(1)
      with tf.name_scope("weights"):
        W = tf.Variable(tf.zeros([784, 10]))
        b = tf.Variable(tf.zeros([10]))

      with tf.name_scope("model"):
        y = tf.matmul(x, W) + b

      with tf.name_scope("cross_entropy"):
        cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y))

      with tf.name_scope("train"):
        train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)

      with tf.name_scope("acc"):
        init_op = tf.initialize_all_variables()
        correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    sv = tf.train.Supervisor(is_chief=(FLAGS.task_index == 0),
                             global_step=global_step,
                             init_op=init_op)

    with sv.prepare_or_wait_for_session(server.target) as sess:
      for _ in range(100):
        batch_xs, batch_ys = mnist.train.next_batch(100)
        sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys})

      print(sess.run(accuracy, feed_dict={x: mnist.test.images, y_: mnist.test.labels}))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.register("type", "bool", lambda v: v.lower() == "true")
  # Flags for defining the tf.train.ClusterSpec
  parser.add_argument(
      "--ps_hosts",
      type=str,
      default="",
      help="Comma-separated list of hostname:port pairs"
  )
  parser.add_argument(
      "--worker_hosts",
      type=str,
      default="",
      help="Comma-separated list of hostname:port pairs"
  )
  parser.add_argument(
      "--job_name",
      type=str,
      default="",
      help="One of 'ps', 'worker'"
  )
  # Flags for defining the tf.train.Server
  parser.add_argument(
      "--task_index",
      type=int,
      default=0,
      help="Index of task within the job"
  )
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
