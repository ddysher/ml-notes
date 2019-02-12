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
  - [KFServing](#kfserving)
  - [Metadata](#metadata)
- [Experiment (v0.0)](#experiment-v00)
  - [Initialize workspace](#initialize-workspace)
  - [Run kubeflow core](#run-kubeflow-core)
  - [Run model training/serving](#run-model-trainingserving)
- [Experiment (v1.0)](#experiment-v10)
  - [Installation](#installation)
  - [KFServing](#kfserving-1)
- [Experiments](#experiments)
  - [Standalone KFServing v0.3](#standalone-kfserving-v03)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 01/06/2020, v0.7*
- *Date: 03/05/2020, v1.0*

## Introduction

> The Kubeflow project is dedicated to making deployments of machine learning (ML) workflows on
> Kubernetes simple, portable and scalable. Our goal is not to recreate other services, but to
> provide a straightforward way to deploy best-of-breed open-source systems for ML to diverse
> infrastructures. Anywhere you are running Kubernetes, you should be able to run Kubeflow.

## Components

Logical components in Kubeflow:
- Jupyter Notebooks: Using Jupyter notebooks in Kubeflow
- Hyperparameter Tuning: Hyperparameter tuning of ML models in Kubeflow
- Pipelines: ML Pipelines in Kubeflow
- Serving: Serving of ML models in Kubeflow
- Training: Training of ML models in Kubeflow
- Miscellaneous: Miscellaneous Kubeflow components

As of v1.0, third-party components include:
- argo: for pipelines
- istio: for kfserving
- knative: for kfserving
- cert-manager: for certificate used in serving
- seldon: for serving (alternative to kfserving)
- minio: store artifacts, for pipelines
- mysql: store metadata, for pipelines and others
- tensorboard: visualization

and projects from Kubeflow include:
- dashboard: a central dashboard
- operators: tf-operator, pytorch-operator
- katib: controller, manager, ui, db
- metadata: controller, db, ui, etc
- pipelines: controller, ui, persistenceagent, etc
- notebook: controller
- kfserving: controller

Dependency versions in v1.0
- istio v1.1.6

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

[Fairing](https://github.com/kubeflow/fairing) allows launching training jobs from python code using
decorator. It can check if the code is running in notebook, and if so, it will convert notebook to
python code using `nbconvert`. Under the hook, the python code will be built into a docker image and
submit to kubeflow.

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

Kubeflow [pipelines](https://github.com/kubeflow/pipelines) describes a machine learning workflow
including all of the components in the workflow and how they combine in the form of a graph.

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

- *Date: 01/12/2019, v0.2*
- *Date: 04/14/2020, v0.3*

[KFServing](https://github.com/kubeflow/kfserving) is a serverless inference solution on Kubernetes,
based on Knative and Istio. KFServing supports TensorFlow, XGBoost, ScikitLearn, PyTorch, ONNX,
TensorRT.

> You can use KFServing to do the following:
> - Provide a Kubernetes Custom Resource Definition for serving ML models on arbitrary frameworks.
> - Encapsulate the complexity of autoscaling, networking, health checking, and server configuration to bring cutting edge serving features like GPU autoscaling, scale to zero, and canary rollouts to your ML deployments.
> - Enable a simple, pluggable, and complete story for your production ML inference server by providing prediction, pre-processing, post-processing and explainability out of the box.

Serving predictors use the following projects. The implementation of xgboostserver, pytorchserver,
etc is simple, where user is required to export models using framework recommended approach, e.g.
save_model (usually pickle, state_dict, etc) then these servers will call load_model and start serving.
- TensorFlow: https://github.com/tensorflow/serving
- ONNX: https://github.com/microsoft/onnxruntime
- TensorRT: https://github.com/NVIDIA/tensorrt-inference-server
- XGBoost: https://github.com/kubeflow/kfserving/tree/0.2.2/python/xgbserver
- PyTorch: https://github.com/kubeflow/kfserving/tree/0.2.2/python/pytorchserver
- ScikitLearn: https://github.com/kubeflow/kfserving/tree/0.2.2/python/sklearnserver

The core of KFServing is a definition of `InferenceService` CRD, with a reconciliation loop that
reconciles Istio & Knative resources.

Note that KFServing in not the only serving solution provided by Kubeflow, others being (all of
these solutions are external to Kubeflow):
- standalone tensorrt inference server: kubeflow just provides a few manifests to deploy trtis.
- seldon: kubeflow provides installation and examples of running seldon on kubernetes.
- tfserving: kubeflow provides manifests and examples to run tfserving on kubernetes, includes
  running tfserving with batch support, and integration with istio.

## Metadata

[Metadata](https://github.com/kubeflow/metadata) is used to track and manage metadata of machine
learning workflows in Kubeflow. It contains a controller, ui, database (e.g. using mysql), etc.
Users interact with Metadata with a SDK.

Metadata wraps around [TFX ML Metadata](https://www.tensorflow.org/tfx/guide/mlmd), which is a low
level library for recording and retrieving metadata associated with ML developer and data scientist
workflows. Kubeflow metadata is a high-level library and a set of services supporting ML Metadata
functionalities. Metadata provides:
- DataSet to capture metadata for a dataset that forms the input into or the output of a component in your workflow.
- Execution to capture metadata for an execution (run) of your ML workflow.
- Metrics to capture metadata for the metrics used to evaluate an ML model.
- Model to capture metadata for an ML model that your workflow produces.

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

# Experiment (v1.0)

*Date: 04/14/2020, v1.0*

## Kubernetes

First, start a vallina Kubernetes. Kubeflow 1.0 only works on Kubernetes 1.14 & 1.15, and a default
storageclass must be available.

```
$ KUBELET_FLAGS='--resolv-conf=/etc/resolv.conf.kubelet' CGROUP_DRIVER=cgroupfs ALLOW_PRIVILEGED=true ./hack/local-up-cluster.sh -O
...
```

Note here Knative is resolving DNS using kube-dns, we need to pass additional parameter to kubelet.
The `resolve.conf.kubelet` file only contains one entry: `nameserver 8.8.8.8`. Without the parameter,
it may not be able to access external name.

```
$ cat /etc/resolv.conf.kubelet
nameserver 8.8.8.8
```

## Installation

Install `kfctl`:

```
$ wget https://github.com/kubeflow/kfctl/releases/download/v1.0.1/kfctl_v1.0.1-0-gf3edb9b_linux.tar.gz
...

$ tar -xvf kfctl_v1.0.1-0-gf3edb9b_linux.tar.gz
...
```

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
export CONFIG_URI="https://raw.githubusercontent.com/kubeflow/manifests/v1.0-branch/kfdef/kfctl_k8s_istio.v1.0.1.yaml"
```

Then run:

```
mkdir -p ${KF_DIR}
cd ${KF_DIR}
kfctl apply -V -f ${CONFIG_URI}
```

Note if prometheus is unable to start due to permission error, we can add the option
`--storage.tsdb.path=/tmp` to prometheus deployment to workaround the problem.

Now check all resources deployed by Kubeflow, under `kubeflow`, `istio`, `knative-serving` and
`cert-manager` namespaces:

<details><summary>kubectl -n kubeflow get all</summary><p>

```
$ kubectl get all -n kubeflow
NAME                                                               READY   STATUS      RESTARTS   AGE
pod/admission-webhook-bootstrap-stateful-set-0                     1/1     Running     0          179m
pod/admission-webhook-deployment-64cb96ddbf-tq8nm                  1/1     Running     0          179m
pod/application-controller-stateful-set-0                          1/1     Running     0          3h
pod/argo-ui-778676df64-5lpc6                                       1/1     Running     0          179m
pod/centraldashboard-7dd7dd685d-j9gqj                              1/1     Running     0          179m
pod/jupyter-web-app-deployment-89789fd5-svx4z                      1/1     Running     0          179m
pod/katib-controller-6b789b6cb5-7l8rp                              1/1     Running     1          179m
pod/katib-db-manager-64f548b47c-gql25                              1/1     Running     7          179m
pod/katib-mysql-57884cb488-z25cl                                   1/1     Running     0          179m
pod/katib-ui-5c5cc6bd77-rtz4t                                      1/1     Running     0          179m
pod/kfserving-controller-manager-0                                 2/2     Running     1          179m
pod/metacontroller-0                                               1/1     Running     0          179m
pod/metadata-db-76c9f78f77-vw9fd                                   1/1     Running     0          179m
pod/metadata-deployment-674fdd976b-zx4p6                           1/1     Running     2          179m
pod/metadata-envoy-deployment-5688989bd6-f87pt                     1/1     Running     0          179m
pod/metadata-grpc-deployment-5579bdc87b-tjvd8                      1/1     Running     9          179m
pod/metadata-ui-9b8cd699d-q99vk                                    1/1     Running     0          179m
pod/minio-755ff748b-fqb84                                          1/1     Running     0          179m
pod/ml-pipeline-79b4f85cbc-sklzs                                   1/1     Running     2          179m
pod/ml-pipeline-ml-pipeline-visualizationserver-5fdffdc5bf-xtl9s   1/1     Running     0          179m
pod/ml-pipeline-persistenceagent-645cb66874-kbb76                  1/1     Running     4          179m
pod/ml-pipeline-scheduledworkflow-6c978b6b85-zf8qm                 1/1     Running     0          179m
pod/ml-pipeline-ui-6995b7bccf-zqn7m                                1/1     Running     0          179m
pod/ml-pipeline-viewer-controller-deployment-8554dc7b9f-qf4lf      1/1     Running     0          179m
pod/mysql-598bc897dc-zp4vr                                         1/1     Running     0          179m
pod/notebook-controller-deployment-7db57b9ccf-t5sbt                1/1     Running     0          179m
pod/profiles-deployment-c44b98f5b-vbhjj                            2/2     Running     0          179m
pod/pytorch-operator-5fd5f94bdd-fjpzl                              1/1     Running     0          179m
pod/seldon-controller-manager-679fc777cd-whfcj                     1/1     Running     0          179m
pod/spark-operatorcrd-cleanup-gw2hx                                0/2     Completed   0          179m
pod/spark-operatorsparkoperator-c7b64b87f-xx852                    1/1     Running     0          179m
pod/spartakus-volunteer-6b767c8d6-b2p88                            1/1     Running     0          179m
pod/tensorboard-6544748d94-jb7wt                                   1/1     Running     0          179m
pod/tf-job-operator-7d7c8fb8bb-zxn6x                               1/1     Running     0          179m
pod/workflow-controller-945c84565-l9qtq                            1/1     Running     0          179m

NAME                                                   TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
service/admission-webhook-service                      ClusterIP   10.0.0.252   <none>        443/TCP             179m
service/application-controller-service                 ClusterIP   10.0.0.44    <none>        443/TCP             3h
service/argo-ui                                        NodePort    10.0.0.220   <none>        80:31093/TCP        179m
service/centraldashboard                               ClusterIP   10.0.0.23    <none>        80/TCP              179m
service/jupyter-web-app-service                        ClusterIP   10.0.0.253   <none>        80/TCP              179m
service/katib-controller                               ClusterIP   10.0.0.2     <none>        443/TCP,8080/TCP    179m
service/katib-db-manager                               ClusterIP   10.0.0.144   <none>        6789/TCP            179m
service/katib-mysql                                    ClusterIP   10.0.0.207   <none>        3306/TCP            179m
service/katib-ui                                       ClusterIP   10.0.0.71    <none>        80/TCP              179m
service/kfserving-controller-manager-metrics-service   ClusterIP   10.0.0.218   <none>        8443/TCP            179m
service/kfserving-controller-manager-service           ClusterIP   10.0.0.225   <none>        443/TCP             179m
service/kfserving-webhook-server-service               ClusterIP   10.0.0.149   <none>        443/TCP             171m
service/metadata-db                                    ClusterIP   10.0.0.241   <none>        3306/TCP            179m
service/metadata-envoy-service                         ClusterIP   10.0.0.202   <none>        9090/TCP            179m
service/metadata-grpc-service                          ClusterIP   10.0.0.247   <none>        8080/TCP            179m
service/metadata-service                               ClusterIP   10.0.0.112   <none>        8080/TCP            179m
service/metadata-ui                                    ClusterIP   10.0.0.132   <none>        80/TCP              179m
service/minio-service                                  ClusterIP   10.0.0.227   <none>        9000/TCP            179m
service/ml-pipeline                                    ClusterIP   10.0.0.205   <none>        8888/TCP,8887/TCP   179m
service/ml-pipeline-ml-pipeline-visualizationserver    ClusterIP   10.0.0.249   <none>        8888/TCP            179m
service/ml-pipeline-tensorboard-ui                     ClusterIP   10.0.0.42    <none>        80/TCP              179m
service/ml-pipeline-ui                                 ClusterIP   10.0.0.4     <none>        80/TCP              179m
service/mysql                                          ClusterIP   10.0.0.171   <none>        3306/TCP            179m
service/notebook-controller-service                    ClusterIP   10.0.0.188   <none>        443/TCP             179m
service/profiles-kfam                                  ClusterIP   10.0.0.208   <none>        8081/TCP            179m
service/pytorch-operator                               ClusterIP   10.0.0.137   <none>        8443/TCP            179m
service/seldon-webhook-service                         ClusterIP   10.0.0.127   <none>        443/TCP             179m
service/tensorboard                                    ClusterIP   10.0.0.3     <none>        9000/TCP            179m
service/tf-job-operator                                ClusterIP   10.0.0.8     <none>        8443/TCP            179m

NAME                                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/admission-webhook-deployment                  1/1     1            1           179m
deployment.apps/argo-ui                                       1/1     1            1           179m
deployment.apps/centraldashboard                              1/1     1            1           179m
deployment.apps/jupyter-web-app-deployment                    1/1     1            1           179m
deployment.apps/katib-controller                              1/1     1            1           179m
deployment.apps/katib-db-manager                              1/1     1            1           179m
deployment.apps/katib-mysql                                   1/1     1            1           179m
deployment.apps/katib-ui                                      1/1     1            1           179m
deployment.apps/metadata-db                                   1/1     1            1           179m
deployment.apps/metadata-deployment                           1/1     1            1           179m
deployment.apps/metadata-envoy-deployment                     1/1     1            1           179m
deployment.apps/metadata-grpc-deployment                      1/1     1            1           179m
deployment.apps/metadata-ui                                   1/1     1            1           179m
deployment.apps/minio                                         1/1     1            1           179m
deployment.apps/ml-pipeline                                   1/1     1            1           179m
deployment.apps/ml-pipeline-ml-pipeline-visualizationserver   1/1     1            1           179m
deployment.apps/ml-pipeline-persistenceagent                  1/1     1            1           179m
deployment.apps/ml-pipeline-scheduledworkflow                 1/1     1            1           179m
deployment.apps/ml-pipeline-ui                                1/1     1            1           179m
deployment.apps/ml-pipeline-viewer-controller-deployment      1/1     1            1           179m
deployment.apps/mysql                                         1/1     1            1           179m
deployment.apps/notebook-controller-deployment                1/1     1            1           179m
deployment.apps/profiles-deployment                           1/1     1            1           179m
deployment.apps/pytorch-operator                              1/1     1            1           179m
deployment.apps/seldon-controller-manager                     1/1     1            1           179m
deployment.apps/spark-operatorsparkoperator                   1/1     1            1           179m
deployment.apps/spartakus-volunteer                           1/1     1            1           179m
deployment.apps/tensorboard                                   1/1     1            1           179m
deployment.apps/tf-job-operator                               1/1     1            1           179m
deployment.apps/workflow-controller                           1/1     1            1           179m

NAME                                                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/admission-webhook-deployment-64cb96ddbf                  1         1         1       179m
replicaset.apps/argo-ui-778676df64                                       1         1         1       179m
replicaset.apps/centraldashboard-7dd7dd685d                              1         1         1       179m
replicaset.apps/jupyter-web-app-deployment-89789fd5                      1         1         1       179m
replicaset.apps/katib-controller-6b789b6cb5                              1         1         1       179m
replicaset.apps/katib-db-manager-64f548b47c                              1         1         1       179m
replicaset.apps/katib-mysql-57884cb488                                   1         1         1       179m
replicaset.apps/katib-ui-5c5cc6bd77                                      1         1         1       179m
replicaset.apps/metadata-db-76c9f78f77                                   1         1         1       179m
replicaset.apps/metadata-deployment-674fdd976b                           1         1         1       179m
replicaset.apps/metadata-envoy-deployment-5688989bd6                     1         1         1       179m
replicaset.apps/metadata-grpc-deployment-5579bdc87b                      1         1         1       179m
replicaset.apps/metadata-ui-9b8cd699d                                    1         1         1       179m
replicaset.apps/minio-755ff748b                                          1         1         1       179m
replicaset.apps/ml-pipeline-79b4f85cbc                                   1         1         1       179m
replicaset.apps/ml-pipeline-ml-pipeline-visualizationserver-5fdffdc5bf   1         1         1       179m
replicaset.apps/ml-pipeline-persistenceagent-645cb66874                  1         1         1       179m
replicaset.apps/ml-pipeline-scheduledworkflow-6c978b6b85                 1         1         1       179m
replicaset.apps/ml-pipeline-ui-6995b7bccf                                1         1         1       179m
replicaset.apps/ml-pipeline-viewer-controller-deployment-8554dc7b9f      1         1         1       179m
replicaset.apps/mysql-598bc897dc                                         1         1         1       179m
replicaset.apps/notebook-controller-deployment-7db57b9ccf                1         1         1       179m
replicaset.apps/profiles-deployment-c44b98f5b                            1         1         1       179m
replicaset.apps/pytorch-operator-5fd5f94bdd                              1         1         1       179m
replicaset.apps/seldon-controller-manager-679fc777cd                     1         1         1       179m
replicaset.apps/spark-operatorsparkoperator-c7b64b87f                    1         1         1       179m
replicaset.apps/spartakus-volunteer-6b767c8d6                            1         1         1       179m
replicaset.apps/tensorboard-6544748d94                                   1         1         1       179m
replicaset.apps/tf-job-operator-7d7c8fb8bb                               1         1         1       179m
replicaset.apps/workflow-controller-945c84565                            1         1         1       179m

NAME                                                        READY   AGE
statefulset.apps/admission-webhook-bootstrap-stateful-set   1/1     179m
statefulset.apps/application-controller-stateful-set        1/1     3h
statefulset.apps/kfserving-controller-manager               1/1     179m
statefulset.apps/metacontroller                             1/1     179m

NAME                                  COMPLETIONS   DURATION   AGE
job.batch/spark-operatorcrd-cleanup   1/1           5m22s      179m
```

</p></details></br>

<details><summary>kubectl -n istio-system get all</summary><p>

```
 kubectl -n istio-system get all
NAME                                            READY   STATUS      RESTARTS   AGE
pod/cluster-local-gateway-748f94c9ff-6plt7      1/1     Running     0          3h2m
pod/grafana-67c69bb567-7h7m5                    1/1     Running     0          3h2m
pod/istio-citadel-67697b6697-ld7j9              1/1     Running     0          3h2m
pod/istio-cleanup-secrets-1.1.6-jdcbf           0/1     Completed   0          3h2m
pod/istio-egressgateway-7dbbb87698-8nr26        1/1     Running     0          3h2m
pod/istio-galley-7bffd57ff4-bsfw4               1/1     Running     0          3h2m
pod/istio-grafana-post-install-1.1.6-4kxp9      0/1     Completed   0          3h2m
pod/istio-ingressgateway-565b894b5f-cnn9f       1/1     Running     0          3h2m
pod/istio-pilot-6dd5b8f74c-92wpt                2/2     Running     0          3h2m
pod/istio-policy-7f8bb87857-xxbpw               2/2     Running     1          3h2m
pod/istio-security-post-install-1.1.6-26l7h     0/1     Completed   0          3h2m
pod/istio-sidecar-injector-fd5875568-mbp26      1/1     Running     0          3h2m
pod/istio-telemetry-8759dc6b7-9tlth             2/2     Running     1          3h2m
pod/istio-tracing-5d8f57c8ff-j44wg              1/1     Running     0          3h2m
pod/kfserving-ingressgateway-598c9fd4ff-slbp7   1/1     Running     0          3h2m
pod/kiali-d4d886dd7-xnshh                       1/1     Running     0          3h2m
pod/prometheus-557494c89-9kpgf                  1/1     Running     0          97m

NAME                               TYPE           CLUSTER-IP   EXTERNAL-IP   PORT(S)                                                                                                                                                                                   AGE
service/cluster-local-gateway      ClusterIP      10.0.0.152   <none>        80/TCP,443/TCP,31400/TCP,15011/TCP,8060/TCP,15029/TCP,15030/TCP,15031/TCP,15032/TCP                                                                                                       3h2m
service/grafana                    ClusterIP      10.0.0.154   <none>        3000/TCP                                                                                                                                                                                  3h2m
service/istio-citadel              ClusterIP      10.0.0.142   <none>        8060/TCP,15014/TCP                                                                                                                                                                        3h2m
service/istio-egressgateway        ClusterIP      10.0.0.98    <none>        80/TCP,443/TCP,15443/TCP                                                                                                                                                                  3h2m
service/istio-galley               ClusterIP      10.0.0.211   <none>        443/TCP,15014/TCP,9901/TCP                                                                                                                                                                3h2m
service/istio-ingressgateway       NodePort       10.0.0.111   <none>        15020:30714/TCP,80:31380/TCP,443:31390/TCP,31400:31400/TCP,15029:32290/TCP,15030:30910/TCP,15031:30880/TCP,15032:32406/TCP,15443:31986/TCP                                                3h2m
service/istio-pilot                ClusterIP      10.0.0.223   <none>        15010/TCP,15011/TCP,8080/TCP,15014/TCP                                                                                                                                                    3h2m
service/istio-policy               ClusterIP      10.0.0.236   <none>        9091/TCP,15004/TCP,15014/TCP                                                                                                                                                              3h2m
service/istio-sidecar-injector     ClusterIP      10.0.0.56    <none>        443/TCP                                                                                                                                                                                   3h2m
service/istio-telemetry            ClusterIP      10.0.0.226   <none>        9091/TCP,15004/TCP,15014/TCP,42422/TCP                                                                                                                                                    3h2m
service/jaeger-agent               ClusterIP      None         <none>        5775/UDP,6831/UDP,6832/UDP                                                                                                                                                                3h2m
service/jaeger-collector           ClusterIP      10.0.0.136   <none>        14267/TCP,14268/TCP                                                                                                                                                                       3h2m
service/jaeger-query               ClusterIP      10.0.0.50    <none>        16686/TCP                                                                                                                                                                                 3h2m
service/kfserving-ingressgateway   LoadBalancer   10.0.0.34    <pending>     15020:31090/TCP,80:32380/TCP,443:32390/TCP,31400:32400/TCP,15011:30496/TCP,8060:32671/TCP,853:30632/TCP,15029:30325/TCP,15030:31785/TCP,15031:30024/TCP,15032:32554/TCP,15443:32636/TCP   3h2m
service/kiali                      ClusterIP      10.0.0.46    <none>        20001/TCP                                                                                                                                                                                 3h2m
service/prometheus                 ClusterIP      10.0.0.113   <none>        9090/TCP                                                                                                                                                                                  3h2m
service/tracing                    ClusterIP      10.0.0.143   <none>        80/TCP                                                                                                                                                                                    3h2m
service/zipkin                     ClusterIP      10.0.0.83    <none>        9411/TCP                                                                                                                                                                                  3h2m

NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/cluster-local-gateway      1/1     1            1           3h2m
deployment.apps/grafana                    1/1     1            1           3h2m
deployment.apps/istio-citadel              1/1     1            1           3h2m
deployment.apps/istio-egressgateway        1/1     1            1           3h2m
deployment.apps/istio-galley               1/1     1            1           3h2m
deployment.apps/istio-ingressgateway       1/1     1            1           3h2m
deployment.apps/istio-pilot                1/1     1            1           3h2m
deployment.apps/istio-policy               1/1     1            1           3h2m
deployment.apps/istio-sidecar-injector     1/1     1            1           3h2m
deployment.apps/istio-telemetry            1/1     1            1           3h2m
deployment.apps/istio-tracing              1/1     1            1           3h2m
deployment.apps/kfserving-ingressgateway   1/1     1            1           3h2m
deployment.apps/kiali                      1/1     1            1           3h2m
deployment.apps/prometheus                 1/1     1            1           3h2m

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/cluster-local-gateway-748f94c9ff      1         1         1       3h2m
replicaset.apps/grafana-67c69bb567                    1         1         1       3h2m
replicaset.apps/istio-citadel-67697b6697              1         1         1       3h2m
replicaset.apps/istio-egressgateway-7dbbb87698        1         1         1       3h2m
replicaset.apps/istio-galley-7bffd57ff4               1         1         1       3h2m
replicaset.apps/istio-ingressgateway-565b894b5f       1         1         1       3h2m
replicaset.apps/istio-pilot-6dd5b8f74c                1         1         1       3h2m
replicaset.apps/istio-policy-7f8bb87857               1         1         1       3h2m
replicaset.apps/istio-sidecar-injector-fd5875568      1         1         1       3h2m
replicaset.apps/istio-telemetry-8759dc6b7             1         1         1       3h2m
replicaset.apps/istio-tracing-5d8f57c8ff              1         1         1       3h2m
replicaset.apps/kfserving-ingressgateway-598c9fd4ff   1         1         1       3h2m
replicaset.apps/kiali-d4d886dd7                       1         1         1       3h2m
replicaset.apps/prometheus-557494c89                  1         1         1       97m
replicaset.apps/prometheus-75dbd8c479                 0         0         0       98m
replicaset.apps/prometheus-7c64dd5b87                 0         0         0       132m
replicaset.apps/prometheus-d8d46c5b5                  0         0         0       3h2m

NAME                                                           REFERENCE                             TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/cluster-local-gateway      Deployment/cluster-local-gateway      <unknown>/80%   1         5         1          3h2m
horizontalpodautoscaler.autoscaling/istio-egressgateway        Deployment/istio-egressgateway        <unknown>/80%   1         5         1          3h2m
horizontalpodautoscaler.autoscaling/istio-ingressgateway       Deployment/istio-ingressgateway       <unknown>/80%   1         5         1          3h2m
horizontalpodautoscaler.autoscaling/istio-pilot                Deployment/istio-pilot                <unknown>/80%   1         5         1          3h2m
horizontalpodautoscaler.autoscaling/istio-policy               Deployment/istio-policy               <unknown>/80%   1         5         1          3h2m
horizontalpodautoscaler.autoscaling/istio-telemetry            Deployment/istio-telemetry            <unknown>/80%   1         5         1          3h2m
horizontalpodautoscaler.autoscaling/kfserving-ingressgateway   Deployment/kfserving-ingressgateway   <unknown>/80%   1         5         1          3h2m

NAME                                          COMPLETIONS   DURATION   AGE
job.batch/istio-cleanup-secrets-1.1.6         1/1           11s        3h2m
job.batch/istio-grafana-post-install-1.1.6    1/1           20s        3h2m
job.batch/istio-security-post-install-1.1.6   1/1           19s        3h2m
```

</p></details></br>

<details><summary>kubectl -n knative-serving get all</summary><p>

```
$ kubectl -n knative-serving get all
NAME                                    READY   STATUS    RESTARTS   AGE
pod/activator-cfc66dc7-7kfqx            2/2     Running   0          3h2m
pod/autoscaler-6cc8bc459b-bfv22         2/2     Running   2          3h2m
pod/autoscaler-hpa-766c77c5f4-x76w4     1/1     Running   0          3h2m
pod/controller-7769b4c845-x68wq         1/1     Running   0          3h2m
pod/networking-istio-7fd5c6bd64-9bghz   1/1     Running   0          3h2m
pod/webhook-775db85f78-thgm2            1/1     Running   0          3h2m

NAME                        TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                     AGE
service/activator-service   ClusterIP   10.0.0.73    <none>        80/TCP,81/TCP,9090/TCP      3h2m
service/autoscaler          ClusterIP   10.0.0.158   <none>        8080/TCP,9090/TCP,443/TCP   3h2m
service/controller          ClusterIP   10.0.0.27    <none>        9090/TCP                    3h2m
service/webhook             ClusterIP   10.0.0.15    <none>        443/TCP                     3h2m

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/activator          1/1     1            1           3h2m
deployment.apps/autoscaler         1/1     1            1           3h2m
deployment.apps/autoscaler-hpa     1/1     1            1           3h2m
deployment.apps/controller         1/1     1            1           3h2m
deployment.apps/networking-istio   1/1     1            1           3h2m
deployment.apps/webhook            1/1     1            1           3h2m

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/activator-cfc66dc7            1         1         1       3h2m
replicaset.apps/autoscaler-6cc8bc459b         1         1         1       3h2m
replicaset.apps/autoscaler-hpa-766c77c5f4     1         1         1       3h2m
replicaset.apps/controller-7769b4c845         1         1         1       3h2m
replicaset.apps/networking-istio-7fd5c6bd64   1         1         1       3h2m
replicaset.apps/webhook-775db85f78            1         1         1       3h2m

NAME                                            REFERENCE              TARGETS          MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/activator   Deployment/activator   <unknown>/100%   1         20        1          3h2m
```

</p></details></br>

<details><summary>kubectl -n cert-manager get all</summary><p>

```
$ kubectl -n cert-manager get all
NAME                                          READY   STATUS    RESTARTS   AGE
pod/cert-manager-564b4bffd7-nflhp             1/1     Running   0          3h4m
pod/cert-manager-cainjector-596986f94-6h9nt   1/1     Running   0          3h4m
pod/cert-manager-webhook-755d75845c-tkxxp     1/1     Running   2          3h4m

NAME                           TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
service/cert-manager           ClusterIP   10.0.0.161   <none>        9402/TCP   3h4m
service/cert-manager-webhook   ClusterIP   10.0.0.21    <none>        443/TCP    3h4m

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/cert-manager              1/1     1            1           3h4m
deployment.apps/cert-manager-cainjector   1/1     1            1           3h4m
deployment.apps/cert-manager-webhook      1/1     1            1           3h4m

NAME                                                DESIRED   CURRENT   READY   AGE
replicaset.apps/cert-manager-564b4bffd7             1         1         1       3h4m
replicaset.apps/cert-manager-cainjector-596986f94   1         1         1       3h4m
replicaset.apps/cert-manager-webhook-755d75845c     1         1         1       3h4m
```

</p></details></br>

<details><summary>All CRDs (a total of 94 CRDs)</summary><p>

```
$ kubectl get crds
NAME                                                 CREATED AT
adapters.config.istio.io                             2020-04-15T02:20:56Z
apikeys.config.istio.io                              2020-04-15T02:20:56Z
applications.app.k8s.io                              2020-04-15T02:20:58Z
attributemanifests.config.istio.io                   2020-04-15T02:20:56Z
authorizations.config.istio.io                       2020-04-15T02:20:56Z
bypasses.config.istio.io                             2020-04-15T02:20:56Z
certificaterequests.cert-manager.io                  2020-04-15T02:20:59Z
certificates.cert-manager.io                         2020-04-15T02:20:59Z
certificates.certmanager.k8s.io                      2020-04-15T02:20:56Z
certificates.networking.internal.knative.dev         2020-04-15T02:21:44Z
challenges.acme.cert-manager.io                      2020-04-15T02:20:59Z
challenges.certmanager.k8s.io                        2020-04-15T02:20:56Z
checknothings.config.istio.io                        2020-04-15T02:20:56Z
circonuses.config.istio.io                           2020-04-15T02:20:56Z
cloudwatches.config.istio.io                         2020-04-15T02:20:56Z
clusterissuers.cert-manager.io                       2020-04-15T02:20:59Z
clusterissuers.certmanager.k8s.io                    2020-04-15T02:20:56Z
clusterrbacconfigs.rbac.istio.io                     2020-04-15T02:20:56Z
compositecontrollers.metacontroller.k8s.io           2020-04-15T02:21:42Z
configurations.serving.knative.dev                   2020-04-15T02:21:44Z
controllerrevisions.metacontroller.k8s.io            2020-04-15T02:21:42Z
decoratorcontrollers.metacontroller.k8s.io           2020-04-15T02:21:42Z
deniers.config.istio.io                              2020-04-15T02:20:56Z
destinationrules.networking.istio.io                 2020-04-15T02:20:56Z
dogstatsds.config.istio.io                           2020-04-15T02:20:56Z
edges.config.istio.io                                2020-04-15T02:20:56Z
envoyfilters.networking.istio.io                     2020-04-15T02:20:56Z
experiments.kubeflow.org                             2020-04-15T02:21:45Z
fluentds.config.istio.io                             2020-04-15T02:20:56Z
gateways.networking.istio.io                         2020-04-15T02:20:56Z
handlers.config.istio.io                             2020-04-15T02:20:56Z
httpapispecbindings.config.istio.io                  2020-04-15T02:20:56Z
httpapispecs.config.istio.io                         2020-04-15T02:20:56Z
images.caching.internal.knative.dev                  2020-04-15T02:21:44Z
inferenceservices.serving.kubeflow.org               2020-04-15T02:21:45Z
ingresses.networking.internal.knative.dev            2020-04-15T02:21:44Z
instances.config.istio.io                            2020-04-15T02:20:56Z
issuers.cert-manager.io                              2020-04-15T02:20:59Z
issuers.certmanager.k8s.io                           2020-04-15T02:20:56Z
kubernetesenvs.config.istio.io                       2020-04-15T02:20:56Z
kuberneteses.config.istio.io                         2020-04-15T02:20:56Z
listcheckers.config.istio.io                         2020-04-15T02:20:56Z
listentries.config.istio.io                          2020-04-15T02:20:56Z
logentries.config.istio.io                           2020-04-15T02:20:56Z
memquotas.config.istio.io                            2020-04-15T02:20:56Z
meshpolicies.authentication.istio.io                 2020-04-15T02:20:56Z
metrics.autoscaling.internal.knative.dev             2020-04-15T02:21:44Z
metrics.config.istio.io                              2020-04-15T02:20:56Z
noops.config.istio.io                                2020-04-15T02:20:56Z
notebooks.kubeflow.org                               2020-04-15T02:21:44Z
opas.config.istio.io                                 2020-04-15T02:20:56Z
orders.acme.cert-manager.io                          2020-04-15T02:20:59Z
orders.certmanager.k8s.io                            2020-04-15T02:20:56Z
podautoscalers.autoscaling.internal.knative.dev      2020-04-15T02:21:44Z
poddefaults.kubeflow.org                             2020-04-15T02:21:42Z
policies.authentication.istio.io                     2020-04-15T02:20:56Z
profiles.kubeflow.org                                2020-04-15T02:21:48Z
prometheuses.config.istio.io                         2020-04-15T02:20:56Z
pytorchjobs.kubeflow.org                             2020-04-15T02:21:44Z
quotas.config.istio.io                               2020-04-15T02:20:56Z
quotaspecbindings.config.istio.io                    2020-04-15T02:20:56Z
quotaspecs.config.istio.io                           2020-04-15T02:20:56Z
rbacconfigs.rbac.istio.io                            2020-04-15T02:20:56Z
rbacs.config.istio.io                                2020-04-15T02:20:56Z
redisquotas.config.istio.io                          2020-04-15T02:20:57Z
reportnothings.config.istio.io                       2020-04-15T02:20:57Z
revisions.serving.knative.dev                        2020-04-15T02:21:44Z
routes.serving.knative.dev                           2020-04-15T02:21:44Z
rules.config.istio.io                                2020-04-15T02:20:57Z
scheduledworkflows.kubeflow.org                      2020-04-15T02:21:47Z
seldondeployments.machinelearning.seldon.io          2020-04-15T02:21:48Z
serverlessservices.networking.internal.knative.dev   2020-04-15T02:21:44Z
serviceentries.networking.istio.io                   2020-04-15T02:20:57Z
servicerolebindings.rbac.istio.io                    2020-04-15T02:20:57Z
serviceroles.rbac.istio.io                           2020-04-15T02:20:57Z
services.serving.knative.dev                         2020-04-15T02:21:44Z
sidecars.networking.istio.io                         2020-04-15T02:20:57Z
signalfxs.config.istio.io                            2020-04-15T02:20:57Z
solarwindses.config.istio.io                         2020-04-15T02:20:57Z
stackdrivers.config.istio.io                         2020-04-15T02:20:57Z
statsds.config.istio.io                              2020-04-15T02:20:57Z
stdios.config.istio.io                               2020-04-15T02:20:57Z
suggestions.kubeflow.org                             2020-04-15T02:21:45Z
templates.config.istio.io                            2020-04-15T02:20:57Z
tfjobs.kubeflow.org                                  2020-04-15T02:21:45Z
tracespans.config.istio.io                           2020-04-15T02:20:57Z
trials.kubeflow.org                                  2020-04-15T02:21:45Z
viewers.kubeflow.org                                 2020-04-15T02:21:47Z
virtualservices.networking.istio.io                  2020-04-15T02:20:57Z
workflows.argoproj.io                                2020-04-15T02:21:42Z
zipkins.config.istio.io                              2020-04-15T02:20:57Z
```
</p></details></br>

<details><summary>CRDs in Kubeflow</summary><p>

```
$ kubectl get crds | grep kubeflow.org
experiments.kubeflow.org                             2020-04-15T02:21:45Z
inferenceservices.serving.kubeflow.org               2020-04-15T02:21:45Z
notebooks.kubeflow.org                               2020-04-15T02:21:44Z
poddefaults.kubeflow.org                             2020-04-15T02:21:42Z
profiles.kubeflow.org                                2020-04-15T02:21:48Z
pytorchjobs.kubeflow.org                             2020-04-15T02:21:44Z
scheduledworkflows.kubeflow.org                      2020-04-15T02:21:47Z
suggestions.kubeflow.org                             2020-04-15T02:21:45Z
tfjobs.kubeflow.org                                  2020-04-15T02:21:45Z
trials.kubeflow.org                                  2020-04-15T02:21:45Z
viewers.kubeflow.org                                 2020-04-15T02:21:47Z
```

</p></details></br>

## KFServing

The experiment follows the full kubeflow v1.0 installation, with kfserving version 0.2.2.

Run kfserving tensorflow example (make sure VPN is connected, as kubeflow will download model from gcs):

```
$ gco 0.2.2
...

$ kubectl label ns default serving.kubeflow.org/inferenceservice=enabled
namespace/default labeled

# Under "kubeflow/kfserving" repository.
$ kubectl apply -f docs/samples/tensorflow/tensorflow.yaml
inferenceservice.serving.kubeflow.org/flowers-sample created
```

After deploying the inference service, kfserving starts bootstrapping, with a pod running the inference server.

```
$ kubectl get inferenceservices
NAME             URL   READY   DEFAULT TRAFFIC   CANARY TRAFFIC   AGE
flowers-sample         False                                      48s

$ kubectl get pods
NAME                                                              READY   STATUS     RESTARTS   AGE
flowers-sample-predictor-default-nk6ct-deployment-5bcf9998ph967   0/2     Init:0/1   0          2s

$ kubectl logs flowers-sample-predictor-default-nk6ct-deployment-5bcf9998ph967 -c storage-initializer
[I 200415 07:48:23 initializer-entrypoint:13] Initializing, args: src_uri [gs://kfserving-samples/models/tensorflow/flowers] dest_path[ [/mnt/models]
[I 200415 07:48:23 storage:35] Copying contents of gs://kfserving-samples/models/tensorflow/flowers to local
[I 200415 07:48:26 _metadata:95] Compute Engine Metadata server unavailable onattempt 1 of 3
[I 200415 07:48:29 _metadata:95] Compute Engine Metadata server unavailable onattempt 2 of 3
[I 200415 07:48:32 _metadata:95] Compute Engine Metadata server unavailable onattempt 3 of 3
[I 200415 07:48:35 storage:111] Downloading: /mnt/models/0001/saved_model.pb
[I 200415 07:48:51 storage:111] Downloading: /mnt/models/0001/variables/variables.data-00000-of-00001
```

After a while, when bootstrapping finished, kfserving controller will create the following resources.
The Knative service now changes to Ready state.

<details><summary>kubectl get all -n default</summary><p>

```
$ kubectl get all
NAME                                                                  READY   STATUS        RESTARTS   AGE
pod/flowers-sample-predictor-default-qxdmb-deployment-6b9bccb75hwmq   1/2     Terminating   0          2m59s

NAME                                                     TYPE           CLUSTER-IP   EXTERNAL-IP                                            PORT(S)                             AGE
service/flowers-sample-predictor-default                 ExternalName   <none>       cluster-local-gateway.istio-system.svc.cluster.local   <none>                              105s
service/flowers-sample-predictor-default-qxdmb           ClusterIP      10.0.0.42    <none>                                                 80/TCP                              2m59s
service/flowers-sample-predictor-default-qxdmb-private   ClusterIP      10.0.0.13    <none>                                                 80/TCP,9090/TCP,9091/TCP,8022/TCP   2m59s
service/kubernetes                                       ClusterIP      10.0.0.1     <none>                                                 443/TCP                             19m

NAME                                                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/flowers-sample-predictor-default-qxdmb-deployment   0/0     0            0           2m59s

NAME                                                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/flowers-sample-predictor-default-qxdmb-deployment-6b9bccb7f9   0         0         0       2m59s

NAME                                                         URL                                                           READY   REASON
route.serving.knative.dev/flowers-sample-predictor-default   http://flowers-sample-predictor-default.default.example.com   True

NAME                                                           URL                                                           LATESTCREATED                            LATESTREADY                              READY   REASON
service.serving.knative.dev/flowers-sample-predictor-default   http://flowers-sample-predictor-default.default.example.com   flowers-sample-predictor-default-qxdmb   flowers-sample-predictor-default-qxdmb   True

NAME                                                                  CONFIG NAME                        K8S SERVICE NAME                         GENERATION   READY   REASON
revision.serving.knative.dev/flowers-sample-predictor-default-qxdmb   flowers-sample-predictor-default   flowers-sample-predictor-default-qxdmb   1            True

NAME                                                                 LATESTCREATED                            LATESTREADY                              READY   REASON
configuration.serving.knative.dev/flowers-sample-predictor-default   flowers-sample-predictor-default-qxdmb   flowers-sample-predictor-default-qxdmb   True
```

</p></details></br>

Predictor is the deployement running serving instance, here the image is `tensorflow/serving`.

```
$ kubectl get deployment flowers-sample-predictor-default-thr7x-deployment -o yaml | grep image
        image: index.docker.io/tensorflow/serving@sha256:f7e59a29cbc17a6b507751cddde37bccad4407c05ebf2c13b8e6ccb7d2e9affb
        imagePullPolicy: IfNotPresent
        image: gcr.io/knative-releases/knative.dev/serving/cmd/queue@sha256:792f6945c7bc73a49a470a5b955c39c8bd174705743abf5fb71aa0f4c04128eb
        imagePullPolicy: IfNotPresent
```

Since kubeflow uses serverless infrastructure, after a while, the single pod will be deleted (but the
kf inference service is still healthy):

```
$ kubectl get pods -n default
No resources found.

$ kubectl get inferenceservices
NAME             URL                                                                  READY   DEFAULT TRAFFIC   CANARY TRAFFIC   AGE
flowers-sample   http://flowers-sample.default.example.com/v1/models/flowers-sample   True    100                                7m17s
```

To run inference:

```
MODEL_NAME=flowers-sample
INPUT_PATH=@./docs/samples/tensorflow/input.json
# The ingress gateway is changed to "kfserving-ingressgateway"
# CLUSTER_IP=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.clusterIP}')
CLUSTER_IP=$(kubectl -n istio-system get service kfserving-ingressgateway -o jsonpath='{.spec.clusterIP}')
SERVICE_HOSTNAME=$(kubectl get inferenceservice ${MODEL_NAME} -o jsonpath='{.status.url}' | cut -d "/" -f 3)

$ curl -v -H "Host: ${SERVICE_HOSTNAME}" http://$CLUSTER_IP/v1/models/$MODEL_NAME:predict -d $INPUT_PATH
*   Trying 10.0.0.238...
* TCP_NODELAY set
* Connected to 10.0.0.238 (10.0.0.238) port 80 (#0)
> POST /v1/models/flowers-sample:predict HTTP/1.1
> Host: flowers-sample.default.example.com
> User-Agent: curl/7.58.0
> Accept: */*
> Content-Length: 16201
> Content-Type: application/x-www-form-urlencoded
> Expect: 100-continue
>
< HTTP/1.1 100 Continue
* We are completely uploaded and fine
< HTTP/1.1 200 OK
< content-length: 220
< content-type: application/json
< date: Wed, 15 Apr 2020 13:19:47 GMT
< x-envoy-upstream-service-time: 425
< server: istio-envoy
<
{
    "predictions": [
        {
            "scores": [0.999114931, 9.2098875e-05, 0.000136786344, 0.000337257865, 0.000300532876, 1.8481378e-05],
            "prediction": 0,
            "key": "   1"
        }
    ]
* Connection #0 to host 10.0.0.238 left intact
}
```

This will bring up a new Pod and run the predictions.

# Experiments

## Standalone KFServing v0.3

*Date: 04/14/2020, v0.3*

The experiment follows a standalone installation of kfserving.

**Install Istio @1.5.1**

To install Istio (based on [getting started link](https://istio.io/docs/setup/getting-started/)):

```
$ curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.5.1 sh -
...

$ istioctl verify-install
...

$ istioctl manifest apply --set profile=demo
- Applying manifest for component Base...
✔ Finished applying manifest for component Base.
- Applying manifest for component Pilot...
✔ Finished applying manifest for component Pilot.
  Waiting for resources to become ready...
  Waiting for resources to become ready...
  Waiting for resources to become ready...
  Waiting for resources to become ready...
- Applying manifest for component IngressGateways...
- Applying manifest for component EgressGateways...
- Applying manifest for component AddonComponents...
✔ Finished applying manifest for component EgressGateways.
✔ Finished applying manifest for component IngressGateways.
✔ Finished applying manifest for component AddonComponents.

✔ Installation complete
```

**Install Knative @0.13.0**

To install Knative (based on [install link](https://knative.dev/docs/install/any-kubernetes-cluster/)):

```
$ kubectl apply --filename https://github.com/knative/serving/releases/download/v0.13.0/serving-crds.yaml
customresourcedefinition.apiextensions.k8s.io/certificates.networking.internal.knative.dev created
customresourcedefinition.apiextensions.k8s.io/configurations.serving.knative.dev created
customresourcedefinition.apiextensions.k8s.io/ingresses.networking.internal.knative.dev created
customresourcedefinition.apiextensions.k8s.io/metrics.autoscaling.internal.knative.dev created
customresourcedefinition.apiextensions.k8s.io/podautoscalers.autoscaling.internal.knative.dev created
customresourcedefinition.apiextensions.k8s.io/revisions.serving.knative.dev created
customresourcedefinition.apiextensions.k8s.io/routes.serving.knative.dev created
customresourcedefinition.apiextensions.k8s.io/serverlessservices.networking.internal.knative.dev created
customresourcedefinition.apiextensions.k8s.io/services.serving.knative.dev created
customresourcedefinition.apiextensions.k8s.io/images.caching.internal.knative.dev created

$ kubectl apply --filename https://github.com/knative/serving/releases/download/v0.13.0/serving-core.yaml
...

$ kubectl apply --filename https://github.com/knative/serving/releases/download/v0.13.0/serving-istio.yaml
clusterrole.rbac.authorization.k8s.io/knative-serving-istio created
gateway.networking.istio.io/knative-ingress-gateway created
gateway.networking.istio.io/cluster-local-gateway created
configmap/config-istio created
deployment.apps/networking-istio created

$ kubectl apply --filename https://github.com/knative/serving/releases/download/v0.13.0/serving-default-domain.yaml
job.batch/default-domain created
service/default-domain-service created
```

KFServing requires `cert-manager` with Knative (based on [cert-manager installation](https://cert-manager.io/docs/installation/kubernetes/)):

```
# NOTE: make sure to install newer version of cert-manager. For cert-manager version 0.6.1, we need
# to change "cert-manager.io/v1alpha2" to "certmanager.k8s.io/v1alpha1" in kfserving.yaml below, which
# is an older version of cert-manager API. In addition, older version uses apps/v1beta1, which is not
# supported in Kubernetes 1.18.
$ kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v0.14.2/cert-manager.yaml
customresourcedefinition.apiextensions.k8s.io/certificaterequests.cert-manager.io created
customresourcedefinition.apiextensions.k8s.io/certificates.cert-manager.io created
customresourcedefinition.apiextensions.k8s.io/challenges.acme.cert-manager.io created
customresourcedefinition.apiextensions.k8s.io/clusterissuers.cert-manager.io created
customresourcedefinition.apiextensions.k8s.io/issuers.cert-manager.io created
customresourcedefinition.apiextensions.k8s.io/orders.acme.cert-manager.io created

$ kubectl apply --filename https://github.com/knative/serving/releases/download/v0.13.0/serving-cert-manager.yaml
...
```

**Install KFServing @0.3.0**

To install KFServing (based on [install kfserving](https://www.kubeflow.org/docs/components/serving/kfserving/)):

```
$ kubectl apply -f https://raw.githubusercontent.com/kubeflow/kfserving/master/install/v0.3.0/kfserving.yaml
...
```
