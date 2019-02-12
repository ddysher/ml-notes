<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
- [Features](#features)
- [Components](#components)
- [Related Projects](#related-projects)
  - [Argo CI (10/02/2018, no release)](#argo-ci-10022018-no-release)
  - [Argo CD (10/02/2018, v0.9.2)](#argo-cd-10022018-v092)
  - [Argo Event (10/02/2018, v0.5)](#argo-event-10022018-v05)
- [Experiments (with implementation details)](#experiments-with-implementation-details)
  - [Installation](#installation)
  - [Hello world](#hello-world)
  - [Parameters](#parameters)
  - [Script output](#script-output)
  - [More examples](#more-examples)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 02/15/2018, v2.0.0*
- *Date: 05/10/2020, v2.8.0*

Argo is an open source project to provide container-native workflows for Kubernetes. A workflow is
composed of one or more sequential and/or parallel steps. Eash step is implemented as a container
and workflows may be arbitrarily nested.

Argo V2 is implemented as a Kubernetes CRD (Custom Resource Definition). As a result, Argo workflows
can be managed using kubectl and natively integrates with other Kubernetes services such as volumes,
secrets, and RBAC.

The Argo V2 software is lightweight, installs in seconds, and provides complete workflow features
including parameter substitution, artifacts, scripting, loops, and recursive workflows.

- Define workflows where each step in the workflow is a container.
- Model multi-step workflows as a sequence of tasks or capture the dependencies between tasks using a graph (DAG).
- Easily run compute intensive jobs for machine learning or data processing in a fraction of the time using Argo workflows on Kubernetes.
- Run CI/CD pipelines natively on Kubernetes without configuring complex software development products.

# Concepts

**Template**

- A composable, reusable definition of a workflow or step within a workflow with support for parameterization.
- Defined as a container, script (e.g. bash, python, javascript), or a series of workflow steps.
- Accepts input parameters/artifacts and produce output parameters/artifacts.

**Step**

- A unit of execution in an Argo workflow.
- Represents a container, or defies a series of steps (e.g. nested workflows).

In argo, steps (including DAG, scripts, etc) are represented as nodes.

<details><summary>steps node yaml, see "status" field</summary><p>

```yaml
$ kubectl get workflow steps-bdvjc -o yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  creationTimestamp: 2018-10-02T07:49:41Z
  generateName: steps-
  generation: 1
  labels:
    workflows.argoproj.io/phase: Running
  name: steps-bdvjc
  namespace: default
  resourceVersion: "19970"
  selfLink: /apis/argoproj.io/v1alpha1/namespaces/default/workflows/steps-bdvjc
  uid: b8378f2b-c617-11e8-b3ad-2c4d54ed3845
spec:
  arguments: {}
  entrypoint: hello-hello-hello
  templates:
  - inputs: {}
    metadata: {}
    name: hello-hello-hello
    outputs: {}
    steps:
    - - arguments:
          parameters:
          - name: message
            value: hello1
        name: hello1
        template: whalesay
    - - arguments:
          parameters:
          - name: message
            value: hello2a
        name: hello2a
        template: whalesay
      - arguments:
          parameters:
          - name: message
            value: hello2b
        name: hello2b
        template: whalesay
  - container:
      args:
      - '{{inputs.parameters.message}}'
      command:
      - cowsay
      image: docker/whalesay
      name: ""
      resources: {}
    inputs:
      parameters:
      - name: message
    metadata: {}
    name: whalesay
    outputs: {}
status:
  finishedAt: null
  nodes:
    steps-bdvjc:
      children:
      - steps-bdvjc-1634307304
      displayName: steps-bdvjc
      finishedAt: null
      id: steps-bdvjc
      name: steps-bdvjc
      phase: Running
      startedAt: 2018-10-02T07:49:41Z
      templateName: hello-hello-hello
      type: Steps
    steps-bdvjc-627503069:
      boundaryID: steps-bdvjc
      children:
      - steps-bdvjc-2472425162
      - steps-bdvjc-2455647543
      displayName: '[1]'
      finishedAt: null
      id: steps-bdvjc-627503069
      name: steps-bdvjc[1]
      phase: Running
      startedAt: 2018-10-02T07:49:48Z
      type: StepGroup
    steps-bdvjc-1175603089:
      boundaryID: steps-bdvjc
      children:
      - steps-bdvjc-627503069
      displayName: hello1
      finishedAt: 2018-10-02T07:49:47Z
      id: steps-bdvjc-1175603089
      inputs:
        parameters:
        - name: message
          value: hello1
      name: steps-bdvjc[0].hello1
      phase: Succeeded
      startedAt: 2018-10-02T07:49:41Z
      templateName: whalesay
      type: Pod
    steps-bdvjc-1634307304:
      boundaryID: steps-bdvjc
      children:
      - steps-bdvjc-1175603089
      displayName: '[0]'
      finishedAt: 2018-10-02T07:49:48Z
      id: steps-bdvjc-1634307304
      name: steps-bdvjc[0]
      phase: Succeeded
      startedAt: 2018-10-02T07:49:41Z
      type: StepGroup
    steps-bdvjc-2455647543:
      boundaryID: steps-bdvjc
      displayName: hello2b
      finishedAt: 2018-10-02T07:49:54Z
      id: steps-bdvjc-2455647543
      inputs:
        parameters:
        - name: message
          value: hello2b
      name: steps-bdvjc[1].hello2b
      phase: Succeeded
      startedAt: 2018-10-02T07:49:48Z
      templateName: whalesay
      type: Pod
    steps-bdvjc-2472425162:
      boundaryID: steps-bdvjc
      displayName: hello2a
      finishedAt: null
      id: steps-bdvjc-2472425162
      inputs:
        parameters:
        - name: message
          value: hello2a
      name: steps-bdvjc[1].hello2a
      phase: Running
      startedAt: 2018-10-02T07:49:48Z
      templateName: whalesay
      type: Pod
  phase: Running
  startedAt: 2018-10-02T07:49:41Z
```

</p></details></br>

**DAG**

As an alternative to specifying sequences of steps, you can define the workflow as a graph by specifying
the dependencies of each task. This can be simpler to maintain for complex workflows and allows for
maximum parallelism when running tasks.

**Pod/Container**

Each pod created to run a step in an Argo workflow consists of the following containers:
- The `main` container which runs the user specified container or script
- The `wait` sidecar container saves any output artifacts/parameters produced by the main container
- An optional `init` container which loads any input artifacts and makes them available to the main container
- Additional user specified sidecar containers to provide supporting role to the main container (e.g. docker-in-docker, database, etc)

For more information, see Experiments section.

**Parameter**

The Argo CLI allows users to specify values for parameterized workflows before they are submitted
to Kubernetes.

**Artifact**

- A collection of files/directories that can be used as inputs or outputs to a step in a workflow.
- Support for Git, HTTP, S3, Artifactory.

**Artifact Repository**

- A long term persistent storage of artifacts.
- Support for S3, Artifactory.

# Features

- DAG or Steps based declaration of workflows
- Artifact support (S3, Artifactory, HTTP, Git, raw)
- Step level input & outputs (artifacts/parameters)
- Loops
- Parameterization
- Conditionals
- Timeouts (step & workflow level)
- Retry (step & workflow level)
- Resubmit (memoized)
- Suspend & Resume
- Cancellation
- K8s resource orchestration
- Exit Hooks (notifications, cleanup)
- Garbage collection of completed workflow
- Scheduling (affinity/tolerations/node selectors)
- Volumes (ephemeral/existing)
- Parallelism limits
- Daemoned steps
- DinD (docker-in-docker)
- Script steps

# Components

**argo**

The command line interface.

**argoexec**

argoexec is the executor sidecar to workflow containers, it has:
- a `init` command to load artifacts
- a `wait` command to save artifacts/parameters

**argo-ui**

argo-ui serves a web-based UI for argo. It starts an API server for argo APIs, which uses kubernetes
javascript client to access CRDs.

**workflow controller**

Workflow controller is the core component in argo, it:
- watches Workflow CRD and Pod from Kubernetes
- once there is a new Workflow, it is responsible to parse the spec and launch Pods
- when any Pod completed, it requeues corresponding Workflow and processes it again

# Related Projects

## Argo CI (10/02/2018, no release)

argo-ci is basically a wrapper (written in typescript) around argo workflow, ref [design diagram](https://github.com/argoproj/argo-ci/blob/9dc090722e0508fc6fd19c686a02d82d1ca596f8/docs/v1-alpha1-design.png).

User configures scm system, e.g. GitHub to send event to argo-ci webhook server, which checks ci.yaml
and code, then creates argo workflow to kuberntes cluster. argo-ci uses exit-handler feature to post
status to GitHub.

<details><summary>ci.yaml for argo</summary><p>

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: argo-ci-
spec:
  entrypoint: argo-ci
  arguments:
    parameters:
    - name: revision
      value: master
    - name: repo
      value: https://github.com/argoproj/argo.git

  templates:
  - name: argo-ci
    steps:
    - - name: build
        template: ci-dind
        arguments:
          parameters:
          - name: cmd
            value: "{{item}}"
        withItems:
        - make controller-image executor-image
        - make cli-linux
        - make cli-darwin
      - name: test
        template: ci-builder
        arguments:
          parameters:
          - name: cmd
            value: "{{item}}"
        withItems:
        - dep ensure && make lint test verify-codegen

  - name: ci-builder
    inputs:
      parameters:
      - name: cmd
      artifacts:
      - name: code
        path: /go/src/github.com/argoproj/argo
        git:
          repo: "{{workflow.parameters.repo}}"
          revision: "{{workflow.parameters.revision}}"
    container:
      image: argoproj/argo-ci-builder:latest
      command: [sh, -c]
      args: ["{{inputs.parameters.cmd}}"]
      workingDir: /go/src/github.com/argoproj/argo

  - name: ci-dind
    inputs:
      parameters:
      - name: cmd
      artifacts:
      - name: code
        path: /go/src/github.com/argoproj/argo
        git:
          repo: "{{workflow.parameters.repo}}"
          revision: "{{workflow.parameters.revision}}"
    container:
      image: argoproj/argo-ci-builder:latest
      command: [sh, -c]
      args: ["until docker ps; do sleep 3; done && {{inputs.parameters.cmd}}"]
      workingDir: /go/src/github.com/argoproj/argo
      env:
      - name: DOCKER_HOST
        value: 127.0.0.1
    sidecars:
    - name: dind
      image: docker:17.10-dind
      securityContext:
        privileged: true
      mirrorVolumeMounts: true
```

</p></details></br>

## Argo CD (10/02/2018, v0.9.2)

argo-cd repository has an introduction to its [architecture](https://github.com/argoproj/argo-cd/blob/v0.9.2/docs/architecture.md),
and [getting started guide](https://github.com/argoproj/argo-cd/blob/v0.9.2/docs/getting_started.md).
Note that argo-cd is different from other cd system in that:
- it mainly tracks kubernetes resource manifests changes (instead of just code changes)
- it proactively fetches git status (not just [webhook event](https://github.com/argoproj/argo-cd/blob/v0.9.2/docs/webhook.md))

**API Server**

The API server is a gRPC/REST server which exposes the API consumed by the Web UI, CLI, and CI/CD
systems. Additions to above architecture doc:
- API server has a fake 'database' with two types: `Repository` and `Cluster`, which is backed by Kubernetes Secret.

**Repository Server**

The repository server is an internal service which maintains a local cache of the git repository
holding the application manifests.

ref: https://github.com/argoproj/argo-cd/issues/143

**Application Controller**

The application controller is a Kubernetes controller which continuously monitors running applications
and compares the current, live state against the desired target state (as specified in the git repo).

**Application CRD**

The Application CRD is the Kubernetes resource object representing a deployed application instance
in an environment. It is defined by two key pieces of information:
- `source` reference to the desired state in git (repository, revision, path, environment)
- `destination` reference to the target cluster and namespace.

There's also a [tracking strategies](https://github.com/argoproj/argo-cd/blob/v0.9.2/docs/tracking_strategies.md).

**AppProject CRD**

The AppProject CRD is the Kubernetes resource object representing a grouping of applications. It is
defined by three key pieces of information.

## Argo Event (10/02/2018, v0.5)

Argo Events is an open source event-based dependency manager for Kubernetes.

- Sensors define a set of dependencies (inputs) and actions (outputs). The sensor's actions will
  only be triggered after it's dependencies have been resolved.
- Triggers are the sensor's actions. Triggers are only executed after all of the sensor's signals
  have been resolved.
- A gateway is a long running/repeatable process whose tasks are to process and transform either
  the internally produced events or incoming events into the [cloudevents specification](https://github.com/cloudevents/spec)
  compliant events and dispatching them to sensors.
  - gateway-processor: either generates the events internally or listens to incoming events
  - gateway-transformer: transforms the incoming event from gateway-processor into a cloudevents
    specification compliant event.

To simply put, `sensor` depends on multiple `gateways` and once all gateways are fired, it triggers
actions set in `trigger`.

*References*:
- [sensor guide](https://github.com/argoproj/argo-events/blob/3272f1f0b8dc5fbe62d80da0aa41454b48f4dbb4/docs/sensor-guide.md)
- [trigger guide](https://github.com/argoproj/argo-events/blob/3272f1f0b8dc5fbe62d80da0aa41454b48f4dbb4/docs/trigger-guide.md)
- [gateway guide](https://github.com/argoproj/argo-events/blob/3272f1f0b8dc5fbe62d80da0aa41454b48f4dbb4/docs/gateway-guide.md)
- [custom gateway guide](https://github.com/argoproj/argo-events/blob/3272f1f0b8dc5fbe62d80da0aa41454b48f4dbb4/docs/custom-gateway.md)

# Experiments (with implementation details)

## Installation

Follow [the link](https://github.com/argoproj/argo/blob/v2.1.0/demo.md) to install argo. The core
command is:

```
$ argo install
$ kubectl create rolebinding default-admin --clusterrole=admin --serviceaccount=default:default
```

After installation, there are two argo components running:
```
$ kubectl get deployment --all-namespaces
NAMESPACE     NAME                  DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
kube-system   argo-ui               1         1         1            1           1m
kube-system   kube-dns              1         1         1            1           6m
kube-system   workflow-controller   1         1         1            1           1m
```

N.b. `argo install` will be removed in favor of `kubectl apply`, ref: https://github.com/argoproj/argo/issues/928

**Misc Notes**

Tiller requires RBAC:

```console
$ kubectl create serviceaccount tiller --namespace kube-system
$ kubectl create clusterrolebinding tiller --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
$ helm init --service-account tiller
```

Run `minio` with NodePort (for local cluster):

```
$ helm install stable/minio --name argo-artifacts --set serviceType=NodePort
```

## Hello world

Create the `hello world` workflow, then we'll see a `Workflow` CR created:

```
$ kubectl create -f 1.hello-world.yaml

$ kubectl get workflow --all-namespaces
NAMESPACE   NAME                AGE
default     hello-world-gqld8   4m
```

The pod contains two containers:
- one that we submitted through workflow template, i.e. `docker/whalesay:latest`
- the other runs `argo wait` from image `argoproj/argoexec:v2.1.0`, and has a lot volumes & env mounted

Here is what the `argo wait` does:

```go
# path: cmd/argoexec/commands/wait.go

func waitContainer() error {
	wfExecutor := initExecutor()
	defer wfExecutor.HandleError()
	defer stats.LogStats()
	stats.StartStatsTicker(5 * time.Minute)

	// Wait for main container to complete and kill sidecars
	err := wfExecutor.Wait()
	if err != nil {
		wfExecutor.AddError(err)
		// do not return here so we can still try to save outputs
	}
	logArt, err := wfExecutor.SaveLogs()
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	err = wfExecutor.SaveArtifacts()
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	// Saving output parameters
	err = wfExecutor.SaveParameters()
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	// Capture output script result
	err = wfExecutor.CaptureScriptResult()
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	err = wfExecutor.AnnotateOutputs(logArt)
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	return nil
}
```

Note, argo has an `executor` (workflow executor) struct which wraps different container runtime
executor, e.g. docker, kubelet. In the code block above, the workflow executor is named `wfExecutor`.
Below, when we say `executor`, we mean workflow executor, but a lot container related operations
are done in container runtime executor.

- `Wait`: Executor queries main container status, and only return if main container exits.
- `SaveLogs`: Executor fetches main container logs and save to its own (sidecar) path: `/argo/output/logs/main.log`.
  If artifact repository is configured, then executor will save the file there.
- `SaveArtifacts`: If `outputs.artifacts.path` in our template is not empty, executor will also save
  artifacts to artifact repository. Artifact is saved as tar file.
- `SaveParameters`: If `outputs.parameters` in our template is not empty, executor will add the
  parameters to in-memory template, i.e. `we.Template.Outputs.Parameters[i].Value = &output`
- `CaptureScriptResult`: Executor will add the stdout of a script template to in-memory template,
  i.e. `we.Template.Outputs.Result = &out`, where `out = we.RuntimeExecutor.GetOutput(mainContainerID)`.
- `AnnotateOutputs`: If a workflow uses script, executor will add annotation to pod with script output.

<details><summary>pod yaml</summary><p>

```yaml
$ kubectl get pods -n default hello-world-gqld8 -o yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    workflows.argoproj.io/node-name: hello-world-gqld8
    workflows.argoproj.io/template: '{"name":"whalesay","inputs":{},"outputs":{},"metadata":{},"container":{"name":"","image":"docker/whalesay:latest","command":["cowsay"],"args":["hello world"],"resources":{}},"archiveLocation":{}}'
  creationTimestamp: 2018-10-02T03:41:53Z
  labels:
    workflows.argoproj.io/completed: "true"
    workflows.argoproj.io/workflow: hello-world-gqld8
  name: hello-world-gqld8
  namespace: default
  ownerReferences:
  - apiVersion: argoproj.io/v1alpha1
    blockOwnerDeletion: true
    controller: true
    kind: Workflow
    name: hello-world-gqld8
    uid: 1a686466-c5f5-11e8-b3ad-2c4d54ed3845
  resourceVersion: "2072"
  selfLink: /api/v1/namespaces/default/pods/hello-world-gqld8
  uid: 1a6ccd83-c5f5-11e8-b3ad-2c4d54ed3845
spec:
  containers:
  - args:
    - hello world
    command:
    - cowsay
    image: docker/whalesay:latest
    imagePullPolicy: Always
    name: main
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-z94kh
      readOnly: true
  - args:
    - wait
    command:
    - argoexec
    env:
    - name: ARGO_POD_IP
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: status.podIP
    - name: ARGO_POD_NAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.name
    - name: ARGO_NAMESPACE
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.namespace
    image: argoproj/argoexec:v2.1.0
    imagePullPolicy: IfNotPresent
    name: wait
    resources: {}
    securityContext:
      privileged: false
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /argo/podmetadata
      name: podmetadata
    - mountPath: /var/lib/docker
      name: docker-lib
      readOnly: true
    - mountPath: /var/run/docker.sock
      name: docker-sock
      readOnly: true
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-z94kh
      readOnly: true
  dnsPolicy: ClusterFirst
  nodeName: 127.0.0.1
  priority: 0
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
  - downwardAPI:
      defaultMode: 420
      items:
      - fieldRef:
          apiVersion: v1
          fieldPath: metadata.annotations
        path: annotations
    name: podmetadata
  - hostPath:
      path: /var/lib/docker
      type: Directory
    name: docker-lib
  - hostPath:
      path: /var/run/docker.sock
      type: Socket
    name: docker-sock
  - name: default-token-z94kh
    secret:
      defaultMode: 420
      secretName: default-token-z94kh
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: 2018-10-02T03:41:53Z
    reason: PodCompleted
    status: "True"
    type: Initialized
  - lastProbeTime: null
    lastTransitionTime: 2018-10-02T03:41:53Z
    reason: PodCompleted
    status: "False"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: null
    reason: PodCompleted
    status: "False"
    type: ContainersReady
  - lastProbeTime: null
    lastTransitionTime: 2018-10-02T03:41:53Z
    status: "True"
    type: PodScheduled
  containerStatuses:
  - containerID: docker://a9e2218a998836f7055012771527febbee06e8d0ae66c283dd1c6e727b91926c
    image: docker/whalesay:latest
    imageID: docker-pullable://docker/whalesay@sha256:178598e51a26abbc958b8a2e48825c90bc22e641de3d31e18aaf55f3258ba93b
    lastState: {}
    name: main
    ready: false
    restartCount: 0
    state:
      terminated:
        containerID: docker://a9e2218a998836f7055012771527febbee06e8d0ae66c283dd1c6e727b91926c
        exitCode: 0
        finishedAt: 2018-10-02T03:41:58Z
        reason: Completed
        startedAt: 2018-10-02T03:41:58Z
  - containerID: docker://293a3c897b1ad058c2cba81496e765a91e1e73a84e9b7c4af02f59b1f8542833
    image: argoproj/argoexec:v2.1.0
    imageID: docker-pullable://argoproj/argoexec@sha256:0dc66b83aa5d2825785b5bf5c720c646894d007c835f836b8f7c124980552bbc
    lastState: {}
    name: wait
    ready: false
    restartCount: 0
    state:
      terminated:
        containerID: docker://293a3c897b1ad058c2cba81496e765a91e1e73a84e9b7c4af02f59b1f8542833
        exitCode: 0
        finishedAt: 2018-10-02T03:42:19Z
        reason: Completed
        startedAt: 2018-10-02T03:42:18Z
  hostIP: 127.0.0.1
  phase: Succeeded
  podIP: 172.17.0.6
  qosClass: BestEffort
  startTime: 2018-10-02T03:41:53Z
```

</p></details></br>

## Parameters

Parameters can be passed/overridden via the argo CLI. To override the printed message, run `argo submit`
with the -p option:
```
$ argo submit 2-arguments-parameters.yaml -p message="goodbye world"
```

The argument is overridden from argo CLI, so there is no way to change the value from server side.

Template is evaluated in `workflow/controller/operator.go#executeTemplate`. In the example, argo
workflow controller uses `fasttemplate` package to expand `container.args` using the global
parameter `message`.

## Script output

We can use script in case pre-defined argo template is not flexible enough to define our steps:

```
$ kubectl create -f 6-script.yaml

$ kubectl get workflow
NAME                 AGE
scripts-bash-nl6vn   9m

$ kubectl get pods
NAME                            READY     STATUS      RESTARTS   AGE
scripts-bash-nl6vn-1779461405   0/2       Completed   0          10m
scripts-bash-nl6vn-2808212750   0/2       Completed   0          10m
```

There are two pods from the output:
- one for running bash script (scripts-bash-nl6vn-2808212750)
- the other for printing message (scripts-bash-nl6vn-1779461405)

For the script pod, we have two containers and one init container:
- init container runs `argoexec init`, which loads script and saves to `/argo/staging/script`
- wait container runs `argoexec wait`, similar to above analysis (script output will be saved to pod annotation)
- script container runs the script `/argo/staging/script`; to share script, init container and script
  container both mount an emptydir to `/argo/staging`

Here is what `argoexec init` does:

```go
# path: cmd/argoexec/commands/init.go

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Load artifacts",
	Run: func(cmd *cobra.Command, args []string) {
		err := loadArtifacts()
		if err != nil {
			log.Fatalf("%+v", err)
		}
	},
}

func loadArtifacts() error {
	wfExecutor := initExecutor()
	defer wfExecutor.HandleError()
	defer stats.LogStats()

	// Download input artifacts
	err := wfExecutor.StageFiles()
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	err = wfExecutor.LoadArtifacts()
	if err != nil {
		wfExecutor.AddError(err)
		return err
	}
	return nil
}
```

<details><summary>script pod yaml</summary><p>

```yaml
$ kubectl get pods scripts-bash-nl6vn-2808212750 -o yaml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    workflows.argoproj.io/node-name: scripts-bash-nl6vn[0].generate
    workflows.argoproj.io/outputs: '{"result":"88"}'
    workflows.argoproj.io/template: '{"name":"gen-random-int","inputs":{},"outputs":{},"metadata":{},"script":{"name":"","image":"debian:9.4","command":["bash"],"resources":{},"source":"cat /dev/urandom | od -N2 -An -i | awk -v f=1 -v r=100 ''{printf \"%i\\n\", f + r * $1 / 65536}''\n"},"archiveLocation":{}}'
  creationTimestamp: 2018-10-02T06:40:45Z
  labels:
    workflows.argoproj.io/completed: "true"
    workflows.argoproj.io/workflow: scripts-bash-nl6vn
  name: scripts-bash-nl6vn-2808212750
  namespace: default
  ownerReferences:
  - apiVersion: argoproj.io/v1alpha1
    blockOwnerDeletion: true
    controller: true
    kind: Workflow
    name: scripts-bash-nl6vn
    uid: 171ff02c-c60e-11e8-b3ad-2c4d54ed3845
  resourceVersion: "14962"
  selfLink: /api/v1/namespaces/default/pods/scripts-bash-nl6vn-2808212750
  uid: 1723ebb9-c60e-11e8-b3ad-2c4d54ed3845
spec:
  containers:
  - args:
    - /argo/staging/script
    command:
    - bash
    image: debian:9.4
    imagePullPolicy: IfNotPresent
    name: main
    resources: {}
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /argo/staging
      name: argo-staging
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-z94kh
      readOnly: true
  - args:
    - wait
    command:
    - argoexec
    env:
    - name: ARGO_POD_IP
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: status.podIP
    - name: ARGO_POD_NAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.name
    - name: ARGO_NAMESPACE
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.namespace
    image: argoproj/argoexec:v2.1.0
    imagePullPolicy: IfNotPresent
    name: wait
    resources: {}
    securityContext:
      privileged: false
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /argo/podmetadata
      name: podmetadata
    - mountPath: /var/lib/docker
      name: docker-lib
      readOnly: true
    - mountPath: /var/run/docker.sock
      name: docker-sock
      readOnly: true
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-z94kh
      readOnly: true
  dnsPolicy: ClusterFirst
  initContainers:
  - args:
    - init
    command:
    - argoexec
    env:
    - name: ARGO_POD_IP
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: status.podIP
    - name: ARGO_POD_NAME
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.name
    - name: ARGO_NAMESPACE
      valueFrom:
        fieldRef:
          apiVersion: v1
          fieldPath: metadata.namespace
    image: argoproj/argoexec:v2.1.0
    imagePullPolicy: IfNotPresent
    name: init
    resources: {}
    securityContext:
      privileged: false
    terminationMessagePath: /dev/termination-log
    terminationMessagePolicy: File
    volumeMounts:
    - mountPath: /argo/podmetadata
      name: podmetadata
    - mountPath: /argo/staging
      name: argo-staging
    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount
      name: default-token-z94kh
      readOnly: true
  nodeName: 127.0.0.1
  priority: 0
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
  - downwardAPI:
      defaultMode: 420
      items:
      - fieldRef:
          apiVersion: v1
          fieldPath: metadata.annotations
        path: annotations
    name: podmetadata
  - hostPath:
      path: /var/lib/docker
      type: Directory
    name: docker-lib
  - hostPath:
      path: /var/run/docker.sock
      type: Socket
    name: docker-sock
  - emptyDir: {}
    name: argo-staging
  - name: default-token-z94kh
    secret:
      defaultMode: 420
      secretName: default-token-z94kh
status:
  conditions:
  - lastProbeTime: null
    lastTransitionTime: 2018-10-02T06:40:46Z
    reason: PodCompleted
    status: "True"
    type: Initialized
  - lastProbeTime: null
    lastTransitionTime: 2018-10-02T06:40:45Z
    reason: PodCompleted
    status: "False"
    type: Ready
  - lastProbeTime: null
    lastTransitionTime: null
    reason: PodCompleted
    status: "False"
    type: ContainersReady
  - lastProbeTime: null
    lastTransitionTime: 2018-10-02T06:40:45Z
    status: "True"
    type: PodScheduled
  containerStatuses:
  - containerID: docker://184deef3e9f0489c2517201674d30ab97a32bb0d7663796a275b2e3ad7663b26
    image: debian:9.4
    imageID: docker-pullable://debian@sha256:6ee341d1cf3da8e6ea059f8bc3af9940613c4287205cd71d7c6f9e1718fdcb9b
    lastState: {}
    name: main
    ready: false
    restartCount: 0
    state:
      terminated:
        containerID: docker://184deef3e9f0489c2517201674d30ab97a32bb0d7663796a275b2e3ad7663b26
        exitCode: 0
        finishedAt: 2018-10-02T06:40:57Z
        reason: Completed
        startedAt: 2018-10-02T06:40:57Z
  - containerID: docker://7fcddcb6720a0fc97a59826141eb975cb55ba27bfd66415927cba34164cf648b
    image: argoproj/argoexec:v2.1.0
    imageID: docker-pullable://argoproj/argoexec@sha256:0dc66b83aa5d2825785b5bf5c720c646894d007c835f836b8f7c124980552bbc
    lastState: {}
    name: wait
    ready: false
    restartCount: 0
    state:
      terminated:
        containerID: docker://7fcddcb6720a0fc97a59826141eb975cb55ba27bfd66415927cba34164cf648b
        exitCode: 0
        finishedAt: 2018-10-02T06:40:59Z
        reason: Completed
        startedAt: 2018-10-02T06:40:58Z
  hostIP: 127.0.0.1
  initContainerStatuses:
  - containerID: docker://2864181e912af73ac4f9fa0510e5ebb61b2f5ed091cfcaee1b97e9d59407fea7
    image: argoproj/argoexec:v2.1.0
    imageID: docker-pullable://argoproj/argoexec@sha256:0dc66b83aa5d2825785b5bf5c720c646894d007c835f836b8f7c124980552bbc
    lastState: {}
    name: init
    ready: true
    restartCount: 0
    state:
      terminated:
        containerID: docker://2864181e912af73ac4f9fa0510e5ebb61b2f5ed091cfcaee1b97e9d59407fea7
        exitCode: 0
        finishedAt: 2018-10-02T06:40:46Z
        reason: Completed
        startedAt: 2018-10-02T06:40:46Z
  phase: Succeeded
  podIP: 172.17.0.6
  qosClass: BestEffort
  startTime: 2018-10-02T06:40:45Z
```

</p></details></br>

## More examples

There are a lot of [examples from argo](https://github.com/argoproj/argo/blob/v2.1.0/examples).
