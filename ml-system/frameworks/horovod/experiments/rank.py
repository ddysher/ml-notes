import tensorflow as tf
import horovod.tensorflow as hvd

hvd.init()

print("local rank and size (for all processes running in a node)")
print(hvd.local_rank())
print(hvd.local_size())

print("global rank and size (for all processes)")
print(hvd.rank())
print(hvd.size())
