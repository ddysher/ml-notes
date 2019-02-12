'''
Distributed Tensorflow 1.2.0 example of using data parallelism and share model
parameters. Trains a simple sigmoid neural network on mnist for 20 epochs on
three machines using one parameter server.

Run like this (on different terminals), all tasks will use the same code.
 $ python helloworld-2.py --job_name="ps" --task_index=0
 $ python helloworld-2.py --job_name="worker" --task_index=0
 $ python helloworld-2.py --job_name="worker" --task_index=1
 $ python helloworld-2.py --job_name="worker" --task_index=2

Copy/Paste (with modification) from:
 https://github.com/ischlag/distributed-tensorflow-example/

Between-Graph, Asynchronous training.
'''

from __future__ import print_function

import tensorflow as tf
import sys
import time

# Cluster specification. The cluster contains one parameter server and three
# workers. All tasks accept the same cluster spec.
parameter_servers = ["localhost:2222"]
workers = ["localhost:2223", "localhost:2224", "localhost:2225"]
cluster = tf.train.ClusterSpec({
  "ps": parameter_servers,
  "worker": workers})

# Input flags, i.e. job name and task index in the job - A job contains multiple
# tasks.
tf.app.flags.DEFINE_string("job_name", "", "either 'ps' or 'worker'")
tf.app.flags.DEFINE_integer("task_index", 0, "index of task within the job")
FLAGS = tf.app.flags.FLAGS

# Start a server for a specific task, i.e. each task has a server which is used
# to communicate with other servers in the cluster.
# server in the cluster.
server = tf.train.Server(
  cluster,
  job_name=FLAGS.job_name,
  task_index=FLAGS.task_index)

# Config
batch_size = 100
learning_rate = 0.0005
training_epochs = 20
logs_path = "/tmp/mnist/1"

# load mnist data set
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets('MNIST_data', one_hot=True)

if FLAGS.job_name == "ps":
  # For ps server, blocks until the server has shut down.
  server.join()
elif FLAGS.job_name == "worker":
  # Refer to document of "replica_device_setter" on how it works. Basically,
  # operations defined below will be assigned to `worker_device`.
  with tf.device(tf.train.replica_device_setter(
      worker_device="/job:worker/task:%d" % FLAGS.task_index,
      cluster=cluster)):
    # Count the number of updates
    global_step = tf.get_variable(
      'global_step',
      [],
      initializer = tf.constant_initializer(0),
      trainable = False)

    # Input images
    with tf.name_scope('input'):
      # None -> batch size can be any size, 784 -> flattened mnist image
      x = tf.placeholder(tf.float32, shape=[None, 784], name="x-input")
      # Target 10 output classes
      y_ = tf.placeholder(tf.float32, shape=[None, 10], name="y-input")

    # Model parameters will change during training so we use tf.Variable
    tf.set_random_seed(1)
    with tf.name_scope("weights"):
      W1 = tf.Variable(tf.random_normal([784, 100]))
      W2 = tf.Variable(tf.random_normal([100, 10]))

    # Bias
    with tf.name_scope("biases"):
      b1 = tf.Variable(tf.zeros([100]))
      b2 = tf.Variable(tf.zeros([10]))

    # Implement model
    with tf.name_scope("softmax"):
      # y is our prediction
      z2 = tf.add(tf.matmul(x,W1),b1)
      a2 = tf.nn.sigmoid(z2)
      z3 = tf.add(tf.matmul(a2,W2),b2)
      y  = tf.nn.softmax(z3)

    # Specify cost function
    with tf.name_scope('cross_entropy'):
      # This is our cost
      cross_entropy = tf.reduce_mean(
        -tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))

    # Specify optimizer
    with tf.name_scope('train'):
      # Optimizer is an "operation" which we can execute in a session
      grad_op = tf.train.GradientDescentOptimizer(learning_rate)
      '''
      rep_op = tf.train.SyncReplicasOptimizer(
          grad_op,
          replicas_to_aggregate=len(workers),
          replica_id=FLAGS.task_index,
          total_num_replicas=len(workers),
          use_locking=True)
          train_op = rep_op.minimize(cross_entropy, global_step=global_step)
      '''
      train_op = grad_op.minimize(cross_entropy, global_step=global_step)

    '''
    init_token_op = rep_op.get_init_tokens_op()
    chief_queue_runner = rep_op.get_chief_queue_runner()
    '''

    with tf.name_scope('Accuracy'):
      # Accuracy
      correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
      accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

      # Create a summary for our cost and accuracy
      tf.summary.scalar("cost", cross_entropy)
      tf.summary.scalar("accuracy", accuracy)

      # Merge all summaries into a single "operation" which we can execute in a session
      summary_op = tf.summary.merge_all()
      init_op = tf.global_variables_initializer()
      print("Variables initialized ...")

  sv = tf.train.Supervisor(is_chief=(FLAGS.task_index == 0),
                           global_step=global_step,
                           init_op=init_op)

  begin_time = time.time()
  frequency = 100

  # Create a session on 'master', recovering or initializing the model as
  # needed, or wait for a session to be ready.
  with sv.prepare_or_wait_for_session(server.target) as sess:
    '''
    # is chief
    if FLAGS.task_index == 0:
    sv.start_queue_runners(sess, [chief_queue_runner])
    sess.run(init_token_op)
    '''
    # Create log writer object (this will log on every machine)
    writer = tf.summary.FileWriter(logs_path, graph=tf.get_default_graph())

    # Perform training cycles
    start_time = time.time()
    for epoch in range(training_epochs):
      # Number of batches in one epoch
      batch_count = int(mnist.train.num_examples/batch_size)
      count = 0
      for i in range(batch_count):
        batch_x, batch_y = mnist.train.next_batch(batch_size)
        # Perform the operations we defined earlier on batch
        _, cost, summary, step = sess.run(
          [train_op, cross_entropy, summary_op, global_step],
          feed_dict={x: batch_x, y_: batch_y})
        writer.add_summary(summary, step)

        count += 1
        if count % frequency == 0 or i+1 == batch_count:
          elapsed_time = time.time() - start_time
          start_time = time.time()
          print("Step: %d," % (step+1),
                " Epoch: %2d," % (epoch+1),
                " Batch: %3d of %3d," % (i+1, batch_count),
                " Cost: %.4f," % cost,
                " AvgTime: %3.2fms" % float(elapsed_time*1000/frequency))
          count = 0

    print("Test-Accuracy: %2.2f" % sess.run(accuracy, feed_dict={x: mnist.test.images, y_: mnist.test.labels}))
    print("Total Time: %3.2fs" % float(time.time() - begin_time))
    print("Final Cost: %.4f" % cost)

  sv.stop()
  print("done")
