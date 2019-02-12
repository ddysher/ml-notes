<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Design & Usage](#design--usage)
  - [Architecture](#architecture)
  - [API & Usage](#api--usage)
  - [Storage](#storage)
  - [Resources](#resources)
  - [Others](#others)
- [Components](#components)
- [Experiment](#experiment)
  - [Installation](#installation)
  - [Run experiment (census)](#run-experiment-census)
  - [Run experiment (census hyper, dist, etc)](#run-experiment-census-hyper-dist-etc)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 07/07/2018, v1.2.3*
- *Date: 10/01/2018, v1.2.3*

[RiseML](https://docs.riseml.com/) is a commercial AI platform (not open source) on top of Kubernetes.
It provides free community edition. As of v1.0, only training & user management are supported.

# Design & Usage

## Architecture

Researchers using RiseML think in terms of experiments that train a model. Under the hood, RiseML
takes care of executing these experiments on the infrastructure in a robust manner, including deciding
on which nodes specific parts of an experiment are executed.

A RiseML cluster consists of a hardware layer with a number of nodes and GPUs, a Kubernetes layer
that orchestrates machine learning jobs and a RiseML layer that manages experiments and turns them
into Kubernetes jobs. Typically, clusters also have storage systems configured for training and
model data.

The RiseML layer consists of multiple components which also run on top of Kubernetes next to all
machine learning jobs. For example, RiseML takes care of versioning, gathering logs, and tracking
the state of each experiment. This is the core function of RiseML. On top RiseML provides a REST
API that can be either acceessed programmatically or via the RiseML client.

All experiments on the RiseML cluster run in containers.

**Deployment Caveats**

- We recommend to explicitly label one node as system node, where the riseml components like database
  and git server will run (riseml has around 10 components).
- We recommend to label one node as a build node, where container images will be built. This allows
  Kubernetes to re-use the local build cache (each time we train a model, a training image will be
  built first).

**Concepts**

- User
- Project
- Experiment
- Experiment Set
- Job

## API & Usage

RiseML is installed via the following command:

```
helm repo add riseml-charts https://cdn.riseml.com/helm-charts
helm install riseml-charts/riseml --name riseml --namespace riseml -f riseml-config.yaml
```

where the minimal `riseml-config.yaml` looks like:

```yaml
accountKey: hpy7zpjp1yk4r17zsd5xze7jsp4qc1qu
adminApiKey: yourSecretApiKeyYouWantToUse1234
adminEmail: deyuan.deng@gmail.com
minio:
  enabled: true
  secretKey: mlriseapikey
nfsProvisioner:
  enabled: true
  path: /tmp/risemlnfs
nodeSelectors:
  system:
    riseml.com/system-node: "true"
  imageBuilder:
    riseml.com/build-node: "true"
```

RiseML has its own yaml API definition, e.g. for hyperparameter tuning, the following config is used:

```yaml
project: ai-toaster
train:
  resources:
    cpus: 2
    mem: 4096
    gpus: 2
  parameters:
    lr:
      - 0.0001
      - 0.001
    lr-decay:
      - 1e-6
      - 1e-7
    epochs:
      - 20
      - 30
  concurrency: 2
  image:
    name: nvidia/cuda:8.0-cudnn7-runtime
  run: >-
    python train_model.py --num-layers {{num-layers}}
                          --learning-rate {{learning-rate}}
                          --training-data /data/ai-toaster
```

## Storage

RiseML requires at least two persistence volumes (PV):
- data: where your training data resides
- output: where experiments write their output in user and project-specific directories

You can optionally use at least one physical volume with enough capacity for each RiseML component:
- database: to persist your database data (required for production)
- git: to persist versioned experiment code (required for production)
- log: to persist job logs
- registry: to persist registry images

You can use any volume type that supports `ReadWriteMany` access. The two volume will be mounted into
training container as `/data` and `/output` directory. Application code is required to read data from
`/data`, and save checkpoint, model, logs, etc, to the `/output` directory.

RiseML shares data and output PVs across multi-user and multi-experiment. The output of each experiment
is **in a separate directory, grouped by user**, so you cannot accidentally overwrite or mix it with
another experiment's output.

Let's assume your code writes a model to the file `/output/toaster.model`. Also, you mounted the output
folder that was configured while installing riseml on `/shared_output` on your local workstation.
Then you can read `/shared_output` on your local workstation to retrieve result; similiarly, you can
mount `/shared_data` to copy data into runtime. Exactly how this sharing works differ from specific
setup, e.g. for nfs, you simply read/write data to nfs exported directory.

For distributed training, OUTPUT_DIR directory (i.e. `/output`) is shared between all jobs. This
allows the components to share data, e.g., the master can write checkpoints and request a parameter
server to load its parameters from this checkpoint. In addition, this allows TensorFlow summary
information to be written and visualized in Tensorboard.

## Resources

The configuration file (from API section) specifies the project name and the minimal required resources
for your training jobs. Resources always specifies the requirements that are guaranteed during training.
In practice, if more CPU or Memory resources are available, the experiment will be able to use them.

## Others

**TensorBoard**

TensorBoard can be started via setting `tensorboard: true` option:

```yaml
project: ai-toaster
train:
  framework: tensorflow
  tensorflow:
    distributed: false
    tensorboard: true
    version: 1.2.0
  resources:
    cpus: 2
    mem: 4096
    gpus: 0
  run:
    - python run.py --embedding-size 32 --verbosity INFO
```

Once set, a TensorBoard will be created which reads summaries below the experiment's `OUTPUT_DIR`.
TensorBoard will be shut down automatically once the associated experiment finishes.

To obtain an offline version you can always run an instance of TensorBoard on your local workstation
(assuming you have Tensorflow installed), e.g. `tensorboard --logdir=/shared_output/your-user/ai-toaster/9`.

**Horovod**

Horovod runs a copy of the training script on each worker which reads a chunk of the data, runs it
through the model and computes model updates (gradients). Then, it uses a ring-allreduce algorithm
that allows workers to average gradients and disperse them to all nodes without the need for a
parameter server. Finally, the model is updated and the process repeats. For optimal performance
Horovod relies on message passing interface (MPI) primitives. While it is relatively easy to install
MPI on a workstation, installation of MPI on a cluster typically requires some effort. With RiseML
there is no need to configure MPI, everything is automatically set up when running a Horovod experiment.

# Components

- api (two containers: api & cronjobs): serve api
- [cli](https://docs.riseml.com/reference/cli/): the command line for riseml
- git (two containers: gitweb & gitback): the `riseml train` command synchronizes your project folder automatically each time you run it.
- ingress: gateway
- loghandler
- minio: riseml uses minio to provide access the data and output volumes via the riseml cli.
- postgresql
- rabbitmq: for streaming logs
- registry: to save training image, etc
- scheduler

# Experiment

## Installation

Follow [docs](https://docs.riseml.com/install/quicksetup/) to install riseml.

<details><summary>installation output</summary><p>

```console
$ kubectl create serviceaccount tiller --namespace kube-system
$ kubectl create clusterrolebinding tiller-cluster-admin-binding \
    --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
$ helm init --service-account tiller --tiller-namespace kube-system
$ kubectl label node 127.0.0.1 riseml.com/build-node=true
$ kubectl label node 127.0.0.1 riseml.com/system-node=true

$ helm install riseml-charts/riseml --name riseml --namespace riseml -f riseml-config.yaml
NAME:   riseml
LAST DEPLOYED: Sat Jul  7 18:02:40 2018
NAMESPACE: riseml
STATUS: DEPLOYED

RESOURCES:
==> v1/ConfigMap
NAME                          DATA  AGE
riseml-config                 31    0s
riseml-ingress-config         3     0s
riseml-ingress-tcp-configmap  3     0s

==> v1/PersistentVolumeClaim
NAME                 STATUS   VOLUME  CAPACITY  ACCESS MODES  STORAGECLASS  AGE
riseml-output-claim  Pending  0s
riseml-data-claim    Pending  0s

==> v1beta1/DaemonSet
NAME            DESIRED  CURRENT  READY  UP-TO-DATE  AVAILABLE  NODE SELECTOR  AGE
riseml-monitor  1        1        0      1           0          <none>         0s

==> v1/Secret
NAME               TYPE    DATA  AGE
riseml-minio       Opaque  2     0s
riseml-postgresql  Opaque  1     0s

==> v1/ServiceAccount
NAME                           SECRETS  AGE
riseml-ingress-serviceaccount  1        0s
riseml-serviceaccount          1        0s

==> v1/ClusterRole
NAME                        AGE
riseml-ingress-clusterrole  0s
riseml-clusterrole          0s

==> v1/ClusterRoleBinding
NAME                                     AGE
riseml-ingress-clusterrole-nisa-binding  0s
riseml-clusterrole-binding               0s

==> v1/Role
NAME                 AGE
riseml-ingress-role  0s
riseml-role          0s

==> v1/RoleBinding
NAME                              AGE
riseml-ingress-role-nisa-binding  0s
riseml-role-binding               0s

==> v1/Service
NAME                 TYPE       CLUSTER-IP  EXTERNAL-IP  PORT(S)                                                       AGE
riseml-api           ClusterIP  10.0.0.157  <none>       80/TCP                                                        0s
riseml-sync          ClusterIP  10.0.0.200  <none>       8765/TCP                                                      0s
riseml-gitback       ClusterIP  10.0.0.159  <none>       80/TCP                                                        0s
riseml-gitweb        ClusterIP  10.0.0.179  <none>       8888/TCP                                                      0s
riseml-ingress       NodePort   10.0.0.147  <none>       31213:31213/TCP,8765:31876/TCP,9000:31900/TCP,9001:31901/TCP  0s
riseml-http-backend  ClusterIP  10.0.0.226  <none>       80/TCP                                                        0s
riseml-loghandler    ClusterIP  10.0.0.119  <none>       80/TCP                                                        0s
riseml-minio         NodePort   10.0.0.161  <none>       9000:31874/TCP,9001:31875/TCP                                 0s
riseml-postgresql    ClusterIP  10.0.0.88   <none>       5432/TCP                                                      0s
riseml-rabbitmq      ClusterIP  10.0.0.245  <none>       5672/TCP,15672/TCP                                            0s
riseml-registry      NodePort   10.0.0.155  <none>       5000:31500/TCP                                                0s

==> v1beta1/Deployment
NAME                       DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  AGE
riseml-api                 1        0        0           0          0s
riseml-git                 1        0        0           0          0s
riseml-ingress-controller  1        0        0           0          0s
riseml-http-backend        1        0        0           0          0s
riseml-loghandler          1        0        0           0          0s
riseml-minio               1        0        0           0          0s
riseml-postgresql          1        0        0           0          0s
riseml-rabbitmq            1        0        0           0          0s
riseml-registry            1        0        0           0          0s
riseml-scheduler           1        0        0           0          0s

==> v1beta1/Ingress
NAME             HOSTS  ADDRESS  PORTS  AGE
riseml-services  *      80       0s

==> v1/Pod(related)
NAME                                        READY  STATUS             RESTARTS  AGE
riseml-monitor-jmh54                        0/1    ContainerCreating  0         0s
riseml-api-69746b89cf-cx6d4                 0/2    Pending            0         0s
riseml-git-6d8c5df587-qlcz7                 0/2    ContainerCreating  0         0s
riseml-ingress-controller-6f7647dcfd-ntqbd  0/1    ContainerCreating  0         0s
riseml-http-backend-5d479f589b-qf642        0/1    ContainerCreating  0         0s
riseml-loghandler-64fdbdb99b-n4mbh          0/1    ContainerCreating  0         0s
riseml-minio-594798944c-9bt6t               0/2    Pending            0         0s
riseml-postgresql-f69789fd9-pjtc2           0/1    Pending            0         0s
riseml-rabbitmq-6f7765748b-vzhx9            0/1    Pending            0         0s


NOTES:

RiseML was deployed. It may take a few minutes for all services to be operational.
You can watch the progress with this command (all Pods should be RUNNING):
  watch -n 1 kubectl get pods -n=riseml

To set up your client, look up your RiseML master's hostname or ip address and run:
  export RISEML_HOSTNAME=<YOUR MASTER HOSTNAME/IP>

### RiseML Client
You can get the RiseML client from here: http://docs.riseml.com/install/cli.html
To configure the RiseML client, run:
  riseml user login --api-key yourSecretApiKeyYouWantToUse1234 --api-host ${RISEML_HOSTNAME}:31213

You can find some examples to run on https://github.com/riseml/examples
More information is available in our documentation: https://docs.riseml.com
```

</p></details></br>

Note I'm having trouble working with nfs provisioner, so it is disabled and we create PV manually:

```
$ kubectl create -f pv-hostpath-2.yaml
```

Once all components are up, login through ingress:

```
$ riseml user login
Configuring new user login. This will overwrite your existing configuration.

Please provide the DNS name or IP of your RiseML API server.
Example: 54.131.125.42:31213
--> 127.0.0.1:31213

Please provide your API key.
Example: krlo2oxrtd2084zs7jahwyqu12b7mozg
--> yourSecretApiKeyYouWantToUse1234

Trying to login to 127.0.0.1:31213/api with API key 'yourSecretApiKeyYouWantToUse1234' for at most 180s... Success!
Checking connection to sync server rsync://127.0.0.1:31876/sync for at most 20s... Success!

Login succeeded, config updated.

$ riseml whoami
you are: admin (deyuan.deng@gmail.com)
```

## Run experiment (census)

Now enter census directory and run `riseml train`. By default, `riseml.yaml` will be used as the
default configuration. Once the command is run, a builder pod will be created. The builder pod has
two containers:
- riseml/imagebuilder:v1.2.3
- riseml/logsidecar:v1.2.3

The image builder has a `build.py` script used to build training container, it:
- download code from `DOWNLOAD_URL`, i.e. downloading repository from gitlab with specific revision
- uses `FROM_IMAGE` and `INSTALL_COMMANDS` to build a container named `TARGET_IMAGE` (auto-generate dockerfile)
- push the result training image to riseml registry

Also note that the build image:
- mounted host path `/var/run/docker.sock`
- mounted `riseml-data-claim` to container `/data` directory
- uses node affinity and pod affinity

<details><summary>builder yaml config</summary><p>

```yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: 2018-07-07T10:30:29Z
  labels:
    experiment_id: c4dadaf8-81d0-11e8-bb06-0242ac11000e
    job_id: c4dce7a8-81d0-11e8-bb06-0242ac11000e
    kind: batch
    project: censusexample
    role: build
    slug: admin-censusexample-2-build
    username: admin
  name: admin-censusexample-2-build
  namespace: riseml
  resourceVersion: "5752"
  selfLink: /api/v1/namespaces/riseml/pods/admin-censusexample-2-build
  uid: c4e57e46-81d0-11e8-8058-2c4d54ed3845
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - preference:
          matchExpressions:
          - key: riseml.com/system-node
            operator: NotIn
            values:
            - "true"
        weight: 100
      - preference:
          matchExpressions:
          - key: riseml.com/build-node
            operator: In
            values:
            - "true"
        weight: 100
    podAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: experiment_id
              operator: In
              values:
              - c4dadaf8-81d0-11e8-bb06-0242ac11000e
          topologyKey: kubernetes.io/hostname
        weight: 100
  containers:
  - env:
    - name: REGISTRY_USER
    - name: REGISTRY_PASSWORD
    - name: TERMINATION_LOGFILE
      value: /logs/termination-log
    - name: LOGFILE
      value: /logs/job
    - name: EXPERIMENT_ID
      value: c4dadaf8-81d0-11e8-bb06-0242ac11000e
    - name: CLUSTER_ID
      value: 2d140abc-81cd-11e8-818b-0242ac11000e
    - name: ENVIRONMENT
      value: production
    - name: BACKEND_URL
      value: https://backend.riseml.com
    - name: BACKEND_URL
      value: https://backend.riseml.com
    - name: TARGET_IMAGE
      value: 127.0.0.1:31500/build:admin-census-example-4cc244a-t3pt3mna
    - name: DOWNLOAD_URL
      value: http://riseml-gitweb:8888/users/0b687763-0757-11e7-875b-80e65006b9ce/repositories/census-example?revision=4cc244a8c8d96c781cb199d7f3dd39da136ba0b8
    - name: ENVIRONMENT
      value: production
    - name: FROM_IMAGE
      value: tensorflow/tensorflow:1.5.0
    - name: INSTALL_COMMANDS
      value: '[]'
    image: riseml/imagebuilder:v1.2.3
    imagePullPolicy: Always
    name: job
    resources:
      requests:
        cpu: 500m
        memory: 512M
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    tty: true
    volumeMounts:
    - mountPath: /logs
      name: logs
    - mountPath: /usr/local/nvidia
      name: nvidia
    - mountPath: /var/run/docker.sock
      name: docker-sock
    - mountPath: /root/.docker/config.json
      name: docker-config
    - mountPath: /data
      name: data
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-nhrh8
      readOnly: true
  - env:
    - name: LOGFILE
      value: /logs/job
    - name: TERMINATION_LOGFILE
      value: /logs/termination-log
    - name: AMQP_URL
      value: amqp://riseml-rabbitmq
    - name: LOG_JOB_ID
      value: c4dce7a8-81d0-11e8-bb06-0242ac11000e
    - name: LOG_QUEUE
      value: log
    - name: CLUSTER_ID
      value: 2d140abc-81cd-11e8-818b-0242ac11000e
    - name: ENVIRONMENT
      value: production
    - name: BACKEND_URL
      value: https://backend.riseml.com
    image: riseml/logsidecar:v1.2.3
    imagePullPolicy: IfNotPresent
    name: log-sidecar
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /logs
      name: logs
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-nhrh8
      readOnly: true
  dnsPolicy: ClusterFirst
  nodeName: 127.0.0.1
  nodeSelector:
    riseml.com/system-node: "true"
  restartPolicy: Never
  schedulerName: default-scheduler
  securityContext: {}
  serviceAccount: default
  serviceAccountName: default
  terminationGracePeriodSeconds: 30
  tolerations:
  - effect: NoExecute
    key: node.kubernetes.io/not-ready
    operator: Exists
    tolerationSeconds: 300
  - effect: NoExecute
    key: node.kubernetes.io/unreachable
    operator: Exists
    tolerationSeconds: 300
  volumes:
  - emptyDir: {}
    name: logs
  - hostPath:
      path: /var/lib/nvidia-docker/volumes/nvidia_driver/latest
      type: ""
    name: nvidia
  - hostPath:
      path: /var/run/docker.sock
      type: ""
    name: docker-sock
  - hostPath:
      path: /var/lib/kubelet/config.json
      type: ""
    name: docker-config
  - name: data
    persistentVolumeClaim:
      claimName: riseml-data-claim
  - name: default-token-nhrh8
    secret:
      defaultMode: 420
      secretName: default-token-nhrh8
```

</p></details></br>

Following is the training pod launched via riseml. There are two containers in the pod:
- one for training whose image comes from built-in registry (see above)
- the other container is log sidecar

<details><summary>training yaml config</summary><p>

```yaml
# kubectl get pods -n riseml admin-censusexample-3-train -o yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: 2018-07-07T10:38:12Z
  labels:
    experiment_id: d8f1cb2c-81d1-11e8-bb06-0242ac11000e
    job_id: d8f6e684-81d1-11e8-bb06-0242ac11000e
    kind: batch
    project: censusexample
    role: train
    slug: admin-censusexample-3-train
    username: admin
  name: admin-censusexample-3-train
  namespace: riseml
  resourceVersion: "6570"
  selfLink: /api/v1/namespaces/riseml/pods/admin-censusexample-3-train
  uid: d911b65c-81d1-11e8-8058-2c4d54ed3845
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - preference:
          matchExpressions:
          - key: riseml.com/system-node
            operator: NotIn
            values:
            - "true"
        weight: 100
    podAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: experiment_id
              operator: In
              values:
              - d8f1cb2c-81d1-11e8-bb06-0242ac11000e
          topologyKey: kubernetes.io/hostname
        weight: 100
  containers:
  - env:
    - name: REGISTRY_USER
    - name: REGISTRY_PASSWORD
    - name: TERMINATION_LOGFILE
      value: /logs/termination-log
    - name: LOGFILE
      value: /logs/job
    - name: EXPERIMENT_ID
      value: d8f1cb2c-81d1-11e8-bb06-0242ac11000e
    - name: CLUSTER_ID
      value: 2d140abc-81cd-11e8-818b-0242ac11000e
    - name: ENVIRONMENT
      value: production
    - name: BACKEND_URL
      value: https://backend.riseml.com
    - name: OUTPUT_DIR
      value: /output
    - name: COMMAND_1
      value: python run.py --num-epochs 2 --num-layers 4 --embedding-size 32  --verbosity
        INFO --job-dir $OUTPUT_DIR
    image: 127.0.0.1:31500/build:admin-census-example-4cc244a-t3pt3mna
    imagePullPolicy: Always
    name: job
    resources:
      requests:
        cpu: 500m
        memory: 512M
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    tty: true
    volumeMounts:
    - mountPath: /logs
      name: logs
    - mountPath: /usr/local/nvidia
      name: nvidia
    - mountPath: /data
      name: data
    - mountPath: /output
      name: output
      subPath: admin/census-example/3
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-nhrh8
      readOnly: true
  - env:
    - name: LOGFILE
      value: /logs/job
    - name: TERMINATION_LOGFILE
      value: /logs/termination-log
    - name: AMQP_URL
      value: amqp://riseml-rabbitmq
    - name: LOG_JOB_ID
      value: d8f6e684-81d1-11e8-bb06-0242ac11000e
    - name: LOG_QUEUE
      value: log
    - name: CLUSTER_ID
      value: 2d140abc-81cd-11e8-818b-0242ac11000e
    - name: ENVIRONMENT
      value: production
    - name: BACKEND_URL
      value: https://backend.riseml.com
    image: riseml/logsidecar:v1.2.3
    imagePullPolicy: IfNotPresent
    name: log-sidecar
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /logs
      name: logs
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-nhrh8
      readOnly: true
  dnsPolicy: ClusterFirst
  nodeName: 127.0.0.1
  restartPolicy: Never
  schedulerName: default-scheduler
  securityContext: {}
  serviceAccount: default
  serviceAccountName: default
  terminationGracePeriodSeconds: 30
  tolerations:
  - effect: NoExecute
    key: node.kubernetes.io/not-ready
    operator: Exists
    tolerationSeconds: 300
  - effect: NoExecute
    key: node.kubernetes.io/unreachable
    operator: Exists
    tolerationSeconds: 300
  volumes:
  - emptyDir: {}
    name: logs
  - hostPath:
      path: /var/lib/nvidia-docker/volumes/nvidia_driver/latest
      type: ""
    name: nvidia
  - name: data
    persistentVolumeClaim:
      claimName: riseml-data-claim
  - name: output
    persistentVolumeClaim:
      claimName: riseml-output-claim
  - name: default-token-nhrh8
    secret:
      defaultMode: 420
      secretName: default-token-nhrh8
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: 2018-07-07T10:38:12Z
    status: "True"
    type: Initialized
  - lastProbeTime: null
    lastTransitionTime: 2018-07-07T10:38:15Z
    status: "True"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: 2018-07-07T10:38:12Z
    status: "True"
    type: PodScheduled
  containerStatuses:
  - containerID: docker://f4676a9f91db722cf73de58a43ec09ee66db4f37baa9400b7cc48625204b7bd8
    image: 127.0.0.1:31500/build:admin-census-example-4cc244a-t3pt3mna
    imageID: docker-pullable://127.0.0.1:31500/build@sha256:1c9db24c89aa5773da9290e386562971f4ed8356df6088342bc1b58c80a346c1
    lastState: {}
    name: job
    ready: true
    restartCount: 0
    state:
      running:
        startedAt: 2018-07-07T10:38:14Z
  - containerID: docker://1ddb10c59c46dbf1ae5dc7943c0d77f98561766a08535a4f7c95fc8034a95c3b
    image: riseml/logsidecar:v1.2.3
    imageID: docker-pullable://riseml/logsidecar@sha256:b2f9588b27a15472c2a037ba3d518aadbb4bcf46194f9de9b25431986c5873fe
    lastState: {}
    name: log-sidecar
    ready: true
    restartCount: 0
    state:
      running:
        startedAt: 2018-07-07T10:38:14Z
  hostIP: 127.0.0.1
  phase: Running
  podIP: 172.17.0.16
  qosClass: Burstable
  startTime: 2018-07-07T10:38:12Z
```

</p></details></br>

Note that the census example data is small, thus data is directly synced to container (the data is
treated as part of the code, instead of using data volume, ). The training process will version
control our code into the built-in git server, and the built image will be pushed to the built-in
docker registry. Here `/tmp/data1` is bound for our output, we can inspect the result:

<details><summary>output directory structure</summary><p>

```
$ tree /tmp/data1
/tmp/data1
└── admin
    └── census-example
        ├── 1
        │   └── riseml-experiment.yml
        └── 2
            ├── checkpoint
            ├── eval
            │   └── events.out.tfevents.1530959482.admin-censusexample-2-train
            ├── events.out.tfevents.1530959477.admin-censusexample-2-train
            ├── export
            │   └── Servo
            │       └── 1530959491
            │           ├── saved_model.pb
            │           └── variables
            │               ├── variables.data-00000-of-00001
            │               └── variables.index
            ├── graph.pbtxt
            ├── model.ckpt-2.data-00000-of-00001
            ├── model.ckpt-2.index
            ├── model.ckpt-2.meta
            ├── model.ckpt-3256.data-00000-of-00001
            ├── model.ckpt-3256.index
            ├── model.ckpt-3256.meta
            └── riseml-experiment.yml

9 directories, 15 files
```

</p></details></br>

To view logs, we can use `riseml logs`. The builder and training image both has a log sidecar, which
- read logs (using `tail -f`) from `LOGFILE`
- use pika, the amqp client to stream logs from container to rabbitmq running at `AMQP_URL`

<details><summary>Logs from the whole build and train process</summary><p>

```
$ riseml logs 2
2.build       | [2018-07-07T10:30:29Z] --> STARTING
2.build       | [2018-07-07T10:30:29Z] Reason: PREPARE
2.build       | [2018-07-07T10:30:29Z] Message: Preparing environment
2.build       | [2018-07-07T10:30:35Z] Preparing image for your experiment
2.build       | [2018-07-07T10:30:35Z] Downloading your code
2.build       | [2018-07-07T10:30:35Z] Running install commands...
2.build       | [2018-07-07T10:30:35Z] Step 1/5 : FROM tensorflow/tensorflow:1.5.0
2.build       | [2018-07-07T10:30:36Z] --> RUNNING
2.build       | [2018-07-07T10:30:39Z] Pulling from tensorflow/tensorflow
2.build       | [2018-07-07T10:30:39Z]  ---> a2d1671e8a93
2.build       | [2018-07-07T10:30:39Z] Step 2/5 : WORKDIR /code
2.build       | [2018-07-07T10:30:41Z] Removing intermediate container 9ee3c5dd4c0a
2.build       | [2018-07-07T10:30:41Z]  ---> c0e88c5233fb
2.build       | [2018-07-07T10:30:41Z] Step 3/5 : COPY riseml_run.sh /riseml_run.sh
2.build       | [2018-07-07T10:30:42Z]  ---> 63dd58784b08
2.build       | [2018-07-07T10:30:42Z] Step 4/5 : COPY code /code
2.build       | [2018-07-07T10:30:44Z]  ---> 457ca354a865
2.build       | [2018-07-07T10:30:44Z] Step 5/5 : CMD /riseml_run.sh
2.build       | [2018-07-07T10:30:44Z]  ---> Running in 1ac765d74803
2.build       | [2018-07-07T10:30:45Z] Removing intermediate container 1ac765d74803
2.build       | [2018-07-07T10:30:45Z]  ---> 9d9d3303437e
2.build       | [2018-07-07T10:30:45Z] Successfully built 9d9d3303437e
2.build       | [2018-07-07T10:30:45Z] Successfully tagged 127.0.0.1:31500/build:admin-census-example-4cc244a-t3pt3mna
2.build       | [2018-07-07T10:30:45Z] Image size: 1260.90 MB in 15 layers
2.build       | [2018-07-07T10:30:45Z] Storing your image...
2.build       | [2018-07-07T10:30:47Z] ...stored 10%
2.build       | [2018-07-07T10:30:49Z] ...stored 20%
2.build       | [2018-07-07T10:30:50Z] ...stored 30%
2.build       | [2018-07-07T10:30:52Z] ...stored 40%
2.build       | [2018-07-07T10:30:54Z] ...stored 50%
2.build       | [2018-07-07T10:30:55Z] ...stored 60%
2.build       | [2018-07-07T10:30:59Z] ...stored 70%
2.build       | [2018-07-07T10:31:01Z] ...stored 80%
2.build       | [2018-07-07T10:31:05Z] ...stored 90%
2.build       | [2018-07-07T10:31:11Z] ...stored 100%
2.build       | [2018-07-07T10:31:12Z] Build process finished.
2             | [2018-07-07T10:31:13Z] --> STARTING
2.build       | [2018-07-07T10:31:13Z] --> FINISHED
2.build       | [2018-07-07T10:31:13Z] Reason: COMPLETED
2.build       | [2018-07-07T10:31:13Z] Exit Code: 0
2.train       | [2018-07-07T10:31:13Z] --> PENDING
2.train       | [2018-07-07T10:31:13Z] --> STARTING
2.train       | [2018-07-07T10:31:13Z] Reason: PREPARE
2.train       | [2018-07-07T10:31:13Z] Message: Preparing environment
2.tensorboard | [2018-07-07T10:31:13Z] --> PENDING
2.tensorboard | [2018-07-07T10:31:13Z] --> STARTING
2.tensorboard | [2018-07-07T10:31:13Z] Reason: PREPARE
2.tensorboard | [2018-07-07T10:31:13Z] Message: Preparing environment
2             | [2018-07-07T10:31:16Z] --> RUNNING
2.train       | [2018-07-07T10:31:16Z] /usr/local/lib/python2.7/dist-packages/h5py/__init__.py:36: FutureWarning: Conversion of the second argument of issubdtype from `float` to `np.floating` is deprecated. In future, it will be treated as `np.float64 == np.dtype(float).type`.
2.train       | [2018-07-07T10:31:16Z]   from ._conv import register_converters as _register_converters
2.train       | [2018-07-07T10:31:16Z] Starting Census: Please lauch tensorboard to see results:
2.train       | [2018-07-07T10:31:16Z] tensorboard --logdir=$MODEL_DIR
2.train       | [2018-07-07T10:31:16Z] TF_CONFIG: None
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:The default stddev value of initializer will change from "1/sqrt(vocab_size)" to "1/sqrt(dimension)" after 2017/02/25.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:From /code/model.py:149: calling __init__ (from tensorflow.contrib.learn.python.learn.estimators.dnn_linear_combined) with fix_global_step_increment_bug=False is deprecated and will be removed after 2017-04-15.
2.train       | [2018-07-07T10:31:16Z] Instructions for updating:
2.train       | [2018-07-07T10:31:16Z] Please set fix_global_step_increment_bug=True and update training steps in your pipeline. See pydoc for details.
2.train       | [2018-07-07T10:31:16Z] INFO:tensorflow:Using default config.
2.train       | [2018-07-07T10:31:16Z] INFO:tensorflow:Using config: {'_save_checkpoints_secs': 600, '_num_ps_replicas': 0, '_keep_checkpoint_max': 5, '_task_type': None, '_is_chief': True, '_cluster_spec': <tensorflow.python.training.server_lib.ClusterSpec object at 0x7fc1081dd750>, '_model_dir': '/output', '_save_checkpoints_steps': None, '_keep_checkpoint_every_n_hours': 10000, '_session_config': None, '_tf_random_seed': None, '_save_summary_steps': 100, '_environment': 'local', '_num_worker_replicas': 0, '_task_id': 0, '_log_step_count_steps': 100, '_tf_config': gpu_options {
2.train       | [2018-07-07T10:31:16Z]   per_process_gpu_memory_fraction: 1.0
2.train       | [2018-07-07T10:31:16Z] }
2.train       | [2018-07-07T10:31:16Z] , '_evaluation_master': '', '_master': ''}
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:From /usr/local/lib/python2.7/dist-packages/tensorflow/contrib/learn/python/learn/monitors.py:267: __init__ (from tensorflow.contrib.learn.python.learn.monitors) is deprecated and will be removed after 2016-12-05.
2.train       | [2018-07-07T10:31:16Z] Instructions for updating:
2.train       | [2018-07-07T10:31:16Z] Monitors are deprecated. Please use tf.train.SessionRunHook.
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:From /code/model.py:164: string_to_index_table_from_tensor (from tensorflow.contrib.lookup.lookup_ops) is deprecated and will be removed after 2017-04-10.
2.train       | [2018-07-07T10:31:16Z] Instructions for updating:
2.train       | [2018-07-07T10:31:16Z] Use `index_table_from_tensor`.
2.train       | [2018-07-07T10:31:16Z] --> RUNNING
2.train       | [2018-07-07T10:31:16Z] WARNING:tensorflow:From /usr/local/lib/python2.7/dist-packages/tensorflow/contrib/layers/python/layers/feature_column.py:2333: calling sparse_feature_cross (from tensorflow.contrib.layers.python.ops.sparse_feature_cross_op) with hash_key=None is deprecated and will be removed after 2016-11-20.
2.train       | [2018-07-07T10:31:16Z] Instructions for updating:
2.train       | [2018-07-07T10:31:16Z] The default behavior of sparse_feature_cross is changing, the default
2.train       | [2018-07-07T10:31:16Z] value for hash_key will change to SPARSE_FEATURE_CROSS_DEFAULT_HASH_KEY.
2.train       | [2018-07-07T10:31:16Z] From that point on sparse_feature_cross will always use FingerprintCat64
2.train       | [2018-07-07T10:31:16Z] to concatenate the feature fingerprints. And the underlying
2.train       | [2018-07-07T10:31:16Z] _sparse_feature_cross_op.sparse_feature_cross operation will be marked
2.train       | [2018-07-07T10:31:16Z] as deprecated.
2.train       | [2018-07-07T10:31:17Z] WARNING:tensorflow:Casting <dtype: 'int64'> labels to bool.
2.train       | [2018-07-07T10:31:17Z] WARNING:tensorflow:Casting <dtype: 'int64'> labels to bool.
2.tensorboard | [2018-07-07T10:31:17Z] /usr/local/lib/python2.7/dist-packages/h5py/__init__.py:36: FutureWarning: Conversion of the second argument of issubdtype from `float` to `np.floating` is deprecated. In future, it will be treated as `np.float64 == np.dtype(float).type`.
2.tensorboard | [2018-07-07T10:31:17Z]   from ._conv import register_converters as _register_converters
2.tensorboard | [2018-07-07T10:31:17Z] TensorBoard 1.5.0 at http://127.0.0.1:31213/tensorboard/admin-censusexample-2-tensorboard (Press CTRL+C to quit)
2.tensorboard | [2018-07-07T10:31:17Z] --> RUNNING
2.train       | [2018-07-07T10:31:18Z] INFO:tensorflow:Create CheckpointSaverHook.
2.train       | [2018-07-07T10:31:18Z] 2018-07-07 10:31:18.179184: I tensorflow/core/platform/cpu_feature_guard.cc:137] Your CPU supports instructions that this TensorFlow binary was not compiled to use: SSE4.1 SSE4.2 AVX AVX2 FMA
2.train       | [2018-07-07T10:31:20Z] INFO:tensorflow:Saving checkpoints for 2 into /output/model.ckpt.
2.train       | [2018-07-07T10:31:21Z] WARNING:tensorflow:Casting <dtype: 'int64'> labels to bool.
2.train       | [2018-07-07T10:31:21Z] WARNING:tensorflow:Casting <dtype: 'int64'> labels to bool.
2.train       | [2018-07-07T10:31:21Z] INFO:tensorflow:Starting evaluation at 2018-07-07-10:31:21
2.train       | [2018-07-07T10:31:21Z] INFO:tensorflow:Restoring parameters from /output/model.ckpt-2
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [10/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [20/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [30/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [40/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [50/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [60/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [70/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [80/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [90/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Evaluation [100/100]
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Finished evaluation at 2018-07-07-10:31:22
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Saving dict for global step 2: accuracy = 0.76325, accuracy/baseline_label_mean = 0.23675, accuracy/threshold_0.500000_mean = 0.76325, auc = 0.5, auc_precision_recall = 0.618375, global_step = 2, labels/actual_label_mean = 0.23675, labels/prediction_mean = 2.6715541e-05, loss = 488.42184, precision/positive_threshold_0.500000_mean = 0.0, recall/positive_threshold_0.500000_mean = 0.0
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:Validation (step 1): accuracy/baseline_label_mean = 0.23675, loss = 488.42184, auc = 0.5, global_step = 2, accuracy/threshold_0.500000_mean = 0.76325, recall/positive_threshold_0.500000_mean = 0.0, labels/prediction_mean = 2.6715541e-05, accuracy = 0.76325, auc_precision_recall = 0.618375, precision/positive_threshold_0.500000_mean = 0.0, labels/actual_label_mean = 0.23675
2.train       | [2018-07-07T10:31:22Z] INFO:tensorflow:loss = 0.9997929, step = 2
2.tensorboard | [2018-07-07T10:31:22Z] W0707 10:31:22.079875 Reloader plugin_event_accumulator.py:300] Found more than one graph event per run, or there was a metagraph containing a graph_def, as well as one or more graph events.  Overwriting the graph with the newest event.
2.tensorboard | [2018-07-07T10:31:22Z] W0707 10:31:22.081069 Reloader plugin_event_accumulator.py:308] Found more than one metagraph event per run. Overwriting the metagraph with the newest event.
2.train       | [2018-07-07T10:31:23Z] INFO:tensorflow:global_step/sec: 42.7116
2.train       | [2018-07-07T10:31:23Z] INFO:tensorflow:loss = 0.33384007, step = 202 (0.533 sec)
2.train       | [2018-07-07T10:31:23Z] INFO:tensorflow:global_step/sec: 623.835
2.train       | [2018-07-07T10:31:23Z] INFO:tensorflow:global_step/sec: 598.458
2.train       | [2018-07-07T10:31:23Z] INFO:tensorflow:loss = 0.29831344, step = 402 (0.364 sec)
2.train       | [2018-07-07T10:31:23Z] INFO:tensorflow:global_step/sec: 514.806
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:global_step/sec: 576.995
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:loss = 0.257569, step = 602 (0.336 sec)
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:global_step/sec: 620.51
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:global_step/sec: 611.812
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:loss = 0.42816648, step = 802 (0.360 sec)
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:global_step/sec: 495.211
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:global_step/sec: 569.785
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:loss = 0.30759683, step = 1002 (0.369 sec)
2.train       | [2018-07-07T10:31:24Z] INFO:tensorflow:global_step/sec: 526.701
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:global_step/sec: 580.687
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:loss = 0.38597742, step = 1202 (0.330 sec)
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:global_step/sec: 653.088
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:global_step/sec: 582.751
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:loss = 0.1596497, step = 1402 (0.347 sec)
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:global_step/sec: 569.692
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:global_step/sec: 544.979
2.train       | [2018-07-07T10:31:25Z] INFO:tensorflow:loss = 0.39917013, step = 1602 (0.358 sec)
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:global_step/sec: 575.956
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:global_step/sec: 579.56
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:loss = 0.45815736, step = 1801 (0.334 sec)
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:global_step/sec: 555.761
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:global_step/sec: 376.353
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:loss = 0.2762114, step = 2001 (0.470 sec)
2.train       | [2018-07-07T10:31:26Z] INFO:tensorflow:global_step/sec: 521.611
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:global_step/sec: 531.01
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:loss = 0.37210077, step = 2201 (0.424 sec)
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:global_step/sec: 396.969
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:global_step/sec: 453.358
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:loss = 0.27984786, step = 2401 (0.453 sec)
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:global_step/sec: 447.443
2.train       | [2018-07-07T10:31:27Z] INFO:tensorflow:global_step/sec: 386.229
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:loss = 0.35403627, step = 2601 (0.457 sec)
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:global_step/sec: 570.084
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:global_step/sec: 666.357
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:loss = 0.24831872, step = 2801 (0.367 sec)
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:global_step/sec: 397.028
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:global_step/sec: 374.212
2.train       | [2018-07-07T10:31:28Z] INFO:tensorflow:loss = 0.39032117, step = 3000 (0.496 sec)
2.train       | [2018-07-07T10:31:29Z] INFO:tensorflow:global_step/sec: 371.631
2.train       | [2018-07-07T10:31:29Z] INFO:tensorflow:global_step/sec: 313.131
2.train       | [2018-07-07T10:31:29Z] INFO:tensorflow:loss = 0.35257336, step = 3200 (0.631 sec)
2.train       | [2018-07-07T10:31:29Z] INFO:tensorflow:Saving checkpoints for 3256 into /output/model.ckpt.
2.train       | [2018-07-07T10:31:30Z] INFO:tensorflow:Loss for final step: 0.54631233.
2.train       | [2018-07-07T10:31:30Z] WARNING:tensorflow:Casting <dtype: 'int64'> labels to bool.
2.train       | [2018-07-07T10:31:30Z] WARNING:tensorflow:Casting <dtype: 'int64'> labels to bool.
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Starting evaluation at 2018-07-07-10:31:30
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Restoring parameters from /output/model.ckpt-3256
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [10/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [20/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [30/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [40/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [50/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [60/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [70/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [80/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [90/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Evaluation [100/100]
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Finished evaluation at 2018-07-07-10:31:31
2.train       | [2018-07-07T10:31:31Z] INFO:tensorflow:Saving dict for global step 3256: accuracy = 0.82925, accuracy/baseline_label_mean = 0.23675, accuracy/threshold_0.500000_mean = 0.82925, auc = 0.89133114, auc_precision_recall = 0.70725477, global_step = 3256, labels/actual_label_mean = 0.23675, labels/prediction_mean = 0.30128515, loss = 0.3604088, precision/positive_threshold_0.500000_mean = 0.618068, recall/positive_threshold_0.500000_mean = 0.7296727
2.train       | [2018-07-07T10:31:32Z] INFO:tensorflow:Restoring parameters from /output/model.ckpt-3256
2.train       | [2018-07-07T10:31:32Z] INFO:tensorflow:Assets added to graph.
2.train       | [2018-07-07T10:31:32Z] INFO:tensorflow:No assets to write.
2.train       | [2018-07-07T10:31:32Z] INFO:tensorflow:SavedModel written to: /output/export/Servo/temp-1530959491/saved_model.pb
2.train       | [2018-07-07T10:31:32Z] Finished.
2             | [2018-07-07T10:31:33Z] --> FINISHED
2.train       | [2018-07-07T10:31:33Z] --> FINISHED
2.train       | [2018-07-07T10:31:33Z] Reason: COMPLETED
2.train       | [2018-07-07T10:31:33Z] Message: Command python run.py --num-epochs 2 --num-layers 4 --embedding-size 32  --verbosity INFO --job-dir $OUTPUT_DIR return code: 0
2.train       | [2018-07-07T10:31:33Z] Exit Code: 0
2.tensorboard | [2018-07-07T10:31:33Z] --> KILLED
2.tensorboard | [2018-07-07T10:31:33Z] Reason: KILLED

Experiment will continue in background
Type `riseml logs 2` to connect to log stream again
```

</p></details></br>

To view training status, use `riseml status`:

```
$ riseml status 2
ID: 2
Type: Experiment
State: ✓ FINISHED
Started:  2018-07-07T10:31:13Z
Finished: 2018-07-07T10:31:33Z
Duration: 20 seconds
Image: tensorflow/tensorflow:1.5.0
Framework: tensorflow
Framework Config:
  tensorboard: True
  version: 1.5.0
Tensorboard: OFFLINE
Run Commands:
  python run.py --num-epochs 2 --num-layers 4 --embedding-size 32  --verbosity INFO --job-dir $OUTPUT_DIR
Concurrency: 1
Parameters:
Result:

JOB ID        STATE       STARTED    DURATION   REASON        MESSAGE              EXIT CODE  GPU    CPU    MEM
2.build       ✓ FINISHED  10 minutes 37 seconds COMPLETED                          0          0      0.5    512
2.train       ✓ FINISHED  9 minutes  17 seconds COMPLETED     Command python ru... 0          0      0.5    512
2.tensorboard ✗ KILLED    9 minutes  16 seconds KILLED                                        0      0.2    256
```

## Run experiment (census hyper, dist, etc)

Use `riseml train -f riseml_hyper.yml` to perform hyperparameter tunning, e.g. the following is training
status for the above command:

```
$ kubectl get pods -n riseml
NAME                                         READY     STATUS    RESTARTS   AGE
admin-censusexample-5-1-train                2/2       Running   0          13s
admin-censusexample-5-2-train                2/2       Running   0          13s
admin-censusexample-5-tensorboard            2/2       Running   0          13s

$ kubectl get pods -n riseml
NAME                                         READY     STATUS        RESTARTS   AGE
admin-censusexample-5-3-train                0/2       Terminating   0          1m
admin-censusexample-5-4-train                0/2       Terminating   0          1m
admin-censusexample-5-5-train                0/2       Terminating   0          35s
admin-censusexample-5-6-train                2/2       Running       0          33s
admin-censusexample-5-tensorboard            2/2       Running       0          1m
```
