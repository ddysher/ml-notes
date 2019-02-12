# This is a pretty naive way of handling multiple input/ouput for task
# dependencies. For details, see http://bionics.it/posts/luigi-tutorial.
#   $ python naive.py --local-scheduler TaskC

import luigi

class TaskA(luigi.Task):
  def requires(self):
    return None
  def output(self):
    return {'output1' : luigi.LocalTarget('task_a_out1'),
            'output2' : luigi.LocalTarget('task_a_out2')}
  def run(self):
    with self.output()['output1'].open('w') as outfile:
      outfile.write('foo\n')
    with self.output()['output2'].open('w') as outfile:
      outfile.write('foo\n')

class TaskB(luigi.Task):
  def requires(self):
    return None
  def output(self):
    return {'output1' : luigi.LocalTarget('task_b_out1'),
            'output2' : luigi.LocalTarget('task_b_out2')}
  def run(self):
    with self.output()['output1'].open('w') as outfile:
      outfile.write('bar\n')
    with self.output()['output2'].open('w') as outfile:
      outfile.write('bar\n')


class TaskC(luigi.Task):
  def requires(self):
    return {'input_a' : TaskA(),
            'input_b' : TaskB()}
  def output(self):
    return luigi.LocalTarget(self.input()['input_a']['output1'].path + '.task_c')
  def run(self):
    with self.input()['input_a']['output1'].open() as infile_a1: # Notice how we need to know the name of TaskA's output
      with self.input()['input_a']['output2'].open() as infile_a2: # ... and same here ...
        with self.input()['input_b']['output1'].open() as infile_b1: # Notice how we need to know the name of TaskB's output
          with self.input()['input_b']['output2'].open() as infile_b2: # ... and same here ...
            with self.output().open('w') as outfile:
              for line in infile_a1:
                outfile.write(line)
              for line in infile_a2:
                outfile.write(line)
              for line in infile_b1:
                outfile.write(line)
              for line in infile_b2:
                outfile.write(line)


if __name__ == '__main__':
  luigi.run()
