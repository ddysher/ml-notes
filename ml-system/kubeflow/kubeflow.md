<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiment](#experiment)
  - [Initialize workspace](#initialize-workspace)
  - [Run kubeflow core](#run-kubeflow-core)
  - [Run model training/serving](#run-model-trainingserving)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

The Kubeflow project is dedicated to making deployment of machine learning on Kubernetes simple,
portable and scalable.

# Experiment

Date: 03/27/2018, v0.0.0

## Initialize workspace

The following commands initialize a kubeflow workspace:


```sh
ks init kubeflow-101
# Install the Kubeflow packages into your application.

cd kubeflow-101
ks registry add kubeflow github.com/kubeflow/kubeflow/tree/master/kubeflow
ks pkg install kubeflow/core
ks pkg install kubeflow/tf-serving
ks pkg install kubeflow/tf-job
```

Running `ks pkg install` will download artifacts from kubeflow registry to "vendor/" directory.
All side effects are saved in "app.yaml" directory.

## Run kubeflow core

Kubeflow core components are "ambassador", "tf-hub (jupyterhub)" and "tf-job-operator".

Now Run the following command to generate core components:

```sh
ks generate core kubeflow-core --name=kubeflow-core
```

Then create environment and deploy core components:

```
# Setting up environment.
KF_ENV=nocloud
NAMESPACE=kubeflow
ks env add ${KF_ENV}
ks env set ${KF_ENV} --namespace ${NAMESPACE}
kubectl create namespace ${NAMESPACE}

# Create resources.
ks apply ${KF_ENV} -c kubeflow-core
```

## Run model training/serving

Follow the [reference link](https://github.com/kubeflow/kubeflow/blob/886efff64c552fd33d6ed43263ee6d4f15490d48/user_guide.md)
for model training/serving. Note that training and serving are ksonnet component of an application.
