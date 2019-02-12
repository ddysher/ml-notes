# To run:
#   python luigitutorial.py --local-scheduler HelloWorld

import luigi

# Targets are some sort of data that is persisted between task runs. In this
# tutorial we will only work with luigi.LocalTarget()'s, which are normal files.
# Tasks are defined as python classes that subclass the luigi.Task super class.
# Each task has methods that the workflow designer is supposed to implement.

class HelloWorld(luigi.Task):

  # requires should return one or more instantiated tasks that current task
  # depends on.
  def requires(self):
    return None

  # output returns one or more target objects that current task will produce
  # after run. This is typically files.
  def output(self):
    return luigi.LocalTarget('helloworld.txt')

  # run contains all the code that the task will run.
  def run(self):
    with self.output().open('w') as outfile:
      outfile.write('Hello World!\n')


if __name__ == '__main__':
    luigi.run()
