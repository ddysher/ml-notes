# Run command:
#   $ python multiple.py --local-scheduler examples.X
#
# Another run will quit immediately since files already exist.
#   $ python multiple.py --local-scheduler examples.X
#
# The above command will run only one worker (single PID), to run with multiple
# works, use:
#   $ rm -rf /tmp/bar
#   $ python multiple.py --local-scheduler --workers 6 examples.X
#
# The above commands use local scheduler; in production, it is necessary to use
# central scheduler:
#   $ rm -rf /tmp/bar
#   $ luigid
# In another terminal:
#   $ python multiple.py --workers 6 examples.X

import time
import luigi


class X(luigi.WrapperTask):
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
