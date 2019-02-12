# Install tensorflow and tensorboard_logger using pip, then run:
#  $ python tb_log.py
#
# Once finished, run tensorboard:
#  $ tensorboard --logdir `pwd`/runs

from tensorboard_logger import configure, log_value

# configure creates a logger instance
configure("runs/run-1234")

for step in range(1000):
  v1, v2 = 0.1, 0.2
  # log_value creates a summary pb, then an event pb and save it to disk.
  # summary pb is part of event pb.
  log_value('v1', v1, step)
  log_value('v2', v2, step)
