<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Design](#design)
- [Usage](#usage)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Papermill is a tool for parameterizing, executing, and analyzing Jupyter Notebooks, i.e.
- parameterize notebooks
- execute and collect metrics across the notebooks
- summarize collections of notebooks

# Design

To run a notebook locally using papermil, run:

```
$ papermill sleep.ipynb output.ipynb -p tick 2
```

Papermill cli accepts an input, output and parameters. It reads input notebook, expands it with
given parameters, and execute the notebook with specific engine (e.g. nbconvert).

Parameters are marked with the `per-cell toolbar` feature in jupyter notebook. Papermill looks for
cells marked with `parameters` tag and treats those values as defaults for the parameters passed in
at execution time. It achieves this by inserting a cell after the tagged cell. If no cell is tagged
with parameters a cell will be inserted to the front of the notebook.

Papermill saves the notebook as a new output notebook. The output notebook contains output while the
input notebook is not touched. Executing notebook with papermill will launch an ipython kernel, and
papermill will send cells to the kernel for execution:

```python
nb = nb_man.nb
for index, cell in enumerate(nb.cells):
    try:
        nb_man.cell_start(cell, index)
        if not cell.source:
            continue
        # preprocess and run the cell
        nb.cells[index], resources = self.preprocess_cell(cell, resources, index)
    except CellExecutionError as ex:
        nb_man.cell_exception(nb.cells[index], cell_index=index, exception=ex)
        break
    finally:
        nb_man.cell_complete(nb.cells[index], cell_index=index)
return nb, resources
```

Following is the processes when running the above command:

```shell
$ ps aux | grep python
deyuandeng       11169   0.0  0.5  4308696  44968   ??  Ss    5:32PM   0:00.50 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/python3.6 -m ipykernel_launcher -f /var/folders/0p/fd12kx9s1rb4fcv2x6bwhd8c0000gn/T/tmpwzsks5yd.json
deyuandeng       11149   0.0  0.8  4316284  65676 s002  S+    5:32PM   0:01.37 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/python3.6 /Users/deyuandeng/.pyenv/versions/3.6.7/bin/papermill sleep.ipynb output.ipynb
```

Note for nbconvert engine, the ipython kernel is launched via nbconvert: nbconvert itself can
execute notebook by launching kernel, e.g.

```shell
$ jupyter nbconvert --execute sleep.ipynb --to notebook
```

# Usage

Papermill can be used as cli or library, i.e.

```
$ papermill local/input.ipynb s3://bkt/output.ipynb -p alpha 0.6 -p l1_ratio 0.1
```

Or

```python
import papermill as pm

pm.execute_notebook(
   'path/to/input.ipynb',
   'path/to/output.ipynb',
   parameters = dict(alpha=0.6, ratio=0.1)
)
```
