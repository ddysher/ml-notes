import tensorflow as tf

# Cluster specification.
cluster_spec = tf.train.ClusterSpec({
  "ps": [
    "127.0.0.1:2221",  # /job:ps/task:0
    "127.0.0.1:2222",  # /job:ps/task:1
  ]})

server = tf.train.Server(cluster_spec, job_name="ps", task_index=0)
server.join()
