"""
Benchmark distributed tensorflow (vs local tensorflow) by adding vector
of ones on worker2 to variable on worker1 as fast as possible.

On 2014 macbook, TensorFlow 0.10 this shows
Local rate:       2175.28 MB per second
Distributed rate: 107.13 MB per second

On i7-6700, 16G desktop, TensorFlow 1.4.0 this shows
Local rate:       2140.96 MB per second
Distributed rate: 509.21 MB per second

Copy/Paste with modification from:
 https://stackoverflow.com/questions/41067398/task-assignment-in-tensorflow-distributed-process
 https://gist.github.com/yaroslavvb/1124bb02a9fd4abce3d86caf2f950cb2
"""

import subprocess
import sys
import time

import tensorflow as tf

flags = tf.flags
flags.DEFINE_integer("iters", 10, "Maximum number of additions")
flags.DEFINE_integer("data_mb", 100, "size of vector in MBs")
flags.DEFINE_string("port1", "30100", "port of worker1")
flags.DEFINE_string("port2", "30101", "port of worker2")
flags.DEFINE_string("task", "", "internal use")
FLAGS = flags.FLAGS

# Setup local cluster from flags.
host = "127.0.0.1:"

# Note that there's no ps server. In tensorflow, there's no built-in distinction
# between worker and ps devices -- it's just a convention that variables get
# assigned to ps devices, and ops are assigned to worker devices.
cluster = {"worker": [host+FLAGS.port1, host+FLAGS.port2]}
clusterspec = tf.train.ClusterSpec(cluster).as_cluster_def()


def default_config():
  """Create default config for running session."""
  optimizer_options = tf.OptimizerOptions(opt_level=tf.OptimizerOptions.L0)
  config = tf.ConfigProto(
    graph_options=tf.GraphOptions(optimizer_options=optimizer_options))
  config.log_device_placement = False
  config.allow_soft_placement = False
  return config


def create_graph(device1, device2):
  """Create a tensorflow graph.

  Create graph that keeps variable (params) on device1, while vector of ones
  and addition op on device2.
  """
  tf.reset_default_graph()
  dtype = tf.int32
  params_size = 250*1000*FLAGS.data_mb # 1MB is 250k integers

  with tf.device(device1):
    params = tf.get_variable(
      "params", [params_size], dtype,
      initializer=tf.zeros_initializer)
  with tf.device(device2):
    # TODO: constant node gets placed on device1 because of simple_placer
    #    update = tf.constant(1, shape=[params_size], dtype=dtype)
    update = tf.get_variable(
      "update", [params_size], dtype,
      initializer=tf.ones_initializer)
    add_op = params.assign_add(update)

  init_op = tf.initialize_all_variables()
  return init_op, add_op


def run_benchmark(sess, init_op, add_op):
  """Returns MB/s rate of addition."""
  sess.run(init_op)
  sess.run(add_op.op)           # TODO: to warm-up operation
  start_time = time.time()
  for i in range(FLAGS.iters):
    # Change to add_op.op to make faster (TODO)
    sess.run(add_op)
  elapsed_time = time.time() - start_time
  return float(FLAGS.iters)*FLAGS.data_mb/elapsed_time


def run_benchmark_local():
  """Run local benchmark.

  Client (*this* python process) creates a graph and connects to an in-process
  engine to run operations.
  """
  ops = create_graph(None, None)
  sess = tf.Session(config=default_config())
  return run_benchmark(sess, *ops)


def run_benchmark_distributed():
  """Run distributed benchmark.

  Client (*this* python process) creates a graph; part of the graph (params)
  locates at task:0 and part of the graph (add_op) locates at task:1. The client
  then creates a session and connects to one of the task to run operations. That
  task (here, task:0) will create Send/Recv ops to transfer data between task:0
  and task:1.
  """
  ops = create_graph("/job:worker/task:0", "/job:worker/task:1")

  # Below we launch two distributed services and have the client connects to
  # the first one to start ops.
  task0 = subprocess.Popen("python %s --task=0" % (sys.argv[0]), shell=True)
  task1 = subprocess.Popen("python %s --task=1" % (sys.argv[0]), shell=True)
  time.sleep(1)

  sess = tf.Session("grpc://"+host+FLAGS.port1, config=default_config())
  result = run_benchmark(sess, *ops)

  task0.kill()
  task1.kill()
  return result


if __name__=='__main__':
  if not FLAGS.task:
    rate1 = run_benchmark_local()
    rate2 = run_benchmark_distributed()

    print("Adding data in %d MB chunks" %(FLAGS.data_mb))
    print("Local rate:       %.2f MB per second" %(rate1,))
    print("Distributed rate: %.2f MB per second" %(rate2,))
  else:
    # Here we launch TensorFlow server (via `popen` in distributed case). The
    # process started here is both a worker and a master.
    server = tf.train.Server(
      clusterspec,
      config=default_config(),
      job_name="worker",
      task_index=int(FLAGS.task))
    server.join()
