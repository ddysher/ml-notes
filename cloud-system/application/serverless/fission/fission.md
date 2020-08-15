<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [fission alpha](#fission-alpha)
  - [fission v1-rc1](#fission-v1-rc1)
    - [Components](#components)
    - [New Features](#new-features)
- [Experiment](#experiment)
  - [fission alpha](#fission-alpha-1)
  - [fission v1-rc1](#fission-v1-rc1-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## fission alpha

*Date: 06/15/2017, alpha*

Fission is a fast serverless framework built on top of kubernetes. It has a pool manager which
manages a pool of pods to receive requests, for each env. There is a router that is used to proxy
traffic backend pods: user functions are loaded to the pod upon first request. Fission doesn't
use thirdparty resources; it has its own etcd to store function, route, env, etc. For example,
the following example will yield this result:

```
$ fission env list
NAME   UID                                  IMAGE
nodejs 367bc93e-5784-4d8b-8e72-995f1fbdd873 fission/node-env

$ fission function list
NAME  UID                                  ENV
hello 3bd0a155-f812-45b5-bee1-ed0eeccd6849 nodejs

$ fission route list
NAME                                 METHOD URL    FUNCTION_NAME FUNCTION_UID
2ac1e880-b36f-4ae6-b088-c665e08d0fb7 GET    /hello hello
```

For more information, refer to [fission architecture](https://github.com/fission/fission/blob/0207d13b2323b79fe9caec5d31da3a88f12b840f/Documentation/Architecture.md).
Fission also supports workflow, refer to [fission-workflow](https://github.com/fission/fission-workflows).

Note, fission has later removed etcd and changed to use TPR (then to CRD), ref: https://github.com/fission/fission/pull/266

*Reference*

- https://kubernetes.io/blog/2017/01/fission-serverless-functions-as-service-for-kubernetes/
- https://medium.com/@natefonseka/kubeless-vs-fission-the-kubernetes-serverless-match-up-41f66611f54d

## fission v1-rc1

### Components

*12/22/2018, v1-rc1*

Core concepts:
- A function is a piece of code that follows the fission function interface.
- An environment contains the language- and runtime-specific parts of running a function. An environment is essentially just a container with a webserver and dynamic loader.
- A trigger is something that maps an event to a function.

As of v1-rc1, fission has following CRDs:

```
$ kubectl get crds
NAME                                 CREATED AT
canaryconfigs.fission.io             2018-12-22T00:50:13Z
environments.fission.io              2018-12-22T00:50:13Z
functions.fission.io                 2018-12-22T00:50:13Z
httptriggers.fission.io              2018-12-22T00:50:13Z
kuberneteswatchtriggers.fission.io   2018-12-22T00:50:13Z
messagequeuetriggers.fission.io      2018-12-22T00:50:13Z
packages.fission.io                  2018-12-22T00:50:13Z
recorders.fission.io                 2018-12-22T00:50:13Z
timetriggers.fission.io              2018-12-22T00:50:13Z
```

- Function: describes the contents of the function. A function has references (kind/namespace/name) to environment, secret, configmap, etc.
- Environment: defines runtime or builder, as well as information around runtime.
- Triggers: one per trigger, HTTPTrigger, TimeTrigger (cron), MessageQueueTrigger, etc.
- Recorder: defines a policy for recording requests and responses.
- CanaryConfig: canary configuration.
- Package: function-level data, either compiled binary (e.g. golang plugin) or modules (e.g. python pip install)

As of v1-rc1, fission has following components:

```
$ kubectl get deployment
NAME          DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
buildermgr    1         1         1            1           30m
controller    1         1         1            1           30m
executor      1         1         1            1           30m
kubewatcher   1         1         1            1           30m
router        1         1         1            1           30m
storagesvc    1         1         1            1           30m
timer         1         1         1            1           30m

$ kubectl get job
NAME                                  COMPLETIONS   DURATION   AGE
fission-1-0-rc1-fission-1.0-rc1-620   1/1           7s         30m
fission-1-0-rc1-fission-1.0-rc1-933   1/1           9s         30m
```

- Controller: Controller is a little misnamed: it is essentially the gateway server for fission
  (not for user functions), which contains CRUD APIs for functions, http triggers, environments,
  Kubernetes event watches, etc. This is the component that the client talks to. By default, it
  creates corresponding CRDs in Kubernetes, but can be changed to use other storage backend.
  Controller also contains a canary controller sub-manager, which queries prometheus and dynamically
  adjust traffic for multiple functions (different versions).
- Router: The router forwards HTTP requests to function pods. If there's no running service for a
  function, it requests one from poolmgr, while holding on to the request; when the function's service
  is ready it forwards the request. Router implementation wraps `gorilla/mux` to allow adding routes
  dynamically.
- Executor: Fission supports multiple execution type, using `--executortype`. Supported types are:
  `poolmgr` and `newdeploy`. poolmgr is the default type, suitable for general use cases; while
  newdeploy is suitable for latency sensitive workload.
  - poolmgr keeps a pool of pods for each environment, and pod is taken from the pool to run functions
    when request comes in. poolmgr exposes two APIs, one for requesting a pod and one for tapping a
    pod that's already been requested (to avoid it from being cleanup up). The APIs are used from
    router. pollmgr manipulates pod labels to take pod from deployment's pod pool, refer to experiment
    and [poolmgr in architecture doc](https://github.com/fission/fission/blob/1.0-rc1/Documentation/Architecture.md#pool-manager)
    for how it works.
  - newdeploy creates a new deployment for each function.
- Kubewatcher: Kubewatcher is a trigger that watches the Kubernetes API and invokes functions associated
  with watches, sending the watch event to the function. To be more specific, the controller keeps
  track of user's requested watches and associated functions. Kubewatcher watches the API based on
  these requests; when a watch event occurs, it serializes the object and calls the function via the
  router.
- Timer: Timer is a trigger that periodically invokes functions associated with a timer. The trigger
  sends empty request to function with hardcoded header, i.e.
  ```
  # timer/timer.go
  (*timer.publisher).Publish("", headers, fission.UrlForFunction(t.Spec.FunctionReference.Name, t.Metadata.Namespace))
  ```
- buildermgr: Buildermgr is responsible to manage build process, as we'll see below. Build here means
  building binaries, as well as installing dependencies.
- storagesvc: storagesvc is a storage service to store build artifacts, archives, etc; for example,
  it is used to save golang plugin built from user source. It works closely with buildermgr and
  environment specific builder.

Environment specific deployment is created when we create a fission environment. Each pod contains
two containers, both of them exposes endpoints for executor to send instructions:
- fetcher container: fetcher container shares the same volume with env specific container. It exposes
  endpoints to download, upload data from/to storage and kubernetes crd.
- env specific container: environment specific container exposes endpoints to 'specialize' a container,
  e.g. for golang, golang container will try to load plugin via golang plugin module; for python, it
  will try to load/import module, etc. Each environment will also host a web server.

Builder specific deployment is created when we create a fission environment with given builder. Each
pod contains two containers, both of them exposes endpoints for buildermgr to send instructions:
- fetcher container: similar as above, fetcher container shares the same volume with builder container,
  and exposes endpoints to download, upload data.
- builder container: similar to env specific container, each runtime has its own builder, e.g. `go build`,
  `pip install`.

In summary, the build workflow looks like:
```
fission env -> fission func -> [fission storagesvc] -> [fission buildermgr] ->  [builder] -> [back to storage] -> [runtime pod]
```

the request workflow looks like:
```
user request -> [fission router] -> [runtime pod fetcher] -> [fission storagesvc] ->  [runtime pod]
```

For a complete workflow, refer to following links.

Following is a list of components from full fission installation:

```
$ kubectl get deployments
NAME                                            DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
buildermgr                                      1         1         1            1           9m59s
controller                                      1         1         1            1           9m59s
executor                                        1         1         1            1           9m59s
fission-1-0-rc1-prometheus-alertmanager         1         1         1            0           12s
fission-1-0-rc1-prometheus-kube-state-metrics   1         1         1            0           12s
fission-1-0-rc1-prometheus-pushgateway          1         1         1            0           12s
fission-1-0-rc1-prometheus-server               1         1         1            0           12s
influxdb                                        1         1         1            0           12s
kubewatcher                                     1         1         1            1           9m59s
mqtrigger-nats-streaming                        1         1         1            1           12s
nats-streaming                                  1         1         1            0           12s
router                                          1         1         1            1           9m59s
storagesvc                                      1         1         1            0           9m59s
timer                                           1         1         1            1           9m59s

$ kubectl get sts
NAME    DESIRED   CURRENT   AGE
redis   1         1         23s

$ kubectl get job
NAME                                  COMPLETIONS   DURATION   AGE
fission-1-0-rc1-fission-1.0-rc1-057   0/1           25s        25s
fission-1-0-rc1-fission-1.0-rc1-366   1/1           8s         25s
fission-1-0-rc1-fission-1.0-rc1-620   1/1           5s         10m
fission-1-0-rc1-fission-1.0-rc1-933   1/1           11s        10m
```

A few more components:
- prometheus & alertmanager: for monitoring
- influxdb: for logging
- mqtrigger & nats-streaming: for message queue trigger
- redis: for event record-replay.

*References*

- https://blog.fission.io/posts/how-to-develop-a-serverless-application-with-fission-pt-1/
- https://blog.fission.io/posts/how-to-develop-a-serverless-application-with-fission-pt-2/
- https://blog.fission.io/posts/how-to-develop-a-serverless-application-with-fission-pt-3/

### New Features

New features in fission v1:
- execution mode: as mentioned above, fission now support two modes
- live reload, i.e. change function source code and fission will push it to remote function automatically
- record replay, i.e. router will save request to redis for future use; user can re-send previous request
- auto canary deployment, i.e. canarycontroller (part of controller) queries prometheus and dynamically
  adjust traffic for multiple functions (different versions)
- prometheus integration, i.e. function metrics like invocation count is automatically saved

*References*

- https://dzone.com/articles/new-in-fission-live-reload-record-replay-canary-de

# Experiment

## fission alpha

*Date: 06/15/2017, alpha*

Installation:

```
$ kubectl create -f http://fission.io/fission.yaml
namespace "fission" created
namespace "fission-function" created
deployment "controller" created
deployment "router" created
service "poolmgr" created
deployment "poolmgr" created
deployment "kubewatcher" created
service "etcd" created
deployment "etcd" created

$ kubectl create -f http://fission.io/fission-nodeport.yaml
service "router" created
service "controller" created

$ export FISSION_URL=http://$(minikube ip):31313
$ export FISSION_ROUTER=$(minikube ip):31314
```

Create an environment in fission, which will be used in poolmgr to create specific deployemnts:

```
# This command will create an environment in fission. An environment is similar to a language runtime.
$ fission env create --name nodejs --image fission/node-env

# fission creates a deployment with 3 pods. This deployment is created from poolmgr.
$ kubectl get pods -n fission-function
NAME                                                              READY     STATUS    RESTARTS   AGE
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv   2/2       Running   0          39m
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462f3gkr   2/2       Running   0          39m
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462sfxcr   2/2       Running   0          39m

$ kubectl get deployment -n fission-function
NAME                                                   DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4   3         3         3            3           39m

$ kubectl logs -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv -c fetcher
```

The nodejs container in the pod is listening on 8888, with codepath set to `/userfunc/user`:

```
$ kubectl logs -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv -c nodejs
npm info it worked if it ends with ok
npm info using npm@4.1.2
npm info using node@v7.7.2
npm info lifecycle fission-nodejs-runtime@0.1.0~prestart: fission-nodejs-runtime@0.1.0
npm info lifecycle fission-nodejs-runtime@0.1.0~start: fission-nodejs-runtime@0.1.0

> fission-nodejs-runtime@0.1.0 start /usr/src/app
> node server.js

Codepath defaulting to  /userfunc/user
Port defaulting to 8888
```

Now we create a function and upload code to fission. We can list it via `function list` command. Note
unlike kubeless, which stores function as thirdparty resources, fission stores functions in etcd. At this
monent, no pod is touched from the pod pool.

```
$ fission function create --name hello --env nodejs --code hello.js

$ fission function list
NAME  UID                                  ENV
hello 3bd0a155-f812-45b5-bee1-ed0eeccd6849 nodejs
```

Now we map `GET /hello` to the new function. Note this also doesn't touch any backend pods; only the
route will be recorded in etcd. As we can see below, all pods doesn't have any user file.

```
$ fission route create --method GET --url /hello --function hello

$ fission route list
NAME                                 METHOD URL    FUNCTION_NAME FUNCTION_UID
2ac1e880-b36f-4ae6-b088-c665e08d0fb7 GET    /hello hello

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462sfxcr -c nodejs sh
# ls /userfunc
node_modules

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462f3gkr -c nodejs sh
# ls /userfunc
node_modules

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462d6glv -c nodejs sh
# ls /userfunc
node_modules
```

Now run the function by requesting fission router. Fission router will send our request to a backend
pod; the pod is chosen by poolmgr.

```
$ curl http://$FISSION_ROUTER/hello
Hello, world!

$ kubectl exec -it -n fission-function nodejs-367bc93e-5784-4d8b-8e72-995f1fbdd873-45r5tde4-41462f3gkr -c nodejs sh
# ls /userfunc
node_modules  user
# cat /userfunc/user

module.exports = async function(context) {
    return {
        status: 200,
        body: "Hello, world!\n"
    };
}
```

## fission v1-rc1

*Date: 12/22/2018, v1-rc1*

Install fission core will create following resources:

```
$ kubectl apply -f https://github.com/fission/fission/releases/download/1.0-rc1/fission-core-1.0-rc1-minikube.yaml
namespace/fission-function created
namespace/fission-builder created
clusterrole.rbac.authorization.k8s.io/secret-configmap-getter created
clusterrole.rbac.authorization.k8s.io/package-getter created
serviceaccount/fission-svc created
rolebinding.rbac.authorization.k8s.io/fission-admin created
clusterrolebinding.rbac.authorization.k8s.io/fission-crd created
serviceaccount/fission-fetcher created
serviceaccount/fission-builder created
configmap/feature-config created
deployment.extensions/controller created
deployment.extensions/router created
service/executor created
deployment.extensions/executor created
deployment.extensions/buildermgr created
deployment.extensions/kubewatcher created
deployment.extensions/timer created
deployment.extensions/storagesvc created
persistentvolumeclaim/fission-storage-pvc created
service/router created
service/controller created
service/storagesvc created
job.batch/fission-1-0-rc1-fission-1.0-rc1-933 created
job.batch/fission-1-0-rc1-fission-1.0-rc1-620 created
```

Now if we follow along with the getting started guide, we'll be able to see CRDs created:

```
# Add the stock NodeJS env to your Fission deployment
$ fission env create --name nodejs --image fission/node-env

# A javascript one-liner that prints "hello world"
$ curl https://raw.githubusercontent.com/fission/fission/master/examples/nodejs/hello.js > hello.js

# Upload your function code to fission
$ fission function create --name hello --env nodejs --code hello.js

# Map GET /hello to your new function
$ fission route create --method GET --url /hello --function hello

# Run the function.  This takes about 100msec the first time.
$ fission function test --name hello
Hello, world!
```

CRDs:

```
$ kubectl get environments.fission.io
NAME     AGE
nodejs   13m

$ kubectl get functions.fission.io
NAME    AGE
hello   5m

# The trigger is created when running `fission route create`
$ kubectl get httptriggers.fission.io
NAME                                   AGE
9e1d6259-7b0f-4a56-b6d8-531f95dde443   3m
```

Note when we call our function, one of the pod in pool manager is used to serve our requests. It is
removed from the pool via changing label, which results in deployment bringing up a new pod. In the
example below, `nodejs-poolmgr-default-cc46fc866-glt5d` is used to serve requests and `nodejs-poolmgr-default-cc46fc866-sphnq`
is the new pod brought up by pool manager.

```
$ kubectl get deployment -n fission-function
NAME                     DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
nodejs-poolmgr-default   3         3         3            3           33m

$ kubectl get pods -n fission-function --show-labels
nodejs-poolmgr-default-cc46fc866-4t5pv   2/2     Running   0          21m   environmentName=nodejs,environmentNamespace=default,environmentUid=015829b0-0584-11e9-a1f1-2c4d54ed3845,executorInstanceId=pwlrz4y2,executorType=poolmgr,pod-template-hash=cc46fc866
nodejs-poolmgr-default-cc46fc866-glt5d   2/2     Running   0          32m   executorInstanceId=pwlrz4y2,functionName=hello,functionUid=2e75a705-0585-11e9-a1f1-2c4d54ed3845,unmanaged=true
nodejs-poolmgr-default-cc46fc866-kwt57   2/2     Running   0          32m   environmentName=nodejs,environmentNamespace=default,environmentUid=015829b0-0584-11e9-a1f1-2c4d54ed3845,executorInstanceId=pwlrz4y2,executorType=poolmgr,pod-template-hash=cc46fc866
nodejs-poolmgr-default-cc46fc866-sphnq   2/2     Running   0          42s   environmentName=nodejs,environmentNamespace=default,environmentUid=015829b0-0584-11e9-a1f1-2c4d54ed3845,executorInstanceId=pwlrz4y2,executorType=poolmgr,pod-template-hash=cc46fc866
```

**Using compiled language, e.g. Golang**

Below, we first create a golang environment. Note the builder pod is created under `fission-builder`
namespace:

```
$ fission env create --name go --image fission/go-env --builder fission/go-builder
environment 'go' created

$ kubectl get deployment -n fission-function
NAME                     DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
go-poolmgr-default       3         3         3            3           89s

$ kubectl get packages --all-namespaces
No resources found.

$ kubectl get functions --all-namespaces
No resources found.

$ kubectl get pods -n fission-builder
NAME                       READY   STATUS    RESTARTS   AGE
go-5362-598f8f8bb8-vz752   2/2     Running   0          15m
```

Then we create golang function with builder image to build go plugin:

```
$ fission fn create --name helloworld --env go --src hw.go --entrypoint Handler
Package 'hw-go-amgo' created
package 'hw-go-amgo' created
function 'helloworld' created

$ kubectl get packages
NAME            AGE
hw-go-amgo      18s

$ kubectl get functions
NAME         AGE
helloworld   28s
```

Following is the yaml content of `hw-go-amgo` package. Pay attention to `spec.deployment.url`, which
is the location of the newly built golang plugin:

```yaml
apiVersion: fission.io/v1
kind: Package
metadata:
  creationTimestamp: 2018-12-22T07:25:59Z
  generation: 1
  name: hw-go-amgo
  namespace: default
  resourceVersion: "5604"
  selfLink: /apis/fission.io/v1/namespaces/default/packages/hw-go-amgo
  uid: d48ecff7-05ba-11e9-a1f1-2c4d54ed3845
spec:
  deployment:
    checksum:
      sum: acbd483a266b6a4554f7f1e00644411bb6174646c98e344bb7d829a50aadce8f
      type: sha256
    type: url
    url: http://storagesvc.default/v1/archive?id=%2Ffission%2Ffission-functions%2Fc4d3dce9-b50a-4d4b-86bb-1648296a1fb4
  environment:
    name: go
    namespace: default
  source:
    checksum: {}
    literal: UEsDBBQACAAIANM5lk0AAAAAAAAAAAAAAAAFAAkAaHcuZ29VVAUAAV7kHVw0jbFu6zAMRWfzK+7zZD8Y8V6gW4fMXTq0HRSHloVKlCrSMIKi/144iDfiguecc
cTLyrAMn6MTjxJXHwSJp8VJ0DTQOMIWRnHTl/OMPGNeZbKQBYuTa+SKtKrhwkguyPFIB7CPRCGVXA0dNa2wjYtZaamn3X5+WILeQyxWbyg5iGHOFbYExRxU9+KRpv04yG7D7ju
9spYsym81GNcBFf8f+/fKaj1+qEnq8fSM9swx5gFbrvH670NaarbTnevePy834y6p73v6pb8AAAD//1BLBwijYB03zgAAACIBAABQSwECFAMUAAgACADTOZZNo2AdN84AAAAiA
QAABQAJAAAAAAAAAAAApIEAAAAAaHcuZ29VVAUAAV7kHVxQSwUGAAAAAAEAAQA8AAAACgEAAAAA
    type: literal
status:
  buildlog: |
    Building in directory /usr/src/hw-go-amgo-sriiov
    + basename /packages/hw-go-amgo-sriiov
    + srcDir=/usr/src/hw-go-amgo-sriiov
    + trap rm -rf /usr/src/hw-go-amgo-sriiov EXIT
    + [ -d /packages/hw-go-amgo-sriiov ]
    + echo Building in directory /usr/src/hw-go-amgo-sriiov
    + ln -sf /packages/hw-go-amgo-sriiov /usr/src/hw-go-amgo-sriiov
    + cd /usr/src/hw-go-amgo-sriiov
    + go build -buildmode=plugin -i -o /packages/hw-go-amgo-sriiov-ix3atl .
    + rm -rf /usr/src/hw-go-amgo-sriiov
  buildstatus: succeeded
```

And here is the logs from builder pod (two containers: builder and fetcher). From the logs, we know
that builder container receives build request (from buildermgr), and fetcher container is responsible
to upload package to storagesvc:

```
$ kubectl logs -n fission-builder go-5362-598f8f8bb8-vz752 -c builder
2018/12/22 07:26:00 Builder received request: {hw-go-amgo-sriiov build}
2018/12/22 07:26:00 Starting build...

=== Build Logs ===command=build
env=[PATH=/go/bin:/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOSTNAME=go-5362-598f8f8bb8-vz752 GO_5362_PORT_8000_TCP_ADDR=10.0.0.116 KUBERNETES_PORT_443_TCP_PORT=443 GO_5362_SERVICE_PORT=8000 GO_5362_SERVICE_PORT_FETCHER_PORT=8000 GO_5362_SERVICE_PORT_BUILDER_PORT=8001 GO_5362_PORT_8000_TCP_PROTO=tcp GO_5362_PORT=tcp://10.0.0.116:8000 GO_5362_PORT_8001_TCP_PORT=8001 GO_5362_SERVICE_HOST=10.0.0.116 KUBERNETES_SERVICE_HOST=10.0.0.1 KUBERNETES_PORT_443_TCP=tcp://10.0.0.1:443 KUBERNETES_PORT_443_TCP_PROTO=tcp GO_5362_PORT_8001_TCP_ADDR=10.0.0.116 KUBERNETES_SERVICE_PORT=443 KUBERNETES_SERVICE_PORT_HTTPS=443 KUBERNETES_PORT=tcp://10.0.0.1:443 GO_5362_PORT_8000_TCP=tcp://10.0.0.116:8000 GO_5362_PORT_8000_TCP_PORT=8000 GO_5362_PORT_8001_TCP=tcp://10.0.0.116:8001 GO_5362_PORT_8001_TCP_PROTO=tcp KUBERNETES_PORT_443_TCP_ADDR=10.0.0.1 GOLANG_VERSION=1.9.2 GOPATH=/usr HOME=/root SRC_PKG=/packages/hw-go-amgo-sriiov DEPLOY_PKG=/packages/hw-go-amgo-sriiov-ix3atl]
Building in directory /usr/src/hw-go-amgo-sriiov
+ basename /packages/hw-go-amgo-sriiov
+ srcDir=/usr/src/hw-go-amgo-sriiov
+ trap rm -rf /usr/src/hw-go-amgo-sriiov EXIT
+ [ -d /packages/hw-go-amgo-sriiov ]
+ echo Building in directory /usr/src/hw-go-amgo-sriiov
+ ln -sf /packages/hw-go-amgo-sriiov /usr/src/hw-go-amgo-sriiov
+ cd /usr/src/hw-go-amgo-sriiov
+ go build -buildmode=plugin -i -o /packages/hw-go-amgo-sriiov-ix3atl .
+ rm -rf /usr/src/hw-go-amgo-sriiov
==================
2018/12/22 07:26:05 elapsed time in build request = 5.594308971s

$ kubectl logs -n fission-builder go-5362-598f8f8bb8-vz752 -c fetcher
2018/12/22 07:14:06 Fetcher ready to receive requests
2018/12/22 07:25:59 fetcher received fetch request and started downloading: {0 {hw-go-amgo  default /apis/fission.io/v1/namespaces/default/packages/hw-go-amgo d48ecff7-05ba-11e9-a1f1-2c4d54ed3845 5600 1 2018-12-22 07:25:59 +0000 UTC <nil> <nil> map[] map[] [] nil [] }   hw-go-amgo-sriiov [] [] false}
2018/12/22 07:26:00 Successfully placed at /packages/hw-go-amgo-sriiov
2018/12/22 07:26:00 Checking secrets/cfgmaps
2018/12/22 07:26:00 Completed fetch request
2018/12/22 07:26:00 elapsed time in fetch request = 11.382827ms
2018/12/22 07:26:05 fetcher received upload request: {hw-go-amgo-sriiov-ix3atl http://storagesvc.default true}
2018/12/22 07:26:05 Starting upload...
2018/12/22 07:26:05 Completed upload request
2018/12/22 07:26:05 http: multiple response.WriteHeader calls
2018/12/22 07:26:05 elapsed time in upload request = 309.966044ms
```

Following is the logs from buildermgr and storagesvc, which also demonstrate the whole process.

```
$ kubectl logs buildermgr-855685c97f-4xdzk
2018/12/22 07:13:58 Creating builder service: go-5362
2018/12/22 07:13:58 Creating builder deployment: go-5362
2018/12/22 07:25:59 Start build for package hw-go-amgo with resource version 5598
2018/12/22 07:25:59 Patched rolebinding : package-getter-binding.default
2018/12/22 07:25:59 Setup rolebinding for sa : fission-builder.fission-builder for pkg : hw-go-amgo.default
2018/12/22 07:26:00 Start building with source package: hw-go-amgo-sriiov
2018/12/22 07:26:05 Build succeed, source package: hw-go-amgo-sriiov, deployment package: hw-go-amgo-sriiov-ix3atl
2018/12/22 07:26:05 Start uploading deployment package: hw-go-amgo-sriiov-ix3atl
2018/12/22 07:26:05 Start updating info of package: hw-go-amgo
2018/12/22 07:26:05 Completed build request for package: hw-go-amgo

$ kubectl logs storagesvc-84f7c85786-b6fwb
time="2018-12-22T00:50:18Z" level=info msg="Storage service started"
time="2018-12-22T00:50:18Z" level=info msg="listening to archiveChannel to prune archives"
time="2018-12-22T01:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T02:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T03:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T04:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T05:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T06:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T07:26:05Z" level=info msg="Handling upload for /packages/hw-go-amgo-sriiov-ix3atl.zip"
172.17.0.12 - - [22/Dec/2018:07:26:05 +0000] "POST /v1/archive HTTP/1.1" 200 72
```

Now we can issue request to our function
- it takes a little long cold start time because fetcher will pull go plugin binary from storagesvc (10s)
- the 'Specializing' command is called from executor to load plugin

```
$ fission fn test --name helloworld
Hello, world!

$ kubectl logs storagesvc-84f7c85786-b6fwb
time="2018-12-22T00:50:18Z" level=info msg="Storage service started"
time="2018-12-22T00:50:18Z" level=info msg="listening to archiveChannel to prune archives"
time="2018-12-22T01:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T02:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T03:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T04:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T05:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T06:50:18Z" level=info msg="getting orphan archives"
time="2018-12-22T07:26:05Z" level=info msg="Handling upload for /packages/hw-go-amgo-sriiov-ix3atl.zip"
172.17.0.12 - - [22/Dec/2018:07:26:05 +0000] "POST /v1/archive HTTP/1.1" 200 72
time="2018-12-22T07:50:18Z" level=info msg="getting orphan archives"
172.17.0.16 - - [22/Dec/2018:07:55:05 +0000] "GET /v1/archive?id=%2Ffission%2Ffission-functions%2Fc4d3dce9-b50a-4d4b-86bb-1648296a1fb4 HTTP/1.1" 200 3252303

$ kubectl logs -n fission-function go-poolmgr-default-bd6974899-bxckj -c fetcher
2018/12/22 07:14:24 Fetcher ready to receive requests
2018/12/22 07:55:05 fetcher received fetch request and started downloading: {1 {hw-go-amgo  default    0 0001-01-01 00:00:00 +0000 UTC <nil> <nil> map[] map[] [] nil [] }   d490406e-05ba-11e9-a1f1-2c4d54ed3845 [] [] false}
2018/12/22 07:55:16 Successfully placed at /userfunc/d490406e-05ba-11e9-a1f1-2c4d54ed3845
2018/12/22 07:55:16 Checking secrets/cfgmaps
2018/12/22 07:55:16 Completed fetch request
2018/12/22 07:55:16 elapsed time in fetch request = 10.893976005s

$ kubectl logs -n fission-function go-poolmgr-default-bd6974899-bxckj -c go
Listening on 8888 ...
Specializing ...
loading plugin from /userfunc/d490406e-05ba-11e9-a1f1-2c4d54ed3845/hw-go-amgo-sriiov-ix3atl
Done
```
