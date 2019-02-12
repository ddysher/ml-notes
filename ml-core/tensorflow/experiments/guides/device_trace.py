#!/usr/bin/env python
#
# Supplement to programmers' Guide to using GPUs
#
# https://www.tensorflow.org/guide/using_gpu

'''
From following sources with modification:
  https://stackoverflow.com/questions/40061895/what-exactly-is-a-device-in-tensorflow
  https://gist.github.com/yaroslavvb/9a5f4a0b613c79152152b35c0bc840b8
'''

from __future__ import print_function

import os
import tensorflow as tf
from tensorflow.python.client import timeline

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

n = 1024
with tf.device("cpu:0"):
  a1 = tf.ones((n, n))
  a2 = tf.ones((n, n))
with tf.device("cpu:1"):
  a3 = tf.matmul(a1, a2)
with tf.device("cpu:2"):
  a4 = tf.matmul(a1, a2)
with tf.device("cpu:3"):
  a5 = tf.matmul(a3, a4)

# Turn off graph optimizations
no_opt = tf.OptimizerOptions(
  opt_level=tf.OptimizerOptions.L0,
  do_common_subexpression_elimination=False,
  do_function_inlining=False,
  do_constant_folding=False)
config = tf.ConfigProto(
  graph_options=tf.GraphOptions(optimizer_options=no_opt),
  log_device_placement=True, allow_soft_placement=False,
  device_count={"CPU": 8},
  inter_op_parallelism_threads=3,
  intra_op_parallelism_threads=1)
sess = tf.Session(config=config)

run_metadata = tf.RunMetadata()
run_options = tf.RunOptions(
  trace_level=tf.RunOptions.FULL_TRACE,
  output_partition_graphs=True)

# Run session.
sess.run(a5.op, options=run_options, run_metadata=run_metadata)

trace = timeline.Timeline(step_stats=run_metadata.step_stats)
with open('/tmp/timeline.json', 'w') as out:
  out.write(trace.generate_chrome_trace_format())

# Print the subgraphs that executed on each device.
print('--------------------------------')
print(run_metadata.partition_graphs)
print('--------------------------------')

# Print the timings of each operation that executed.
print(run_metadata.step_stats)

# Print all metadata
print(run_metadata)
