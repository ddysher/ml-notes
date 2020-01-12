<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [Components](#components)
- [Projects](#projects)
  - [Katib](#katib)
  - [Fairing](#fairing)
  - [Pipelines](#pipelines)
- [Experiment (v0.0)](#experiment-v00)
  - [Initialize workspace](#initialize-workspace)
  - [Run kubeflow core](#run-kubeflow-core)
  - [Run model training/serving](#run-model-trainingserving)
- [Experiment (v0.7)](#experiment-v07)
  - [Installation](#installation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 01/06/2020, v0.7*

## Introduction

> The Kubeflow project is dedicated to making deployments of machine learning (ML) workflows on
> Kubernetes simple, portable and scalable. Our goal is not to recreate other services, but to
> provide a straightforward way to deploy best-of-breed open-source systems for ML to diverse
> infrastructures. Anywhere you are running Kubernetes, you should be able to run Kubeflow.

## Components

Logical components in KubeFlow:
- Jupyter Notebooks: Using Jupyter notebooks in Kubeflow
- Hyperparameter Tuning: Hyperparameter tuning of ML models in Kubeflow
- Pipelines: ML Pipelines in Kubeflow
- Serving: Serving of ML models in Kubeflow
- Training: Training of ML models in Kubeflow
- Miscellaneous: Miscellaneous Kubeflow components

As of v0.7, third-party components include:
- argo: for pipelines
- istio: for kfserving
- knative: for kfserving
- seldon: for serving (alternative to kfserving)
- minio: store artifacts, for pipelines
- mysql: store metadata, for pipelines and others
- tensorboard: visualization

and projects from KubeFlow include:
- dashboard: a central dashboard
- operators: tf-operator, pytorch-operator
- katib: controller, manager, ui, db
- metadata: controller, db, ui, etc
- pipelines: controller, ui, persistenceagent, etc
- notebook: controller
- kfserving: controller

# Projects

## Katib

In google vizier, client uses SDK to query vizier for suggestions (trial), use the trial to run
training, then report metrics back to server. However, in katib (very early, v0.1.0), everything
is done via study config. Running a trial is done in katib instead of users launching training
themselves - the suggestioned parameters are passed as container entrypoint. See this [blog](http://gaocegege.com/Blog/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0/katib).

**Related Projects -  [advisor](https://github.com/tobegit3hub/advisor)**

The project is a very simple system implementing vizier API. At its core, it is a web application
with a few endpoints, i.e. CRUD studies, suggestions, etc. Following is the API in advisor:

```python
client = AdvisorClient()

# Create the study
study_configuration = {
  "goal": "MAXIMIZE",
  "maxTrials": 5,
  "maxParallelTrials": 1,
  "params": [
    {
      "parameterName": "hidden1",
      "type": "INTEGER",
      "minValue": 40,
      "maxValue": 400,
      "scallingType": "LINEAR"
    }
  ]
}
study = client.create_study("Study", study_configuration)

# Get suggested trials
trials = client.get_suggestions(study, 3)

# Training ...


# Complete the trial
client.complete_trial(trial, trial_metrics)
```

When calling `create_study`, the object is saved to backend; when calling `get_suggestions`,
corresponding algorithm is invoked to calculate trial suggestions; when `complete_trial` is called,
the trial status is updated to completed and saved to backend. Users are responsible to train
their model based on trial suggestions and provide the objective value.

## Fairing

- *Date: 01/2019, v0.0*
- *Date: 01/2020, v0.5*

Fairing allows launching training jobs from python code using decorator. It can check if the code
is running in notebook, and if so, it will convert notebook to python code using `nbconvert`.
Under the hook, the python code will be built into a docker image and submit to kubeflow.

User defines a class with a decorator, then creates an object from the class and call its train method.

```python
@Train(package={'name': 'fairing-mnist', 'repository': '<your-repository-name>', 'publish': True})
class MyModel(object):
    def train(self):
      pass

if __name__ == '__main__':
    model = MyModel()
    model.train()
```

The `Train` decorator is a class decorator with the following content:

<details><summary>Train decorator</summary><p>

```python
# @Train decorator
class Train(object):
    def __init__(self, package, tensorboard=None, architecture=BasicArchitecture(), strategy=BasicTrainingStrategy()):
        self.trainer = Trainer(package, tensorboard, architecture, strategy)

    def __call__(self, cls):
        class UserClass(cls):
            # self refers to the Train instance
            # user_class is equivalentto self in the UserClass instance
            def __init__(user_class):
                user_class.is_training_initialized = False

            def __getattribute__(user_class, attribute_name):
                # Overriding train in order to minimize the changes necessary in the user
                # code to go from local to remote execution.
                # That way, by simply commenting or uncommenting the Train decorator
                # Model.train() will execute either on the local setup or in kubernetes

                if attribute_name != 'train' or user_class.is_training_initialized:
                    return super(UserClass, user_class).__getattribute__(attribute_name)

                if attribute_name == 'train' and not is_runtime_phase():
                    return super(UserClass, user_class).__getattribute__('_deploy_training')

                print(type(self))
                print(type(user_class))
                user_class.is_training_initialized = True
                self.trainer.start_training(user_class)
                return super(UserClass, user_class).__getattribute__('_noop_attribute')

            def _noop_attribute(user_class):
                pass

            def _deploy_training(user_class):
                self.trainer.deploy_training()


        return UserClass
```

</p></details></br>

The inner `UserClass` is the wrapper class on top of MyModel - all function calls go through the
`__call__` method. There are two methods worth mentioning, one is the `train()` method that calls
user code (MyModel.train) to start training, and `deploy_train()` method which creates a dockerfile,
build it (directly issue docker build command) and deploy training tfjob to kubernetes.

*Update on 01/05/2020, v0.5*

Fairing design has changed to explicit function SDK based approach: instead of using decorators,
users directly call fairing library to launch training job, serving service, etc. For example,

```python
from kubeflow import fairing
from kubeflow.fairing import TrainJob
from kubeflow.fairing.backends import KubeflowGKEBackend

job = TrainJob("train.py", backend=KubeflowGKEBackend())
job.submit()
```

As another example,

```python
from kubeflow import fairing
fairing.config.set_preprocessor('python', input_files=[__file__])
fairing.config.set_builder(name='docker', registry='<your-registry-name>',
                           base_image='tensorflow/tensorflow:1.13.1-py3')
fairing.config.run()
```

## Pipelines

*Date: 01/06/2020, v0.1*

Kubeflow pipeline describes a machine learning workflow including all of the components in the
workflow and how they combine in the form of a graph.

[Architecture-wise](https://www.kubeflow.org/docs/pipelines/overview/pipelines-overview/#architectural-overview), it consists of:
- Python SDK and DSL compiler
- Backend and Frontend
- Kubernetes operators to run workflow (wrap around argo)
- Database
  - Metadata: save jobs, runs, etc into MySQL database
  - Artifact: store pipeline outputs, etc into S3 compatible storage like Minio

The core of kubeflow pipeline is its SDK, which compiles to a Kubernetes YAML. For example, running
`mnist_pipeline.py` will generate a `mnist_pipeline.py.tar.gz`, which contains a simple file named
`pipeline.yaml`. The full example can be found [here](https://github.com/kubeflow/examples/tree/d9258237163a2df820889904206b40816afb9c1f/pipelines/mnist-pipelines).

<details><summary>mnist_pipeline.py</summary><p>

```python
import kfp.dsl as dsl
import kfp.gcp as gcp
import kfp.onprem as onprem

platform = 'GCP'

@dsl.pipeline(
  name='MNIST',
  description='A pipeline to train and serve the MNIST example.'
)
def mnist_pipeline(model_export_dir='gs://your-bucket/export',
                   train_steps='200',
                   learning_rate='0.01',
                   batch_size='100',
                   pvc_name=''):
  """
  Pipeline with three stages:
    1. train an MNIST classifier
    2. deploy a tf-serving instance to the cluster
    3. deploy a web-ui to interact with it
  """
  train = dsl.ContainerOp(
      name='train',
      image='gcr.io/kubeflow-examples/mnist/model:v20190304-v0.2-176-g15d997b',
      arguments=[
          "/opt/model.py",
          "--tf-export-dir", model_export_dir,
          "--tf-train-steps", train_steps,
          "--tf-batch-size", batch_size,
          "--tf-learning-rate", learning_rate
          ]
  )


  serve_args = [
      '--model-export-path', model_export_dir,
      '--server-name', "mnist-service"
  ]
  if platform != 'GCP':
    serve_args.extend([
        '--cluster-name', "mnist-pipeline",
        '--pvc-name', pvc_name
    ])

  serve = dsl.ContainerOp(
      name='serve',
      image='gcr.io/ml-pipeline/ml-pipeline-kubeflow-deployer:'
            '7775692adf28d6f79098e76e839986c9ee55dd61',
      arguments=serve_args
  )
  serve.after(train)


  webui_args = [
          '--image', 'gcr.io/kubeflow-examples/mnist/web-ui:'
                     'v20190304-v0.2-176-g15d997b-pipelines',
          '--name', 'web-ui',
          '--container-port', '5000',
          '--service-port', '80',
          '--service-type', "LoadBalancer"
  ]
  if platform != 'GCP':
    webui_args.extend([
      '--cluster-name', "mnist-pipeline"
    ])

  web_ui = dsl.ContainerOp(
      name='web-ui',
      image='gcr.io/kubeflow-examples/mnist/deploy-service:latest',
      arguments=webui_args
  )
  web_ui.after(serve)

  steps = [train, serve, web_ui]
  for step in steps:
    if platform == 'GCP':
      step.apply(gcp.use_gcp_secret('user-gcp-sa'))
    else:
      step.apply(onprem.mount_pvc(pvc_name, 'local-storage', '/mnt'))

if __name__ == '__main__':
  import kfp.compiler as compiler
  compiler.Compiler().compile(mnist_pipeline, __file__ + '.tar.gz')
```

</p></details></br>

<details><summary>pipeline.yaml</summary><p>

```yaml
"apiVersion": |-
  argoproj.io/v1alpha1
"kind": |-
  Workflow
"metadata":
  "annotations":
    "pipelines.kubeflow.org/pipeline_spec": |-
      {"description": "A pipeline to train and serve the MNIST example.", "inputs": [{"default": "gs://your-bucket/export", "name": "model_export_dir"}, {"default": "200", "name": "train_steps"}, {"default": "0.01", "name": "learning_rate"}, {"default": "100", "name": "batch_size"}, {"default": "", "name": "pvc_name"}], "name": "MNIST"}
  "generateName": |-
    mnist-
"spec":
  "arguments":
    "parameters":
    - "name": |-
        model_export_dir
      "value": |-
        gs://your-bucket/export
    - "name": |-
        train_steps
      "value": |-
        200
    - "name": |-
        learning_rate
      "value": |-
        0.01
    - "name": |-
        batch_size
      "value": |-
        100
    - "name": |-
        pvc_name
      "value": ""
  "entrypoint": |-
    mnist
  "serviceAccountName": |-
    pipeline-runner
  "templates":
  - "dag":
      "tasks":
      - "arguments":
          "parameters":
          - "name": |-
              model_export_dir
            "value": |-
              {{inputs.parameters.model_export_dir}}
        "dependencies":
        - |-
          train
        "name": |-
          serve
        "template": |-
          serve
      - "arguments":
          "parameters":
          - "name": |-
              batch_size
            "value": |-
              {{inputs.parameters.batch_size}}
          - "name": |-
              learning_rate
            "value": |-
              {{inputs.parameters.learning_rate}}
          - "name": |-
              model_export_dir
            "value": |-
              {{inputs.parameters.model_export_dir}}
          - "name": |-
              train_steps
            "value": |-
              {{inputs.parameters.train_steps}}
        "name": |-
          train
        "template": |-
          train
      - "dependencies":
        - |-
          serve
        "name": |-
          web-ui
        "template": |-
          web-ui
    "inputs":
      "parameters":
      - "name": |-
          batch_size
      - "name": |-
          learning_rate
      - "name": |-
          model_export_dir
      - "name": |-
          train_steps
    "name": |-
      mnist
  - "container":
      "args":
      - |-
        --model-export-path
      - |-
        {{inputs.parameters.model_export_dir}}
      - |-
        --server-name
      - |-
        mnist-service
      "env":
      - "name": |-
          GOOGLE_APPLICATION_CREDENTIALS
        "value": |-
          /secret/gcp-credentials/user-gcp-sa.json
      - "name": |-
          CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE
        "value": |-
          /secret/gcp-credentials/user-gcp-sa.json
      "image": |-
        gcr.io/ml-pipeline/ml-pipeline-kubeflow-deployer:7775692adf28d6f79098e76e839986c9ee55dd61
      "volumeMounts":
      - "mountPath": |-
          /secret/gcp-credentials
        "name": |-
          gcp-credentials-user-gcp-sa
    "inputs":
      "parameters":
      - "name": |-
          model_export_dir
    "name": |-
      serve
    "volumes":
    - "name": |-
        gcp-credentials-user-gcp-sa
      "secret":
        "secretName": |-
          user-gcp-sa
  - "container":
      "args":
      - |-
        /opt/model.py
      - |-
        --tf-export-dir
      - |-
        {{inputs.parameters.model_export_dir}}
      - |-
        --tf-train-steps
      - |-
        {{inputs.parameters.train_steps}}
      - |-
        --tf-batch-size
      - |-
        {{inputs.parameters.batch_size}}
      - |-
        --tf-learning-rate
      - |-
        {{inputs.parameters.learning_rate}}
      "env":
      - "name": |-
          GOOGLE_APPLICATION_CREDENTIALS
        "value": |-
          /secret/gcp-credentials/user-gcp-sa.json
      - "name": |-
          CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE
        "value": |-
          /secret/gcp-credentials/user-gcp-sa.json
      "image": |-
        gcr.io/kubeflow-examples/mnist/model:v20190304-v0.2-176-g15d997b
      "volumeMounts":
      - "mountPath": |-
          /secret/gcp-credentials
        "name": |-
          gcp-credentials-user-gcp-sa
    "inputs":
      "parameters":
      - "name": |-
          batch_size
      - "name": |-
          learning_rate
      - "name": |-
          model_export_dir
      - "name": |-
          train_steps
    "name": |-
      train
    "volumes":
    - "name": |-
        gcp-credentials-user-gcp-sa
      "secret":
        "secretName": |-
          user-gcp-sa
  - "container":
      "args":
      - |-
        --image
      - |-
        gcr.io/kubeflow-examples/mnist/web-ui:v20190304-v0.2-176-g15d997b-pipelines
      - |-
        --name
      - |-
        web-ui
      - |-
        --container-port
      - |-
        5000
      - |-
        --service-port
      - |-
        80
      - |-
        --service-type
      - |-
        LoadBalancer
      "env":
      - "name": |-
          GOOGLE_APPLICATION_CREDENTIALS
        "value": |-
          /secret/gcp-credentials/user-gcp-sa.json
      - "name": |-
          CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE
        "value": |-
          /secret/gcp-credentials/user-gcp-sa.json
      "image": |-
        gcr.io/kubeflow-examples/mnist/deploy-service:latest
      "volumeMounts":
      - "mountPath": |-
          /secret/gcp-credentials
        "name": |-
          gcp-credentials-user-gcp-sa
    "name": |-
      web-ui
    "volumes":
    - "name": |-
        gcp-credentials-user-gcp-sa
      "secret":
        "secretName": |-
          user-gcp-sa
```

</p></details></br>

The pipeline SDK includes following packages:
- kfp.compiler
- kfp.components
- kfp.dsl
- kfp.Client
- kfp.notebook

*References*

- https://www.kubeflow.org/docs/pipelines/
- https://www.kubeflow.org/docs/pipelines/overview/pipelines-overview/
- https://github.com/amygdala/code-snippets/blob/master/ml/kubeflow-pipelines/README_github_summ.md

## KFServing

*Date: 01/12/2019, v0.2*

KFServing is a serverless inference solution on Kubernetes, based on KNative and Istio. KFServing
supports Tensorflow, XGBoost, ScikitLearn, PyTorch, ONNX, etc.

> You can use KFServing to do the following:
> - Provide a Kubernetes Custom Resource Definition for serving ML models on arbitrary frameworks.
> - Encapsulate the complexity of autoscaling, networking, health checking, and server configuration to bring cutting edge serving features like GPU autoscaling, scale to zero, and canary rollouts to your ML deployments.
> - Enable a simple, pluggable, and complete story for your production ML inference server by providing prediction, pre-processing, post-processing and explainability out of the box.

Note that KFServing in not the only serving solution provided by KubeFlow, others being (all of
these solutions are external to KubeFlow):
- standalone tensorrt inference server: kubeflow just provides a few manifests to deploy trtis.
- seldon: kubeflow provides installation and examples of running seldon on kubernetes.
- tfserving: kubeflow provides manifests and examples to run tfserving on kubernetes, includes
  running tfserving with batch support, and integration with istio.

      "--resolv-conf=/etc/resolv.conf.kubelet"

kubectl label ns default serving.kubeflow.org/inferenceservice=enabled


```
$ kubectl get all -n default

NAME                                                                  READY   STATUS     RESTARTS   AGE
pod/flowers-sample-predictor-default-rp5wh-deployment-66ddcc99q7w5p   0/2     Init:0/1   0          40s


NAME                                                   TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
service/flowers-sample-predictor-default-rp5wh         ClusterIP   10.0.0.195   <none>        80/TCP              40s
service/flowers-sample-predictor-default-rp5wh-ftk2j   ClusterIP   10.0.0.220   <none>        9090/TCP,9091/TCP   41s
service/flowers-sample-predictor-default-rp5wh-xxglt   ClusterIP   10.0.0.247   <none>        80/TCP              40s
service/kubernetes                                     ClusterIP   10.0.0.1     <none>        443/TCP             25m


NAME                                                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/flowers-sample-predictor-default-rp5wh-deployment   0/1     1            0           41s

NAME                                                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/flowers-sample-predictor-default-rp5wh-deployment-66ddcc9966   1         1         0       41s








NAME                                                                  CONFIG NAME                        K8S SERVICE NAME                         GENERATION   READY     REASON
revision.serving.knative.dev/flowers-sample-predictor-default-rp5wh   flowers-sample-predictor-default   flowers-sample-predictor-default-rp5wh   1            Unknown   Deploying

NAME                                                                 LATESTCREATED                            LATESTREADY   READY     REASON
configuration.serving.knative.dev/flowers-sample-predictor-default   flowers-sample-predictor-default-rp5wh                 Unknown

NAME                                                           URL                                                           LATESTCREATED                            LATESTREADY   READY     REASON
service.serving.knative.dev/flowers-sample-predictor-default   http://flowers-sample-predictor-default.default.example.com   flowers-sample-predictor-default-rp5wh                 Unknown   RevisionMissing

NAME                                                         URL                                                           READY     REASON
route.serving.knative.dev/flowers-sample-predictor-default   http://flowers-sample-predictor-default.default.example.com   Unknown   RevisionMissing
```


```
$ kubectl get deployment flowers-sample-predictor-default-rp5wh-deployment -o yaml| grep image
        image: index.docker.io/tensorflow/serving@sha256:f7e59a29cbc17a6b507751cddde37bccad4407c05ebf2c13b8e6ccb7d2e9affb
        imagePullPolicy: IfNotPresent
        image: gcr.io/knative-releases/knative.dev/serving/cmd/queue@sha256:e0654305370cf3bbbd0f56f97789c92cf5215f752b70902eba5d5fc0e88c5aca
        imagePullPolicy: IfNotPresent
```

# Experiment (v0.0)

*Date: 03/27/2018, v0.0*

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

# Experiment (v0.7)

*Date: 01/05/2020, v0.7*

## Installation

Export configurations using env:

```shell
# Set KF_NAME to the name of your Kubeflow deployment.
export KF_NAME='kf-test'

# Set the path to the base directory where you want to store one or more
# Kubeflow deployments. For example, /opt/.
# Then set the Kubeflow application directory for this deployment.
export BASE_DIR=`pwd`
export KF_DIR=${BASE_DIR}/${KF_NAME}

# Set the configuration file to use when deploying Kubeflow.
# The following configuration installs Istio by default. Comment out
# the Istio components in the config file to skip Istio installation.
# See https://github.com/kubeflow/kubeflow/pull/3663
export CONFIG_URI="https://raw.githubusercontent.com/kubeflow/manifests/v0.7-branch/kfdef/kfctl_k8s_istio.0.7.1.yaml"
```

Then run:

```
$ mkdir -p ${KF_DIR}
$ cd ${KF_DIR}
$ kfctl apply -V -f ${CONFIG_URI}
```

Now check all resources deployed by KubeFlow, under `kubeflow`, `istio`, `knative-serving` namespaces:

<details><summary>kubectl -n kubeflow get all</summary><p>

```
$ kubectl -n kubeflow get all
NAME                                                               READY   STATUS    RESTARTS   AGE
pod/admission-webhook-bootstrap-stateful-set-0                     1/1     Running   0          4h47m
pod/admission-webhook-deployment-b7d89f4c7-wr82s                   1/1     Running   0          4h33m
pod/application-controller-stateful-set-0                          1/1     Running   0          4h47m
pod/argo-ui-6754c76f9b-msgn8                                       1/1     Running   0          4h47m
pod/centraldashboard-5578cc9569-kdpt5                              1/1     Running   0          4h47m
pod/jupyter-web-app-deployment-6b7d9c5fd6-4zwnl                    1/1     Running   0          4h47m
pod/katib-controller-789d76d446-qjtr4                              1/1     Running   1          4h47m
pod/katib-db-75975d8dbd-r2h7h                                      1/1     Running   0          4h47m
pod/katib-manager-59bb84948f-jdkjv                                 1/1     Running   5          4h47m
pod/katib-ui-dd75bd446-dvbfs                                       1/1     Running   0          4h47m
pod/kfserving-controller-manager-0                                 2/2     Running   1          4h47m
pod/metacontroller-0                                               1/1     Running   0          4h47m
pod/metadata-db-7584d44b65-8g9d6                                   1/1     Running   0          4h47m
pod/metadata-deployment-cd8f7d58f-z4hcm                            1/1     Running   1          4h47m
pod/metadata-envoy-deployment-bff4f8b9-9ntwc                       1/1     Running   0          4h47m
pod/metadata-grpc-deployment-7cc5d84854-bwnl9                      1/1     Running   8          4h47m
pod/metadata-ui-7c978889b5-sshbh                                   1/1     Running   0          4h47m
pod/minio-764648495-wgg99                                          1/1     Running   0          4h47m
pod/ml-pipeline-588b64fff-tflqr                                    1/1     Running   1          4h47m
pod/ml-pipeline-ml-pipeline-visualizationserver-6c7c97869d-gmwd2   1/1     Running   0          4h47m
pod/ml-pipeline-persistenceagent-79ff896578-8c62g                  1/1     Running   3          4h47m
pod/ml-pipeline-scheduledworkflow-7d89bb6db5-jnq65                 1/1     Running   0          4h47m
pod/ml-pipeline-ui-6656886579-97dvh                                1/1     Running   0          4h47m
pod/ml-pipeline-viewer-controller-deployment-546bd5f545-qctnl      1/1     Running   0          4h47m
pod/mysql-6c9cb88c4d-wdkpw                                         1/1     Running   0          4h47m
pod/notebook-controller-deployment-6d594ddd6b-5jn4c                1/1     Running   0          4h47m
pod/profiles-deployment-67799585bd-cx8bv                           2/2     Running   0          4h47m
pod/pytorch-operator-fdfd7985-qrzph                                1/1     Running   0          4h47m
pod/seldon-operator-controller-manager-0                           1/1     Running   1          4h47m
pod/spartakus-volunteer-5888bc655-hrm85                            1/1     Running   0          4h47m
pod/tensorboard-5f685f9d79-fphhr                                   1/1     Running   0          4h47m
pod/tf-job-operator-5dff84b966-6279c                               1/1     Running   0          4h47m
pod/workflow-controller-85c665bcb9-f8kwk                           1/1     Running   0          4h47m


NAME                                                   TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
service/admission-webhook-service                      ClusterIP   10.0.0.248   <none>        443/TCP             4h47m
service/application-controller-service                 ClusterIP   10.0.0.147   <none>        443/TCP             4h47m
service/argo-ui                                        NodePort    10.0.0.175   <none>        80:30491/TCP        4h47m
service/centraldashboard                               ClusterIP   10.0.0.220   <none>        80/TCP              4h47m
service/jupyter-web-app-service                        ClusterIP   10.0.0.161   <none>        80/TCP              4h47m
service/katib-controller                               ClusterIP   10.0.0.141   <none>        443/TCP             4h47m
service/katib-db                                       ClusterIP   10.0.0.120   <none>        3306/TCP            4h47m
service/katib-manager                                  ClusterIP   10.0.0.135   <none>        6789/TCP            4h47m
service/katib-ui                                       ClusterIP   10.0.0.33    <none>        80/TCP              4h47m
service/kfserving-controller-manager-metrics-service   ClusterIP   10.0.0.237   <none>        8443/TCP            4h47m
service/kfserving-controller-manager-service           ClusterIP   10.0.0.118   <none>        443/TCP             4h47m
service/kfserving-webhook-server-service               ClusterIP   10.0.0.232   <none>        443/TCP             4h12m
service/metadata-db                                    ClusterIP   10.0.0.113   <none>        3306/TCP            4h47m
service/metadata-envoy-service                         ClusterIP   10.0.0.22    <none>        9090/TCP            4h47m
service/metadata-grpc-service                          ClusterIP   10.0.0.231   <none>        8080/TCP            4h47m
service/metadata-service                               ClusterIP   10.0.0.149   <none>        8080/TCP            4h47m
service/metadata-ui                                    ClusterIP   10.0.0.139   <none>        80/TCP              4h47m
service/minio-service                                  ClusterIP   10.0.0.191   <none>        9000/TCP            4h47m
service/ml-pipeline                                    ClusterIP   10.0.0.128   <none>        8888/TCP,8887/TCP   4h47m
service/ml-pipeline-ml-pipeline-visualizationserver    ClusterIP   10.0.0.96    <none>        8888/TCP            4h47m
service/ml-pipeline-tensorboard-ui                     ClusterIP   10.0.0.34    <none>        80/TCP              4h47m
service/ml-pipeline-ui                                 ClusterIP   10.0.0.2     <none>        80/TCP              4h47m
service/mysql                                          ClusterIP   10.0.0.31    <none>        3306/TCP            4h47m
service/notebook-controller-service                    ClusterIP   10.0.0.179   <none>        443/TCP             4h47m
service/profiles-kfam                                  ClusterIP   10.0.0.11    <none>        8081/TCP            4h47m
service/pytorch-operator                               ClusterIP   10.0.0.94    <none>        8443/TCP            4h47m
service/seldon-operator-controller-manager-service     ClusterIP   10.0.0.61    <none>        443/TCP             4h47m
service/tensorboard                                    ClusterIP   10.0.0.152   <none>        9000/TCP            4h47m
service/tf-job-operator                                ClusterIP   10.0.0.15    <none>        8443/TCP            4h47m
service/webhook-server-service                         ClusterIP   10.0.0.230   <none>        443/TCP             4h47m


NAME                                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/admission-webhook-deployment                  1/1     1            1           4h47m
deployment.apps/argo-ui                                       1/1     1            1           4h47m
deployment.apps/centraldashboard                              1/1     1            1           4h47m
deployment.apps/jupyter-web-app-deployment                    1/1     1            1           4h47m
deployment.apps/katib-controller                              1/1     1            1           4h47m
deployment.apps/katib-db                                      1/1     1            1           4h47m
deployment.apps/katib-manager                                 1/1     1            1           4h47m
deployment.apps/katib-ui                                      1/1     1            1           4h47m
deployment.apps/metadata-db                                   1/1     1            1           4h47m
deployment.apps/metadata-deployment                           1/1     1            1           4h47m
deployment.apps/metadata-envoy-deployment                     1/1     1            1           4h47m
deployment.apps/metadata-grpc-deployment                      1/1     1            1           4h47m
deployment.apps/metadata-ui                                   1/1     1            1           4h47m
deployment.apps/minio                                         1/1     1            1           4h47m
deployment.apps/ml-pipeline                                   1/1     1            1           4h47m
deployment.apps/ml-pipeline-ml-pipeline-visualizationserver   1/1     1            1           4h47m
deployment.apps/ml-pipeline-persistenceagent                  1/1     1            1           4h47m
deployment.apps/ml-pipeline-scheduledworkflow                 1/1     1            1           4h47m
deployment.apps/ml-pipeline-ui                                1/1     1            1           4h47m
deployment.apps/ml-pipeline-viewer-controller-deployment      1/1     1            1           4h47m
deployment.apps/mysql                                         1/1     1            1           4h47m
deployment.apps/notebook-controller-deployment                1/1     1            1           4h47m
deployment.apps/profiles-deployment                           1/1     1            1           4h47m
deployment.apps/pytorch-operator                              1/1     1            1           4h47m
deployment.apps/spartakus-volunteer                           1/1     1            1           4h47m
deployment.apps/tensorboard                                   1/1     1            1           4h47m
deployment.apps/tf-job-operator                               1/1     1            1           4h47m
deployment.apps/workflow-controller                           1/1     1            1           4h47m

NAME                                                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/admission-webhook-deployment-b7d89f4c7                   1         1         1       4h47m
replicaset.apps/argo-ui-6754c76f9b                                       1         1         1       4h47m
replicaset.apps/centraldashboard-5578cc9569                              1         1         1       4h47m
replicaset.apps/jupyter-web-app-deployment-6b7d9c5fd6                    1         1         1       4h47m
replicaset.apps/katib-controller-789d76d446                              1         1         1       4h47m
replicaset.apps/katib-db-75975d8dbd                                      1         1         1       4h47m
replicaset.apps/katib-manager-59bb84948f                                 1         1         1       4h47m
replicaset.apps/katib-ui-dd75bd446                                       1         1         1       4h47m
replicaset.apps/metadata-db-7584d44b65                                   1         1         1       4h47m
replicaset.apps/metadata-deployment-cd8f7d58f                            1         1         1       4h47m
replicaset.apps/metadata-envoy-deployment-bff4f8b9                       1         1         1       4h47m
replicaset.apps/metadata-grpc-deployment-7cc5d84854                      1         1         1       4h47m
replicaset.apps/metadata-ui-7c978889b5                                   1         1         1       4h47m
replicaset.apps/minio-764648495                                          1         1         1       4h47m
replicaset.apps/ml-pipeline-588b64fff                                    1         1         1       4h47m
replicaset.apps/ml-pipeline-ml-pipeline-visualizationserver-6c7c97869d   1         1         1       4h47m
replicaset.apps/ml-pipeline-persistenceagent-79ff896578                  1         1         1       4h47m
replicaset.apps/ml-pipeline-scheduledworkflow-7d89bb6db5                 1         1         1       4h47m
replicaset.apps/ml-pipeline-ui-6656886579                                1         1         1       4h47m
replicaset.apps/ml-pipeline-viewer-controller-deployment-546bd5f545      1         1         1       4h47m
replicaset.apps/mysql-6c9cb88c4d                                         1         1         1       4h47m
replicaset.apps/notebook-controller-deployment-6d594ddd6b                1         1         1       4h47m
replicaset.apps/profiles-deployment-67799585bd                           1         1         1       4h47m
replicaset.apps/pytorch-operator-fdfd7985                                1         1         1       4h47m
replicaset.apps/spartakus-volunteer-5888bc655                            1         1         1       4h47m
replicaset.apps/tensorboard-5f685f9d79                                   1         1         1       4h47m
replicaset.apps/tf-job-operator-5dff84b966                               1         1         1       4h47m
replicaset.apps/workflow-controller-85c665bcb9                           1         1         1       4h47m

NAME                                                        READY   AGE
statefulset.apps/admission-webhook-bootstrap-stateful-set   1/1     4h47m
statefulset.apps/application-controller-stateful-set        1/1     4h47m
statefulset.apps/kfserving-controller-manager               1/1     4h47m
statefulset.apps/metacontroller                             1/1     4h47m
statefulset.apps/seldon-operator-controller-manager         1/1     4h47m
```

</p></details></br>

<details><summary>kubectl -n istio-system get all</summary><p>

```
$ kubectl -n istio-system get all
NAME                                          READY   STATUS      RESTARTS   AGE
pod/grafana-86f89dbd84-hx6pc                  1/1     Running     0          4h50m
pod/istio-citadel-74966f47d6-sjq22            1/1     Running     0          4h50m
pod/istio-cleanup-secrets-1.1.6-qrj86         0/1     Completed   0          4h50m
pod/istio-egressgateway-5c64d575bc-rj4t7      1/1     Running     0          4h50m
pod/istio-galley-784b9f6d75-vf4cb             1/1     Running     0          4h50m
pod/istio-grafana-post-install-1.1.6-f49n8    0/1     Completed   0          4h50m
pod/istio-ingressgateway-589ff776dd-48r9k     1/1     Running     0          4h50m
pod/istio-pilot-677df6b6d4-frnmf              2/2     Running     0          4h50m
pod/istio-policy-6f74d9d95d-hj2dd             2/2     Running     15         4h50m
pod/istio-security-post-install-1.1.6-cvk68   0/1     Completed   0          4h50m
pod/istio-sidecar-injector-866f4b98c7-z4lc8   1/1     Running     0          4h50m
pod/istio-telemetry-549c8f9dcb-96k45          2/2     Running     14         4h50m
pod/istio-tracing-555cf644d-zl8vx             1/1     Running     0          4h50m
pod/kiali-7db44d6dfb-tjpzf                    1/1     Running     0          4h50m
pod/prometheus-d44645598-khw4b                1/1     Running     0          4h50m


NAME                             TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                                                                                                      AGE
service/grafana                  ClusterIP   10.0.0.74    <none>        3000/TCP                                                                                                                                     4h50m
service/istio-citadel            ClusterIP   10.0.0.27    <none>        8060/TCP,15014/TCP                                                                                                                           4h50m
service/istio-egressgateway      ClusterIP   10.0.0.52    <none>        80/TCP,443/TCP,15443/TCP                                                                                                                     4h50m
service/istio-galley             ClusterIP   10.0.0.150   <none>        443/TCP,15014/TCP,9901/TCP                                                                                                                   4h50m
service/istio-ingressgateway     NodePort    10.0.0.14    <none>        15020:30637/TCP,80:31380/TCP,443:31390/TCP,31400:31400/TCP,15029:31032/TCP,15030:32320/TCP,15031:31351/TCP,15032:32738/TCP,15443:30102/TCP   4h50m
service/istio-pilot              ClusterIP   10.0.0.117   <none>        15010/TCP,15011/TCP,8080/TCP,15014/TCP                                                                                                       4h50m
service/istio-policy             ClusterIP   10.0.0.121   <none>        9091/TCP,15004/TCP,15014/TCP                                                                                                                 4h50m
service/istio-sidecar-injector   ClusterIP   10.0.0.162   <none>        443/TCP                                                                                                                                      4h50m
service/istio-telemetry          ClusterIP   10.0.0.99    <none>        9091/TCP,15004/TCP,15014/TCP,42422/TCP                                                                                                       4h50m
service/jaeger-agent             ClusterIP   None         <none>        5775/UDP,6831/UDP,6832/UDP                                                                                                                   4h50m
service/jaeger-collector         ClusterIP   10.0.0.167   <none>        14267/TCP,14268/TCP                                                                                                                          4h50m
service/jaeger-query             ClusterIP   10.0.0.103   <none>        16686/TCP                                                                                                                                    4h50m
service/kiali                    ClusterIP   10.0.0.24    <none>        20001/TCP                                                                                                                                    4h50m
service/prometheus               ClusterIP   10.0.0.79    <none>        9090/TCP                                                                                                                                     4h50m
service/tracing                  ClusterIP   10.0.0.13    <none>        80/TCP                                                                                                                                       4h50m
service/zipkin                   ClusterIP   10.0.0.214   <none>        9411/TCP                                                                                                                                     4h50m


NAME                                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/grafana                  1/1     1            1           4h50m
deployment.apps/istio-citadel            1/1     1            1           4h50m
deployment.apps/istio-egressgateway      1/1     1            1           4h50m
deployment.apps/istio-galley             1/1     1            1           4h50m
deployment.apps/istio-ingressgateway     1/1     1            1           4h50m
deployment.apps/istio-pilot              1/1     1            1           4h50m
deployment.apps/istio-policy             1/1     1            1           4h50m
deployment.apps/istio-sidecar-injector   1/1     1            1           4h50m
deployment.apps/istio-telemetry          1/1     1            1           4h50m
deployment.apps/istio-tracing            1/1     1            1           4h50m
deployment.apps/kiali                    1/1     1            1           4h50m
deployment.apps/prometheus               1/1     1            1           4h50m

NAME                                                DESIRED   CURRENT   READY   AGE
replicaset.apps/grafana-86f89dbd84                  1         1         1       4h50m
replicaset.apps/istio-citadel-74966f47d6            1         1         1       4h50m
replicaset.apps/istio-egressgateway-5c64d575bc      1         1         1       4h50m
replicaset.apps/istio-galley-784b9f6d75             1         1         1       4h50m
replicaset.apps/istio-ingressgateway-589ff776dd     1         1         1       4h50m
replicaset.apps/istio-pilot-677df6b6d4              1         1         1       4h50m
replicaset.apps/istio-policy-6f74d9d95d             1         1         1       4h50m
replicaset.apps/istio-sidecar-injector-866f4b98c7   1         1         1       4h50m
replicaset.apps/istio-telemetry-549c8f9dcb          1         1         1       4h50m
replicaset.apps/istio-tracing-555cf644d             1         1         1       4h50m
replicaset.apps/kiali-7db44d6dfb                    1         1         1       4h50m
replicaset.apps/prometheus-d44645598                1         1         1       4h50m


NAME                                                       REFERENCE                         TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/istio-egressgateway    Deployment/istio-egressgateway    <unknown>/80%   1         5         1          4h50m
horizontalpodautoscaler.autoscaling/istio-ingressgateway   Deployment/istio-ingressgateway   <unknown>/80%   1         5         1          4h50m
horizontalpodautoscaler.autoscaling/istio-pilot            Deployment/istio-pilot            <unknown>/80%   1         5         1          4h50m
horizontalpodautoscaler.autoscaling/istio-policy           Deployment/istio-policy           <unknown>/80%   1         5         1          4h50m
horizontalpodautoscaler.autoscaling/istio-telemetry        Deployment/istio-telemetry        <unknown>/80%   1         5         1          4h50m

NAME                                          COMPLETIONS   DURATION   AGE
job.batch/istio-cleanup-secrets-1.1.6         1/1           4m1s       4h50m
job.batch/istio-grafana-post-install-1.1.6    1/1           4m12s      4h50m
job.batch/istio-security-post-install-1.1.6   1/1           4m40s      4h50m
```

</p></details></br>

<details><summary>kubectl -n knative-serving get all</summary><p>

```
$ kubectl -n knative-serving get all
NAME                                    READY   STATUS    RESTARTS   AGE
pod/activator-5484756f7b-5ftcb          2/2     Running   2          4h10m
pod/autoscaler-8dc957c8-4ht6x           2/2     Running   2          4h10m
pod/autoscaler-hpa-5654b69d4c-btmmj     1/1     Running   0          4h10m
pod/controller-66654bc6f7-gqs52         1/1     Running   0          4h10m
pod/networking-istio-557465cf96-r8mh6   1/1     Running   0          4h10m
pod/webhook-585767d97f-j9td4            1/1     Running   0          4h10m


NAME                        TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                     AGE
service/activator-service   ClusterIP   10.0.0.42    <none>        80/TCP,81/TCP,9090/TCP      4h50m
service/autoscaler          ClusterIP   10.0.0.104   <none>        8080/TCP,9090/TCP,443/TCP   4h50m
service/controller          ClusterIP   10.0.0.195   <none>        9090/TCP                    4h50m
service/webhook             ClusterIP   10.0.0.229   <none>        443/TCP                     4h50m


NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/activator          1/1     1            1           4h50m
deployment.apps/autoscaler         1/1     1            1           4h50m
deployment.apps/autoscaler-hpa     1/1     1            1           4h50m
deployment.apps/controller         1/1     1            1           4h50m
deployment.apps/networking-istio   1/1     1            1           4h50m
deployment.apps/webhook            1/1     1            1           4h50m

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/activator-5484756f7b          1         1         1       4h50m
replicaset.apps/autoscaler-8dc957c8           1         1         1       4h50m
replicaset.apps/autoscaler-hpa-5654b69d4c     1         1         1       4h50m
replicaset.apps/controller-66654bc6f7         1         1         1       4h50m
replicaset.apps/networking-istio-557465cf96   1         1         1       4h50m
replicaset.apps/webhook-585767d97f            1         1         1       4h50m


NAME                                            REFERENCE              TARGETS          MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/activator   Deployment/activator   <unknown>/100%   1         20        1          4h50m
```

</p></details></br>
