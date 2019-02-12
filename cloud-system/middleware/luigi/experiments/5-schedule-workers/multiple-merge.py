# Run command:
#   $ luigid
#   $ python multiple.py examples.X
#   $ python multiple-merge.py examples.Y
#
# This will run tasks 'X' and 'Y' in two workers using central scheduler. Since
# 'Bar' is the same for 'X' and 'Y', only 10 tasks will run instead of 20, i.e.
# execution is merged.
#
# Note that there is a race here that one of 'X' and 'Y' will leave unfinished
# because whoever finishes its tasks and is waiting the other task to finish the
# last 'Bar' will exit. For example, if there is only one 'Bar' task left (thus
# 'X' and 'Y' are not run yet), and now 'Y' picks up the last 'Bar', since there
# is no task left for X worker, it will exit (it can't run 'X" because the last
# 'Bar' taks is not finished yet), leaving task 'X' unfinshed. To fix this, we
# need to use '--worker-keep-alive'.
#   $ # stop luigid
#   $ luigid
#   $ rm -rf /tmp/bar
#   $ python multiple.py --worker-keep-alive examples.X
#   $ python multiple-merge.py --worker-keep-alive examples.Y
#
# keep_alive
#   If true, workers will stay alive when they run out of jobs to run, as long
#   as they have some pending job waiting to be run. Defaults to false.

import time
import luigi


class Y(luigi.WrapperTask):
  task_namespace = 'examples'
  def run(self):
    print("Running X")
  def requires(self):
    for i in range(10):
      yield Bar(i)


class Bar(luigi.Task):
  task_namespace = 'examples'
  num = luigi.IntParameter()
  def run(self):
    print("Bar %s" % self.num)
    time.sleep(10)
    self.output().open('w').close()
    print("Bar touched %s" % self.output())
  def output(self):
    return luigi.LocalTarget('/tmp/bar/%d' % self.num)


if __name__ == '__main__':
  luigi.run()
