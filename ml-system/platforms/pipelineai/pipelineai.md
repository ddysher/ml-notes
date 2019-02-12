<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Workflow](#workflow)
- [Features](#features)
- [Experiments](#experiments)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 07/07/2018, v1.5*

Pipeline AI streamlines machine learning pipeline. The core of PipelineAI is its command line, IMO.

# Workflow

Based on getting started guide, `pipeline cli` is the entrypoint; however, cli is not available
under github, we can instead find it at [pip package site](https://pypi.org/project/cli-pipeline/).

Pipeline workflow is simple, it has a few jinja templates to be replaced by commandline arguments.
For example, running command:
```
pipeline predict-server-build --model-name=mnist --model-tag=v3a --model-type=tensorflow --model-path=./tensorflow/mnist-v3/model
```

will call `predict_server_build` method which replace placeholders in template file `predict-server-local-dockerfile.template`.

# Features

Following is a list of features from pipelineai:

- Consistent, Immutable, Reproducible Model Runtimes
- Sample Machine Learning and AI Models
- Supported Model Runtimes (CPU and GPU)
- Supported Streaming Engines
- Drag N' Drop Model Deploy
- Generate Optimize Model Versions Upon Upload
- Distributed Model Training and Hyper-Parameter Tuning
- Continuously Deploy Models to Clusters of PipelineAI Servers
- View Real-Time Prediction Stream
- Compare Both Offline (Batch) and Real-Time Model Performance
- Compare Response Time, Throughput, and Cost-Per-Prediction
- Shift Live Traffic to Maximize Revenue and Minimize Cost
- Continuously Fix Borderline Predictions through Crowd Sourcing

# Experiments

https://github.com/PipelineAI/pipeline/tree/r1.5/docs/quickstart/kubernetes
