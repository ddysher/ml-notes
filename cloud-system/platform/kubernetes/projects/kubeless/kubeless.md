<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [kubeless v0.0.13](#kubeless-v0013)
  - [kubeless v1.0.0-alpha](#kubeless-v100-alpha)
- [Experiment](#experiment)
  - [kubeless v0.0.13](#kubeless-v0013-1)
  - [kubeless v1.0.0-alpha](#kubeless-v100-alpha-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## kubeless v0.0.13

*Date: 06/15/2017, v0.0.13*

kubeless is a project running on top of kubernetes to provide serverless function, or FaaS. It
creates a custom resource `Function`, and have a kubeless controller watching function resource.

When user creates a function via kubeless, kubeless command will create a resource of kind `Function`
with user provided specifications (e.g. runtime, handler, etc). kubeless controller is notified about
the resource creation, then creates a deployment with one pod for this function, along with a
configmap for the above specification. The pod has init container defined, which mounts the same
volume as regular containers, and install runtimes, e.g. for python runtime, it will run command:

```
pip install --prefix=/pythonpath -r /requirements/requirements.txt'.
```

This will install necessary libraries for the function. The image of regular container is created
by kubeless project; it will load source file from mounted directory (`/kubeless`), and runs a
custom script to handle request. For http trigger, it runs bottle framework to accept requests and
pass request to user handler; for pubsub trigger, it runs kafka consumer client and pass topic data
to user handler. For more information, see `kubeless/docker/`.

## kubeless v1.0.0-alpha

*Date: 11/04/2018, v1.0.0-alpha*

kubeless has an in-depth introduction to its [architecture](https://github.com/kubeless/kubeless/blob/v1.0.0-alpha.8/docs/architecture.md).
Following is a quick summary:

Core concept:
- Function: Piece of code to execute, created as CRDs
- Trigger: Event source of functions, one CRD per trigger. This is added in new kubeless versions.
- Runtime: Runtime doesn't have CRDs; instead it is an environment representation. It Represents
  language and runtime specific environment in which function will be executed.

Takeaways:
- Function CRD specification contains full `Deployment`, `Service` and `HorizontalPodAutoscaler`
  definition; however, as shown in experiment, Function CRD doesn't store any information, it's just
  an empty deployement, service, etc.
- Function CRD specification contains full user file content, as well as handler name, check sum, etc
- Runtime image used for the function deployment could be chosen by one of the below options:
  - User explicitly specifies custom runtime image to be used for the function (set function.deployment.xxx.image)
  - Image artifact is generated on the fly by the function builder
  - A pre-built image is used for each language and version combination. A configmap is used to inject
    the function code from function.spec.function into the corresponding Kubernetes runtime pod.
- There are three Trigger CRDs: http, cronjob, kafka, each has a function name and corresponding
  trigger condition, e.g. for http, function is ran everytime a url in the spec is accessed.

# Experiment

## kubeless v0.0.13

Install and deploy a function.

```
# Create a PV first, used by kafka.
$ kubectl create -f pv-hostpath.yaml

# This will create:
#   1. kubeless controller (deployment)
#   2. kafka statefulset
#   3. zookeeper statefulset
#   4. 'function' thirdparty resource.
$ kubeless install

# Inspect the resources
$ kubectl get deployment -n kubeless
NAME                  DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
kubeless-controller   1         1         1            1           22m

$ kubectl get statefulset -n kubeless
NAME      DESIRED   CURRENT   AGE
kafka     1         1         22m
zoo       1         1         22m

$ kubectl get thirdpartyresources
NAME              DESCRIPTION                                     VERSION(S)
function.k8s.io   Kubeless: Serverless framework for Kubernetes   v1

$ kubectl get pods -n kubeless
NAME                                   READY     STATUS    RESTARTS   AGE
kafka-0                                1/1       Running   0          22m
kubeless-controller-3331951411-npgqk   1/1       Running   0          22m
zoo-0                                  1/1       Running   0          22m
```

**http trigger**

```
# Now deploy a 'hello-world' function. kubeless function deploy will
# create a 'function' resource in kubernetes, which has the kind
# Function.v1.k8s.io.
kubeless function deploy get-python \
         --runtime python27 \
         --handler test.foobar \
         --from-file test.py \
         --trigger-http

# Kubeless creates a 'get-python' function and respective deployment.
$ kubectl get function
NAME         KIND
get-python   Function.v1.k8s.io

$ kubectl get deployment
NAME         DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
get-python   1         1         1            1           12m

$ kubectl get pods
NAME                          READY     STATUS    RESTARTS   AGE
get-python-1265444380-htbzz   1/1       Running   0          11m

# Our code locates at /kubeless.
$ kubectl exec -it get-python-1265444380-htbzz sh
/ # ls
bin          home         lib          mnt          run          sys          var
dev          kubeless     linuxrc      proc         sbin         tmp
etc          kubeless.py  media        root         srv          usr
/ # ls kubeless
handler           requirements.txt  test.py

# Now we can call our function
$ kubeless function call get-python --data '{"echo": "echo echo"}'
```

**pubsub trigger**

```
# This is a shortcut for creating a topic in kafka.
$ kubeless topic create new-topic

$ kubeless function deploy pubsub \
    --runtime python27 \
    --handler test.foobar \
    --from-file test.py \
    --trigger-topic "new-topic"

$ kubectl get pods --all-namespaces
NAMESPACE     NAME                                   READY     STATUS    RESTARTS   AGE
default       get-python-1265444380-htbzz            1/1       Running   0          1h
default       pubsub-912430680-0fwd2                 1/1       Running   0          18m

# This is a shortcut for publishing data to a topic.
kubeless topic publish --topic new-topic --data "hello"

# Now we'll be able to see logs from the pubsub pod.
```

## kubeless v1.0.0-alpha

Installation:

```
kubectl create ns kubeless
kubectl create -f https://github.com/kubeless/kubeless/releases/download/v1.0.0-alpha.8/kubeless-v1.0.0-alpha.8.yaml

$ kubectl get deployment -n kubeless
NAME                          DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
kubeless-controller-manager   1         1         1            1           1h

$ kubectl get customresourcedefinition
NAME                          AGE
cronjobtriggers.kubeless.io   1h
functions.kubeless.io         1h
httptriggers.kubeless.io      1h
```

All the available runtimes are represented as images in configmap.

```
$ kubectl get configmap -n kubeless
NAME              DATA   AGE
kubeless-config   10     1h
```

Deploy a function. A couple of resources are created on behalf of the function:
- Deployment: create long-running pods to deal with requests, and image runtime comes from configmap
- Service: expose pod service
- Configmap: save file content

```
$ kubeless function deploy hello --runtime python2.7 --from-file test.py --handler test.hello
INFO[0000] Deploying function...
INFO[0000] Function hello submitted for deployment
INFO[0000] Check the deployment status executing 'kubeless function ls hello'

$ kubectl get deployment
NAME    DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
hello   1         1         1            1           5m52s

$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
hello-7fb7fcfb97-hv92g   1/1     Running   0          5m47s

$ kubectl get service
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
hello        ClusterIP   10.0.0.173   <none>        8080/TCP   6m28s
kubernetes   ClusterIP   10.0.0.1     <none>        443/TCP    8m9s

$ kubectl get configmap
NAME    DATA   AGE
hello   3      6m48s

$ kubectl get function
NAME    AGE
hello   31s
```

The funtion yaml contains empty deployment, service, etc:

```
$ kubectl get function hello -o yaml
apiVersion: kubeless.io/v1beta1
kind: Function
metadata:
  creationTimestamp: 2018-11-05T13:47:58Z
  finalizers:
  - kubeless.io/function
  generation: 1
  labels:
    created-by: kubeless
    function: hello
  name: hello
  namespace: default
  resourceVersion: "349"
  selfLink: /apis/kubeless.io/v1beta1/namespaces/default/functions/hello
  uid: 675a8d48-e101-11e8-b31a-1c1b0d57c021
spec:
  checksum: sha256:e4eaa2dc4bd2a3f95a04df0e29c0c82ec2691c52da24b03ca6ad4b8f4d134daf
  deployment:
    metadata:
      creationTimestamp: null
    spec:
      strategy: {}
      template:
        metadata:
          creationTimestamp: null
        spec:
          containers:
          - imagePullPolicy: Always
            name: ""
            resources: {}
    status: {}
  deps: ""
  function: |
    def hello(event, context):
      print event
      return event['data']
  function-content-type: text
  handler: test.hello
  horizontalPodAutoscaler:
    metadata:
      creationTimestamp: null
    spec:
      maxReplicas: 0
      scaleTargetRef:
        kind: ""
        name: ""
    status:
      conditions: null
      currentMetrics: null
      currentReplicas: 0
      desiredReplicas: 0
  runtime: python2.7
  service:
    ports:
    - name: http-function-port
      port: 8080
      protocol: TCP
      targetPort: 8080
    selector:
      created-by: kubeless
      function: hello
    type: ClusterIP
  timeout: "
```
