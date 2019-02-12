<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
  - [Tracking](#tracking)
  - [Projects](#projects)
  - [Models](#models)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[MLflow](https://mlflow.org/docs/latest/index.html) provides a set of libraries and APIs for working
with machine learning problems. It is designed to put as few constraints as possible on user's
workflow, and supports any machine learning library.

# Components

MLflow is organized into three components: Tracking, Projects, and Models. These components are not
running processes, but rather library and API. User can use each of these components on their own,
but they are also designed to work well together.

## Tracking

MLflow Tracking is an API and UI for logging parameters, code versions, metrics, and output files
when running your machine learning code and for later visualizing the results. You can use MLflow
Tracking in any environment (for example, a standalone script or a notebook) to log results to
local files or to a server, then compare multiple runs. Teams can also use it to compare results
from different users.

Following commands are run under `experiments/tracking`.

**Run model with mlflow tracking API**

```
python model.py
```

The output looks like:

```
$ tree
.
├── mlruns
│   └── 0
│       ├── f574eb32b08e4521bdcbe63dd8691bc5
│       │   ├── artifacts
│       │   │   └── test.txt
│       │   ├── meta.yaml
│       │   ├── metrics
│       │   │   └── foo
│       │   └── params
│       │       └── param1
│       └── meta.yaml
├── model.py
├── outputs
│   └── test.txt
└── README.md
```

Another run of the command will create a new ID directory under `mlruns/0`. Here, `0` is experiment
ID, which is used to group each run of our model.

**Experiment**

To create a new experiment, we can use mlflow API `mlflow.create_experiment()`, or use command line:

```
mlflow experiments create newexp
```

Then a new experiment with name `newexp` and ID `1` wll be created. To run under a specific
experiment, we can use:

```
# Set the ID via environment variables
export MLFLOW_EXPERIMENT_ID=1
python model.py
```

To view tracking, use:

```
mlflow ui
```

**Remote tracking**

By default, mlflow saves files in local directory (mlruns), we can create remote server to serve
all tasks:

```
$ mlflow server \
    --file-store /tmp/mlflow-file \
    --host 0.0.0.0
```

Now if we run `python model.py`, we'll see that our files are saved in `/tmp/mlflow-file`.

## Projects

MLflow Projects are a standard format for packaging reusable data science code. Each project is
simply a directory with code or a Git repository, and uses a descriptor file or simply convention
to specify its dependencies and how to run the code. For example, projects can contain a `conda.yaml`
file for specifying a Python Conda environment. You can also describe your project in more detail
by adding a `MLproject` file, which is a YAML formatted text file.

When you use the MLflow Tracking API in a Project, MLflow automatically remembers the project
version executed (for example, Git commit) and any parameters. You can easily run existing MLflow
Projects from GitHub or your own Git repository, and chain them into multi-step workflows.

Following commands are run under `experiments/projects`.

```
$ mlflow run . -P alpha=0.5
```

## Models

MLflow Models offer a convention for packaging machine learning models in multiple flavors, and a
variety of tools to help you deploy them. Each Model is saved as a directory containing arbitrary
files and a descriptor file `MLModel` that lists several `flavors` the model can be used in. For
example, a TensorFlow model can be loaded as a TensorFlow DAG, or as a Python function to apply to
input data.

MLflow provides tools to deploy many common model types to diverse platforms: for example, any model
supporting the `Python function` flavor can be deployed to a Docker-based REST server, to cloud
platforms such as Azure ML and AWS SageMaker, and as a user-defined function in Apache Spark for
batch and streaming inference. If you output MLflow Models using the Tracking API, MLflow will also
automatically remember which Project and run they came from.

Flavors are the core concept that makes mlflow powerful. For example, we can train a model locally
which has flavor `python_function`, then we can use any deployment approach that support
`python_function` flavor, e.g. AzureML.

In python client, for each framework and library, two methods are implemented: `log_model` and
`load_model`. For example, sklearn.py implements the two APIs via pickle.dump() and pickle.load().

Following commands are run under `experiments/models`.

**Create a sklearn model**

Run the command to create a sklearn model:

```
python sklearn_model.py
```

We'll find a pickled scikit-learn model:

```
$ tree
.
├── mlruns
│   └── 0
│       ├── 2614619d34454cdb8a8b3da271df6862
│       │   ├── artifacts
│       │   │   └── model
│       │   │       ├── MLmodel
│       │   │       └── model.pkl
│       │   ├── meta.yaml
│       │   ├── metrics
│       │   │   └── score
│       │   └── params
│       └── meta.yaml
├── README.md
└── sklearn_model.py

7 directories, 7 files
```

View the model using mlflow UI:

```
mlflow ui
```

**Serving model using mlflow command**

Serve the model:

```
# -r <RUN_ID>
$ mlflow sklearn serve -r 2614619d34454cdb8a8b3da271df6862 model
```

Curl prediction endpoint:

```
$ curl -d '[{"x": 1}, {"x": -1}]' -H 'Content-Type: application/json' -X POST localhost:5000/invocations
{"predictions": [1, 0]}
```
