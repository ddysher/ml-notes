import tensorflow as tf
import sys
x = tf.Variable(0.0, name="x")
increment_x = tf.assign(x, x + 1)

with tf.Session(sys.argv[1]) as sess:
  if sys.argv[2:]==["init"]:
    sess.run(x.initializer)
  sess.run(increment_x)
  print(x.eval())
