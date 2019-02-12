# Papermill

Papermill is a tool for parameterizing, executing, and analyzing Jupyter Notebooks.

Papermill lets you:
- parameterize notebooks
- execute and collect metrics across the notebooks
- summarize collections of notebooks

**Implementation**

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

To run locally:

```
$ papermill sleep.ipynb output.ipynb
```

Papermill accepts an input, output and parameters. It reads input notebook, expands it with given
parameters, and execute the notebook with specific engine (e.g. nbconvert). Executing notebook will
launch an ipython kernel Once ran, it saves the notebook as a new output notebook. The output
notebook contains output while the input notebook is not touched.
