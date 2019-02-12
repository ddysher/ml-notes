<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Designs](#designs)
- [Concepts](#concepts)
  - [Task](#task)
  - [TaskRun](#taskrun)
  - [PipelineResources](#pipelineresources)
  - [Pipeline](#pipeline)
  - [PipelineRun](#pipelinerun)
  - [Conditions](#conditions)
- [Experiments (v0.12.0)](#experiments-v0120)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 05/10/2020, 0.12.0*

The Tekton Pipelines project provides Kubernetes-style resources for declaring CI/CD-style pipelines.

Tekton was rebranded from Knative Build.

# Designs

For many of the design decisions, see [developer guide](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/developers/README.md).

Quick summary:
- Tekton's core running component is: tekton controller and tekton webhook.
- Use configmap extensively for configuration management.
- Step (Container) execution order of a Task (Pod) is managed by replacing container's entrypoint
  with Tekton's entrypoint. The Tekton entrypoint binary is mounted at Task startup, and sequencing
  containers will leverage files under `/tekton/downward/ready`, etc, e.g. wait file to be present.
- Reserved directories is necessary and worth well-documentation, in Tekton, it's `/tekton` and `/workspace`.
- PipelineRun uses PVC to share PipelineResources between tasks. PVC volume is mounted on path `/pvc`
  by PipelineRun. Depending on Pipeline definition, Tekton controller will selectively copy resources
  from `/workspace/output/resource_name` to `/pvc/task_name/resource_name`.
- Task can define multiple results and the results will be added to `task.status.taskResults`. Tekton
  uses container termination log to save results, so it's ok to add the result to CRD status since
  the size is limited to serveral kilobytes. For larger result, a workspace/volume is needed.
- Tekton sidecar needs to run before Setps container starts and stop after Setps container terminates.
  The design here is to use downward API to project a file from annotation, which is an empty string
  initially: tekton entrypoint will wait until the file is not empty size. Once all sidecars start,
  the annotation value will be changed to "READY" and thus the projected file is no longer empty
  (therefore Steps entrypoint will move on). On completion of all Steps, the controller will change
  sidecar image to a `nop` image (a custom do-nothing image), which results Kubernetes restarting
  the sidecar containers and change the status to "Completed": if Tekton doesn't change the image,
  the sidecar might run forever, since it is usually a service like DinD, MongoDB, etc.
- In order to support potential multi-tenant configurations, the roles of the tekton controller are
  split into two: `tekton-pipelines-controller-cluster-access` and `tekton-pipelines-controller-tenant-access`.

# Concepts

## [Task](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/tasks.md)

Task is a CRD defined in Kubernetes. A Task defines a series of steps that run in a desired order
and complete a set amount of build work. Every Task runs as a **Pod** on your Kubernetes cluster
with each step as its own **Container**. Note that creating a Task CRD won't run the Task: we need
to create a TaskRun CRD to trigger the execution.

<details><summary>Example</summary><p>

```yaml
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: echo-hello-world
spec:
  steps:
    - name: echo
      image: ubuntu
      command:
        - echo
      args:
        - "Hello World"
```

Tekton CLI `tkn` provides a better UX for dealing with Task (compared to `kubectl`):

```shell
$ kubectl apply -f hello-world-task.yaml
...

$ tkn task describe echo-hello-world
...
```

</p></details></br>

A Task declaration contains following core elements:
- Steps: A Step is a reference to a container image that executes a specific tool on a specific
  input and produces a specific output. To add Steps to a Task you define a `steps` field (required)
  containing a list of desired Steps. **The order in which the Steps appear in this list is the
  order in which they will execute.**
- Parameters: You can specify parameters, such as compilation flags or artifact names, that you want
  to supply to the Task at execution time. **Parameters are passed to the Task from its corresponding
  TaskRun**.
- Resources: A Task definition can specify input and output resources supplied by a PipelineResources
  entity. If the output of a Task is the input of another Task, then the first Task needs to write
  the output to `/workspace/output/resource_name/`.
- Workspaces: Workspaces allow Tasks to declare parts of the filesystem that need to be provided at
  runtime by TaskRuns. A TaskRun can make these parts of the filesystem available in many ways: using
  a read-only ConfigMap or Secret, an existing PersistentVolumeClaim shared with other Tasks, create
  a PersistentVolumeClaim from a provided VolumeClaimTemplate, or simply an emptyDir that is discarded
  when the TaskRun completes. **Workspaces are similar to Volumes except that they allow a Task author
  to defer to users and their TaskRuns when deciding which class of storage to use.**
- Results: The results field is used to specify one or more files in which the Task stores its
  execution results. The output path is `/tekton/results/result_name`. Result is saved in container
  termination log in Kubernetes; for larger result, a Workspace is needed.
- Volumes: Specifies one or more Volumes that the Steps in your Task require to execute in addition
  to volumes that are implicitly created for input and output resources. Generally, volumes here
  refer to Kubernetes volumes like Secret, EmptyDir, ConfigMap, HostPath, PVC, etc.

Additional features include:
- Specifying a Step template: a base Step template for all othe Steps.
- Specifying Sidecars: a list of containers running alongside with Step container. Sidecars are
  created when Task executes and are deleted after the Task execution completes.
- Adding a description
- Using variable substitution

A few more details:
- A Task is available within a specific namespace, while a ClusterTask is available across the
  entire cluster. ClusterTasks are used to represent Tasks that should be publicly addressable
  from any namespace in the cluster. **The actual pods will run inside the namespace from TaskRun
  that references the ClusterTask: it's just the ClusterTask that is cluster scope.**
- Tekton contains a few **Reserved Directories**:
  - `/workspace` - This directory is where resources and workspaces are mounted.
  - `/tekton` - This directory is used for Tekton specific functionality:
    - `/tekton/results` is where results are written.
    - There are other subfolders which are implementation details of Tekton.

## [TaskRun](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/taskruns.md)

A TaskRun allows you to instantiate and execute a Task on-cluster. A TaskRun executes the Steps in
the Task in the order they are specified until all Steps have executed successfully or a failure
occurs.

<details><summary>Example</summary><p>

```yaml
apiVersion: tekton.dev/v1beta1
kind: TaskRun
metadata:
  name: echo-hello-world-task-run
spec:
  taskRef:
    name: echo-hello-world
```

To run:

```shell
$ kubectl apply -f hello-world-task.yaml
...

$ kubectl get pods
NAME                                  READY   STATUS     RESTARTS   AGE
echo-hello-world-task-run-pod-x4m2q   0/1     Init:0/1   0          6s

# 2min later
$ kubectl get pods
NAME                                  READY   STATUS      RESTARTS   AGE
echo-hello-world-task-run-pod-x4m2q   0/1     Completed   0          108s

$ tkn taskrun describe echo-hello-world
...
```
</p></details></br>

A TaskRun declaration contains following core elements:
- Task: User can reference a Task using `taskRef` or embed a Task via `taskSpec`.
- Parameters: To supply parameters to Task.
- Resources: If a Task requires Resources (that is, inputs and outputs) you must specify them in your
  TaskRun definition. You can specify Resources by reference to existing PipelineResource objects or
  embed their definitions directly in the TaskRun, i.e. `resourceRef`, or `resourceSpec`.
- PodTemplate: You can specify a Pod template configuration that will serve as the configuration
  starting point for the Pod in which the container images specified in your Task will execute. This
  allows you to customize the Pod confguration specifically for that TaskRun.
- Workspaces: If a Task specifies one or more Workspaces, you must map those Workspaces to the
  corresponding physical volumes in your TaskRun definition, e.g. map PVC to a workspace.
- LimitRange: Tekton only requests the maximum values for CPU, memory, and ephemeral storage from
  within each Step. It will respect LimitRange set in a namespace (choose the mimimal).

Additional features include:
- Configuring the failure timeout
- Monitoring execution status
  - Monitoring Steps
  - Monitoring Results
- Cancelling a TaskRun: set `spec.status` to `TaskRunCancelled`

A few more details:
- The initialization step runs an init container from `tektoncd/pipeline/cmd/entrypoint`, and use
  the same to overwrite container's entrypoint.
- It's common to reuse a Task: simply pass different params and resources in TaskRun.

## [PipelineResources](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/resources.md)

PipelineResources in a pipeline are the set of objects that are going to be used as inputs to a Task
and can be output by a Task, e.g.

<details><summary>Example</summary><p>

```yaml
apiVersion: tekton.dev/v1alpha1
kind: PipelineResource
metadata:
  name: skaffold-git
spec:
  type: git
  params:
    - name: revision
      value: master
    - name: url
      value: https://github.com/GoogleContainerTools/skaffold
---
apiVersion: tekton.dev/v1alpha1
kind: PipelineResource
metadata:
  name: skaffold-image-leeroy-web
spec:
  type: image
  params:
    - name: url
      value: gcr.io/<use your project>/leeroy-web
---
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: build-docker-image-from-git-source
spec:
  params:
    - name: pathToDockerFile
      type: string
      description: The path to the dockerfile to build
      default: $(resources.inputs.docker-source.path)/Dockerfile
    - name: pathToContext
      type: string
      description: |
        The build context used by Kaniko
        (https://github.com/GoogleContainerTools/kaniko#kaniko-build-contexts)
      default: $(resources.inputs.docker-source.path)
  resources:
    inputs:
      - name: docker-source
        type: git
    outputs:
      - name: builtImage
        type: image
  steps:
    - name: build-and-push
      image: gcr.io/kaniko-project/executor:v0.17.1
      # specifying DOCKER_CONFIG is required to allow kaniko to detect docker credential
      env:
        - name: "DOCKER_CONFIG"
          value: "/tekton/home/.docker/"
      command:
        - /kaniko/executor
      args:
        - --dockerfile=$(params.pathToDockerFile)
        - --destination=$(resources.outputs.builtImage.url)
        - --context=$(params.pathToContext)
```

</p></details></br>

Input resources, like source code (git) or artifacts, are dumped at path `/workspace/task_resource_name`
within a mounted volume and are available to all steps of your Task. The path that the resources are
mounted at can be overridden with the targetPath field. If targetPath is set, the resource will be
initialized under `/workspace/targetPath`. If targetPath is not specified, the resource will be
initialized under `/workspace`.

PipelineResources might associate with certain credentials, like login credential for docker registry.
These credentials are not set in PipelineResources directly, but rather with TaskRun. Similar, if
TaskRun needs to access Kubernetes resources, the ServiceAccount must be bound to an appropriate Role.
The workflow in Tekton is to:
- create a Kubernetes Secret with the credential
- create a Kubernetes ServiceAccount referencing the Secret
- associate the ServiceAccount with TaskRun

Currently, PipelineResources contains:
- Git Resource: The git resource represents a git repository, that contains the source code to be built by the pipeline.
- Pull Request Resource: The pullRequest resource represents a pull request event from a source control system.
- Image Resource: An image resource represents an image that lives in a remote repository, usually for pushing image.
- Cluster Resource: A cluster resource represents a Kubernetes cluster, usually for deploying application.
- Storage Resource: The storage resource represents blob storage; it will automatically download the blob if any.
- Cloud Event Resource: The cloudevent resource represents a cloud event that is sent to a target URI upon completion of a TaskRun.

**PipelineResource is the only alpha-level core CRD, see [here](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/resources.md#why-arent-pipelineresources-in-beta).**

## [Pipeline](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/pipelines.md)

A Pipeline is a collection of Tasks that you define and arrange in a specific order of execution as
part of your continuous integration flow. Each Task in a Pipeline executes as a Pod on your Kubernetes
cluster. You can configure various execution conditions to fit your business needs.

Pipeline spec shares similar structures as Task spec, notably `resources` and `params`. Pipeline
resources and params will be given from PipelineRun, and will then be passed to Task.

<details><summary>Example</summary><p>

```yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: tutorial-pipeline
spec:
  resources:
    - name: source-repo
      type: git
    - name: web-image
      type: image
  tasks:
    - name: build-skaffold-web
      taskRef:
        name: build-docker-image-from-git-source
      params:
        - name: pathToDockerFile
          value: Dockerfile
        - name: pathToContext
          value: /workspace/docker-source/examples/microservices/leeroy-web #configure: may change according to your source
      resources:
        inputs:
          - name: docker-source
            resource: source-repo
        outputs:
          - name: builtImage
            resource: web-image
    - name: deploy-web
      taskRef:
        name: deploy-using-kubectl
      resources:
        inputs:
          - name: source
            resource: source-repo
          - name: image
            resource: web-image
            from:
              - build-skaffold-web
      params:
        - name: path
          value: /workspace/source/examples/microservices/leeroy-web/kubernetes/deployment.yaml #configure: may change according to your source
        - name: yamlPathToImage
          value: "spec.template.spec.containers[0].image"
```

</p></details></br>

A Pipeline declaration contains following core elements:
- Resources: provide inputs and store outputs for the Tasks that comprise it.
- Workspaces: specify one or more volumes that each Task in the Pipeline requires during execution.
- Parameters: supply parameters to the Pipeline at execution time.
- Conditions: the `conditions` field allows you to list a series of references to Conditions CRD that
  are run before the task is run. If all of the conditions evaluate to true, the task is run. If any
  of the conditions are false, the Task is not run.
- Adding Tasks to the Pipeline:
  - Using the from parameter
  - Using the runAfter parameter
  - Using the retries parameter
  - Specifying execution conditions
  - Configuring the failure timeout
  - Configuring execution results at the Task level
- Configuring execution results at the Pipeline level

## [PipelineRun](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/pipelineruns.md)

A PipelineRun allows you to instantiate and execute a Pipeline on-cluster. A Pipeline specifies one
or more Tasks in the desired order of execution. A PipelineRun executes the Tasks in the Pipeline in
the order they are specified until all Tasks have executed successfully or a failure occurs.

The PipelineRun automatically defines a corresponding TaskRun for each Task you have defined in your
Pipeline, and collects the results of executing each TaskRun.

<details><summary>Example</summary><p>

```
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  name: tutorial-pipeline-run-1
spec:
  serviceAccountName: tutorial-service
  pipelineRef:
    name: tutorial-pipeline
  resources:
    - name: source-repo
      resourceRef:
        name: skaffold-git
    - name: web-image
      resourceRef:
        name: skaffold-image-leeroy-web
```

Many of the core elements in PipelineRun are similar to TaskRun.

</p></details></br>

## [Conditions](https://github.com/tektoncd/pipeline/blob/v0.12.0/docs/conditions.md)

Condition is a CRD in Tekton, it is referenced in Pipeline and allows Pipeline to execute tasks
based on certain conditions.

The only required fields (apart name, etc) in Condition is the `check` field, which defines a
container image to run and optionally, a script. Condintion can reference resources if needed.
The output of the container will be used as the condition.

<details><summary>Example</summary><p>

```yaml
apiVersion: tekton.dev/v1alpha1
kind: Condition
metadata:
  name: file-exists
spec:
  params:
    - name: "path"
  resources:
    - name: workspace
      type: git
  check:
    image: alpine
    script: 'test -f $(resources.workspace.path)/$(params.path)'
```

</p></details></br>

# Experiments (v0.12.0)

Tekton installation is as simple as applying a manifest:

<details><summary>Installation</summary><p>

```sh
$ kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/previous/v0.12.0/release.yaml
namespace/tekton-pipelines created
podsecuritypolicy.policy/tekton-pipelines created
clusterrole.rbac.authorization.k8s.io/tekton-pipelines-controller-cluster-access created
clusterrole.rbac.authorization.k8s.io/tekton-pipelines-controller-tenant-access created
clusterrole.rbac.authorization.k8s.io/tekton-pipelines-webhook-cluster-access created
role.rbac.authorization.k8s.io/tekton-pipelines-controller created
role.rbac.authorization.k8s.io/tekton-pipelines-webhook created
serviceaccount/tekton-pipelines-controller created
serviceaccount/tekton-pipelines-webhook created
clusterrolebinding.rbac.authorization.k8s.io/tekton-pipelines-controller-cluster-access created
clusterrolebinding.rbac.authorization.k8s.io/tekton-pipelines-controller-tenant-access created
clusterrolebinding.rbac.authorization.k8s.io/tekton-pipelines-webhook-cluster-access created
rolebinding.rbac.authorization.k8s.io/tekton-pipelines-controller created
rolebinding.rbac.authorization.k8s.io/tekton-pipelines-webhook created
customresourcedefinition.apiextensions.k8s.io/clustertasks.tekton.dev created
customresourcedefinition.apiextensions.k8s.io/conditions.tekton.dev created
customresourcedefinition.apiextensions.k8s.io/images.caching.internal.knative.dev created
customresourcedefinition.apiextensions.k8s.io/pipelines.tekton.dev created
customresourcedefinition.apiextensions.k8s.io/pipelineruns.tekton.dev created
customresourcedefinition.apiextensions.k8s.io/pipelineresources.tekton.dev created
customresourcedefinition.apiextensions.k8s.io/tasks.tekton.dev created
customresourcedefinition.apiextensions.k8s.io/taskruns.tekton.dev created
secret/webhook-certs created
validatingwebhookconfiguration.admissionregistration.k8s.io/validation.webhook.pipeline.tekton.dev created
mutatingwebhookconfiguration.admissionregistration.k8s.io/webhook.pipeline.tekton.dev created
validatingwebhookconfiguration.admissionregistration.k8s.io/config.webhook.pipeline.tekton.dev created
clusterrole.rbac.authorization.k8s.io/tekton-aggregate-edit created
clusterrole.rbac.authorization.k8s.io/tekton-aggregate-view created
configmap/config-artifact-bucket created
configmap/config-artifact-pvc created
configmap/config-defaults created
configmap/feature-flags created
configmap/config-leader-election created
configmap/config-logging created
configmap/config-observability created
deployment.apps/tekton-pipelines-controller created
service/tekton-pipelines-controller created
deployment.apps/tekton-pipelines-webhook created
service/tekton-pipelines-webhook created
```

</p></details></br>

Tekton creates a bunch of underline resources, most of them are configs.

<details><summary>Resources</summary><p>

```
$ kubectl get crds
NAME                                  CREATED AT
clustertasks.tekton.dev               2020-05-10T14:01:05Z
conditions.tekton.dev                 2020-05-10T14:01:05Z
images.caching.internal.knative.dev   2020-05-10T14:01:05Z
pipelineresources.tekton.dev          2020-05-10T14:01:05Z
pipelineruns.tekton.dev               2020-05-10T14:01:05Z
pipelines.tekton.dev                  2020-05-10T14:01:05Z
taskruns.tekton.dev                   2020-05-10T14:01:05Z
tasks.tekton.dev                      2020-05-10T14:01:05Z


$ kubectl get all -n tekton-pipelines
NAME                                              READY   STATUS    RESTARTS   AGE
pod/tekton-pipelines-controller-5d76dbf8b-dc4x6   1/1     Running   0          13m
pod/tekton-pipelines-webhook-c6c57f76-vwl2p       1/1     Running   0          13m


NAME                                  TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                     AGE
service/tekton-pipelines-controller   ClusterIP   10.0.0.20    <none>        9090/TCP                    13m
service/tekton-pipelines-webhook      ClusterIP   10.0.0.164   <none>        9090/TCP,8008/TCP,443/TCP   13m


NAME                                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/tekton-pipelines-controller   1/1     1            1           13m
deployment.apps/tekton-pipelines-webhook      1/1     1            1           13m

NAME                                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/tekton-pipelines-controller-5d76dbf8b   1         1         1       13m
replicaset.apps/tekton-pipelines-webhook-c6c57f76       1         1         1       13m
```

</p></details></br>

In Tekton, a lot of configurations can be set via configmaps, notably:
- use `config-artifact-bucket` to set bucket store for artifacts
- use `config-artifact-pvc` to set PV for artifacts
- use `config-defautls` to set pipeline resources created from Tekton
- use `feature-flags` to configure Tekton controller behaviors
- etc

```
$ kubectl get cm -n tekton-pipelines
NAME                     DATA   AGE
config-artifact-bucket   0      14m
config-artifact-pvc      0      14m
config-defaults          1      14m
config-leader-election   4      14m
config-logging           3      14m
config-observability     1      14m
feature-flags            2      14m
```
