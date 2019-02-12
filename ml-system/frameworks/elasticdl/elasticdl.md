<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Workflow](#workflow)
  - [Fault-tolerate](#fault-tolerate)
  - [Model Building](#model-building)
  - [Embedding Service](#embedding-service)
- [Experiments](#experiments)
  - [Kubernetes cluster](#kubernetes-cluster)
  - [Client submission](#client-submission)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 09/13/2019*

ElasticDL is a Kubernetes-native deep learning framework built on top of TensorFlow 2.0 that
supports fault-tolerance and elastic scheduling. In the initial launch, ElasticDL only supports
PS-Worker distributed training, with plan to support other strategies. The PS-Worker architecture
doesn't depend on any native TensorFlow features; rather, it wraps TensorFlow single process
training and intecepts gradients report (worker) and average (master), similar to Horovod.

## Workflow

[Core workflow](https://github.com/sql-machine-learning/elasticdl/blob/7f4b3f9031ced2bb9656244ce394b95624ccb214/doc/design_diagram.pdf):
- User submits job via client
  - client builds docker image and push to registry, the docker image contains
    - elasticdl code
    - user defined code
  - client calls Kubernetes API to start master
- Master then
  - creates task queue, i.e. master shards all tasks and dispatch them to different workers
  - optionally creates tensorboard, checkpoint, embedding services
  - starts gRPC services to listen on worker requests
  - launches worker manager, which creates worker pods
- Workers call `GetTask` gRPC method from master to claim a training task, i.e. compute gradient on
  the assigned minibatch, and reports back gradients via `ReportGradient` gRPC method

The worker entrypoint is defined in elasticdl (not user code, which is loaded via python class).
Therefore, elasticdl has total control over reporting gradients.
- For sync sgd design, refer to [this link](https://github.com/sql-machine-learning/elasticdl/blob/7a849374ff7e650f0e89230f5cafdf3a174ce901/doc/elastic_sync_sgd.md)
- For async sgd design, refer to [this link](https://github.com/sql-machine-learning/elasticdl/blob/7a849374ff7e650f0e89230f5cafdf3a174ce901/doc/async_sgd_design.md)

## Fault-tolerate

If any worker fails, master will be notified via Kubernetes watch event. It will start a new worker
in place of the old worker. Since the master maintains the task queue and global model (parameters),
the new worker can easily join the training process by getting the global model, then claim a task
to start training.

If master fails, the whole training fails, and workers will be cleaned up by Kubernetes gc (worker
has ownerreference set to master).

## Model Building

The model building process is similar to Hadoop/Spark, that is, user writes core methods and the
system is responsible to submit it. The [link](https://github.com/sql-machine-learning/elasticdl/blob/7f4b3f9031ced2bb9656244ce394b95624ccb214/doc/model_building.md)
has more information on the interface.

## Embedding Service

The embedding service is actually a redis pod/service launched via master to share embedding vector
across workers.

# Experiments

## Kubernetes cluster

Run a local Kubernetes cluster (1.15):

```bash
ALLOW_PRIVILEGED=true ./hack/local-up-cluster.sh -O
```

Before launching elasticdl training job, we need to apply rbac rules since master service needs to
talk to Kubernetes API to update labels, create pods, etc.

```bash
# run under project root
kubectl apply -f elasticdl/manifests/examples/elasticdl-rbac.yaml
```

## Client submission

Now build all docker images, including `elasticdl:ci`, which contains small dataset.

```bash
./elasticdl/docker/build_all.sh
```

Install `kubernetes` and `docker` package then we'll be able to launch a trainig job:

```bash
pip install kubernetes
pip install docker

python -m elasticdl.python.elasticdl.client train \
    --model_zoo=model_zoo \
    --model_def=mnist_subclass.mnist_subclass.CustomModel \
    --image_base=elasticdl:ci \
    --training_data_dir=/data/mnist/train \
    --evaluation_data_dir=/data/mnist/test \
    --num_epochs=1 \
    --master_resource_request="cpu=1,memory=512Mi" \
    --master_resource_limit="cpu=1,memory=512Mi" \
    --worker_resource_request="cpu=1,memory=1024Mi" \
    --worker_resource_limit="cpu=1,memory=1024Mi" \
    --minibatch_size=10 \
    --records_per_task=100 \
    --num_workers=2 \
    --checkpoint_steps=2 \
    --grads_to_wait=2 \
    --job_name=test \
    --image_pull_policy=Never \
    --log_level=INFO \
    --envs=e1=v1,e2=v2
```

The command will create a master Pod in Kubernetes, which is effectively a PS. The master Pod will
in turn other workers:

```bash
$ kubectl get pods
NAME                      READY   STATUS    RESTARTS   AGE
elasticdl-test-master     1/1     Running   0          10s
elasticdl-test-worker-0   1/1     Running   0          6s
elasticdl-test-worker-1   1/1     Running   0          6s
```

The workers will have OwnerReference set to master, so deleting master will delete all workers.

```
$ kubectl get pods elasticdl-test-worker-0 -o yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: "2019-09-13T08:00:57Z"
  labels:
    app: elasticdl
    elasticdl-job-name: test
    elasticdl-replica-index: "0"
    elasticdl-replica-type: worker
  name: elasticdl-test-worker-0
  namespace: default
  ownerReferences:
  - apiVersion: v1
    blockOwnerDeletion: true
    kind: Pod
    name: elasticdl-test-master
    uid: a6d24c1e-b5c4-4bca-aa8e-7c772c59e73c
  resourceVersion: "1279"
```
