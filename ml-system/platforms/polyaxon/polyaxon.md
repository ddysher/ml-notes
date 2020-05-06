<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [Concepts](#concepts)
  - [Architecture](#architecture)
- [Experiments (02/23/2020, v0.6)](#experiments-02232020-v06)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Run Experiments](#run-experiments)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 02/23/2020, v0.6*

## Introduction

Polyaxon is a platform for managing the whole lifecycle of large scale deep learning and machine
learning applications. The goal is to make it faster, easier, and more efficient to develop machine
learning and deep learning applications. Essentially, Polyaxon is an experiment tracking platform,
with an [opinioned API](https://docs.polyaxon.com/references/polyaxon-tracking-api/).

At its core, Polyaxon provides:
- Code Version: Git information used for the run.
- Run time: Start and end time of the run.
- Environment: Name of the file to launch the run, the command, arguments, python packages, ...
- Parameters: Key-value parameters used or this run.
- Metrics: Key-value metrics where the value is numeric. Each metric can be updated throughout the course of the run (for example, to track how your model’s loss function is converging), and MLflow records and lets you visualize the metric’s full history.
- Outputs/Artifacts: Output files in any format. For example, you can record images, audio, models (e.g., a pickled scikit-learn model), or even data files (e.g. a Parquet file) as artifacts.

## Concepts

Following is a list of core concepts and design decisions of polyaxon.

**Project**

A `Project` in polyaxon is very similar to a project in GitHub, it aims at organizing your efforts
to solve a specific problem. A project consist of a name and a description, the code to execute,
the data, and a polyaxonfile.yml.

A project can only associate with a sinlge repository.

**Experiment**

An `Experiment` is the execution of your model with data and the provided parameters on the cluster.

An `Experiment Job` is the Kubernetes pod running on the cluster for a specific experiment; in an
other word, job is the running component of an experiment. An experiment has at least one job. If
the experiment is running in a distributed way then it will have more than one job.

**Experiment Group**

`Experiment Group` is a group of experiments, useful for selection and hyperparameter optimization.
- selection means grouping interested experiments to compare metrics, visualize their differences, etc
- each run of hyperparameter optimization will create an experiment group, with each trial being an experiment

**Job**

A `Job` is the execution of your code to do some data processing or any generic operation. Note that
`Job` is different from `Experiment Job`: `Job` is an independent concept, and can be used to run
tasks unrelated to a certain experiment.

**Build**

A `Build` is the process of creating containers, polyaxon provides different backends for creating
containers, and try not to expose container image to end user.

**Checkpointing**

Polyaxon provides toolings to checkpoint, resume and restart experiments, specifically, Polyaxon
contains client APIs like `get_outputs_path`, `get_data_path` that return path to save model
artifacts, etc. Developer needs to use standard approach in deep learning frameworks in order to
leverage the feature.

**Others**

- User
- Team & Organization
- Jupyter Notebook
- TensorBoard

## Architecture

Polyaxon relies on several components to function smoothly:
- Postgres database
- Redis
- RabbitMQ
- Docker registries
- Storage for data/outputs/logs

**Pods Created from Polyaxon**

```
polyaxon-docker-registry-7d479b4766-87742     1/1    Running  0         2m56s
polyaxon-polyaxon-api-65dcbf9668-xn4rj        0/2    Running  0         2m56s
polyaxon-polyaxon-beat-9c7c69c86-v45rm        2/2    Running  0         2m56s
polyaxon-polyaxon-events-847745c9bb-k2skb     1/1    Running  0         2m56s
polyaxon-polyaxon-hpsearch-6d959696b5-lr5kj   1/1    Running  0         2m56s
polyaxon-polyaxon-k8s-events-d58c6bb6-vzpcl   1/1    Running  0         2m56s
polyaxon-polyaxon-monitors-55459b84c6-xmxjn   1/1    Running  0         2m56s
polyaxon-polyaxon-scheduler-668b7d575d-qjg9w  1/1    Running  0         2m56s
polyaxon-postgresql-7696d44c45-mjjhw          1/1    Running  0         2m56s
polyaxon-rabbitmq-ha-0                        1/1    Running  0         2m56s
polyaxon-redis-master-0                       1/1    Running  0         2m56s
polyaxon-redis-slave-0                        1/1    Running  0         2m56s
polyaxon-redis-slave-1                        1/1    Running  0         2m39s
```

Polyaxon relies on Kubernetes for:
- Managing the resources of your cluster (Memory, CPU, and GPU)
- Creating easy, repeatable, portable deployments
- Scaling up and down as needed

Polyaxon does the heavy lifting of:
- Scheduling the jobs
- Versioning the code
- Creating docker images
- Monitoring the statuses and resources
- Tracking params, logs, configurations, and tags
- Reporting metrics and outputs and other results to the user

# Experiments (02/23/2020, v0.6)

## Installation

```
# Create a namespace
$ kubectl create namespace polyaxon

# Add Polyaxon charts repo
$ helm repo add polyaxon https://charts.polyaxon.com
$ helm repo update

# Check configuration
$ polyaxon admin deploy -f config.yml --check
kubectl is installed
helm is installed
Polyaxon deployment file is valid.

# Option1: Deploy Polyaxon via CLI
$ polyaxon admin deploy -f config.yml

# Option2: Deploy Polyaxon via Helm
$ helm install polyaxon/polyaxon \
    --name=polyaxon \
    --namespace=polyaxon \
    -f config.yaml
```

## [Configuration](https://docs.polyaxon.com/configuration/introduction/)

```
# Get the application URL by running these commands:
$ export POLYAXON_PORT=$(kubectl get --namespace polyaxon -o jsonpath="{.spec.ports[0].nodePort}" services polyaxon-polyaxon-api)
$ export POLYAXON_IP=$(kubectl get nodes --namespace polyaxon -o jsonpath="{.items[0].status.addresses[1].address}")
$ echo http://$POLYAXON_IP:$POLYAXON_PORT

# Setup your cli by running theses commands:
$ polyaxon config set --host=$POLYAXON_IP --port=$POLYAXON_PORT
Config was updated.

# Log in with superuser
$ kubectl get secret --namespace polyaxon polyaxon-polyaxon-secret -o jsonpath="{.data.POLYAXON_ADMIN_PASSWORD}" | base64 --decode
$ polyaxon login --username=root --password=rootpassword
Login successful

$ polyaxon whoami
Username: root, Email: root@polyaxon.local
```

A list of all resources created from Polyaxon, note a `sync-db` Job is deleted after installation.

<details><summary>Resources created</summary><p>

```
$ helm status polyaxon
LAST DEPLOYED: Thu Jan 23 14:10:09 2020
NAMESPACE: polyaxon
STATUS: DEPLOYED

RESOURCES:
==> v1/ConfigMap
NAME                             DATA  AGE
polyaxon-docker-registry-config  1     2m57s
polyaxon-polyaxon-config         82    2m57s
polyaxon-rabbitmq-ha             2     2m57s
polyaxon-redis                   3     2m57s
polyaxon-redis-health            6     2m57s

==> v1/Deployment
NAME                          READY  UP-TO-DATE  AVAILABLE  AGE
polyaxon-docker-registry      1/1    1           1          2m56s
polyaxon-polyaxon-api         0/1    1           0          2m56s
polyaxon-polyaxon-beat        1/1    1           1          2m56s
polyaxon-polyaxon-events      1/1    1           1          2m56s
polyaxon-polyaxon-hpsearch    1/1    1           1          2m56s
polyaxon-polyaxon-k8s-events  1/1    1           1          2m56s
polyaxon-polyaxon-monitors    1/1    1           1          2m56s
polyaxon-polyaxon-scheduler   1/1    1           1          2m56s

==> v1/Pod(related)
NAME                                          READY  STATUS   RESTARTS  AGE
polyaxon-docker-registry-7d479b4766-87742     1/1    Running  0         2m56s
polyaxon-polyaxon-api-65dcbf9668-xn4rj        0/2    Running  0         2m56s
polyaxon-polyaxon-beat-9c7c69c86-v45rm        2/2    Running  0         2m56s
polyaxon-polyaxon-events-847745c9bb-k2skb     1/1    Running  0         2m56s
polyaxon-polyaxon-hpsearch-6d959696b5-lr5kj   1/1    Running  0         2m56s
polyaxon-polyaxon-k8s-events-d58c6bb6-vzpcl   1/1    Running  0         2m56s
polyaxon-polyaxon-monitors-55459b84c6-xmxjn   1/1    Running  0         2m56s
polyaxon-polyaxon-scheduler-668b7d575d-qjg9w  1/1    Running  0         2m56s
polyaxon-postgresql-7696d44c45-mjjhw          1/1    Running  0         2m56s
polyaxon-rabbitmq-ha-0                        1/1    Running  0         2m56s
polyaxon-redis-master-0                       1/1    Running  0         2m56s
polyaxon-redis-slave-0                        1/1    Running  0         2m56s
polyaxon-redis-slave-1                        1/1    Running  0         2m39s

==> v1/Role
NAME                  AGE
polyaxon-rabbitmq-ha  2m56s

==> v1/RoleBinding
NAME                  AGE
polyaxon-rabbitmq-ha  2m56s

==> v1/Secret
NAME                             TYPE    DATA  AGE
polyaxon-docker-registry-secret  Opaque  1     2m57s
polyaxon-polyaxon-secret         Opaque  4     2m57s
polyaxon-postgresql              Opaque  1     2m57s
polyaxon-rabbitmq-ha             Opaque  6     2m57s

==> v1/Service
NAME                            TYPE       CLUSTER-IP  EXTERNAL-IP  PORT(S)                      AGE
polyaxon-docker-registry        NodePort   10.0.0.29   <none>       5000:31813/TCP               2m56s
polyaxon-polyaxon-api           NodePort   10.0.0.88   <none>       80:31811/TCP                 2m56s
polyaxon-postgresql             ClusterIP  10.0.0.105  <none>       5432/TCP                     2m56s
polyaxon-rabbitmq-ha            ClusterIP  10.0.0.98   <none>       15672/TCP,5672/TCP,4369/TCP  2m56s
polyaxon-rabbitmq-ha-discovery  ClusterIP  None        <none>       15672/TCP,5672/TCP,4369/TCP  2m56s
polyaxon-redis-headless         ClusterIP  None        <none>       6379/TCP                     2m56s
polyaxon-redis-master           ClusterIP  10.0.0.51   <none>       6379/TCP                     2m56s
polyaxon-redis-slave            ClusterIP  10.0.0.195  <none>       6379/TCP                     2m56s

==> v1/ServiceAccount
NAME                                      SECRETS  AGE
polyaxon-polyaxon-serviceaccount          1        2m56s
polyaxon-polyaxon-workers-serviceaccount  1        2m57s
polyaxon-rabbitmq-ha                      1        2m57s

==> v1/StatefulSet
NAME                   READY  AGE
polyaxon-rabbitmq-ha   1/1    2m56s
polyaxon-redis-master  1/1    2m56s
polyaxon-redis-slave   2/2    2m56s

==> v1beta1/Deployment
NAME                 READY  UP-TO-DATE  AVAILABLE  AGE
polyaxon-postgresql  1/1    1           1          2m56s


NOTES:
Polyaxon is currently running:


1. Get the application URL by running these commands:

  export POLYAXON_PORT=$(kubectl get --namespace polyaxon -o jsonpath="{.spec.ports[0].nodePort}" services polyaxon-polyaxon-api)

  export POLYAXON_IP=$(kubectl get nodes --namespace polyaxon -o jsonpath="{.items[0].status.addresses[1].address}")

  echo http://$POLYAXON_IP:$POLYAXON_PORT

2. Setup your cli by running theses commands:
  polyaxon config set --host=$POLYAXON_IP --port=$POLYAXON_PORT

3. Log in with superuser

  USER: root
  PASSWORD: Get login password with

    kubectl get secret --namespace polyaxon polyaxon-polyaxon-secret -o jsonpath="{.data.POLYAXON_ADMIN_PASSWORD}" | base64 --decode
```

</p></details></br>

```
$ polyaxon project create --name=quick-start --description='Polyaxon quick start.'
```

## [Run Experiments](https://docs.polyaxon.com/concepts/quick-start-internal-repo/)

Behind the scene:
- You uploaded your code, and created a git commit for this version of your code
- You built a docker image with the latest version of your code
- You ran the image with the specified command in the polyaxonfile
- You persisted your logs and outputs to your volume claims
- You created a group of experiments to fine tune hyperparameters
