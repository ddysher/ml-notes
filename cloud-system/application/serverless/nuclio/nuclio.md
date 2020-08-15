<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
  - [Design](#design)
  - [Components](#components)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Nuclio is a high-performance serverless event and data processing platform. It is different from
other platforms in that nuclio focuses on performance, concurrent real-time processing, stream
partitioning, etc.

*References*

- https://thenewstack.io/whats-next-serverless/
- https://www.slideshare.net/iguazio/running-highspeed-serverless-with-nuclio

# Architecture

*Date: 12/23/2018, v0.7.4*

## Design

Unlike other serverless platforms where each function comes with a very thin entrypoint layer (e.g.
a simple webserver, a simple init process), nuclio's per-function processor acts as the management
plane for user function, it will:
- listen to triggers
- manage databindings
- handle request/response
- manage multiple workers (each function is running in a worker, e.g. goroutine, asyncio)
- load user function via language runtime, e.g. golang plugin, python wrapper, etc

To convert source code to a running function, you must first deploy the function. A deploy process
has three stages:
- The source code is built to a Docker image and pushed to a Docker registry, or user can directly
  use custom image, provided the image conforms to a couple rules, e.g. the first command to run
  must be `processor`, shim layer must be installed, e.g. python wrapper. docker `ONBUILD` is used
  here.
- A function object is created in Nuclio (i.e., in Kubernetes, this is a function CRD).
- A controller creates the appropriate function resources on the cluster (i.e., in Kubernetes this
  is the deployment, service, ingress, etc.).

All supported runtimes (such as Go, Python, or NodeJS) have an entry point that receives two arguments:
- Context: An object that maintains state across function invocations. Includes objects like the
  logger, data bindings, worker information and user specified data. See the appropriate context
  reference for your specific runtime for more.
- Event: An object containing information about the event that triggered the function including body,
  headers, trigger information and so forth.

## Components

**Controller**

A controller accepts function and event-source specifications, invokes builders and processors
through an orchestration platform (such as Kubernetes), and manages function elasticity, life cycle,
and versions.

In Kubernetes, Controller is a regular long running deployment.

**Processor**

A processor listens on one or more triggers (for example, HTTP, Message Queue, or Stream), and
executes user functions with one or more parallel workers.

The workers use language-specific runtimes to execute the function (via native calls, shared memory,
or shell). Processors use abstract interfaces to integrate with platform facilities for logging,
monitoring and configuration, allowing for greater portability and extensibility (such as logging to
a screen, file, or log stream). It also manages data binding to provide persistent data connections
to external files, objects, databases, or messaging systems.

In Kuberntes, Processor is not a long runnong component, it is launched when user creates a function.
It is the init process in function container: it manages user function, etc. Each function has its
own processor.

**Builder**

A builder receives raw code and optional build instructions and dependencies, and generates the
function artifact - a binary file or a Docker container image that the builder can also push to a
specified image repository. The builder can run in the context of the CLI or as a separate service,
for automated development pipelines.

In Kubernetes, by default, builder is not running as a separate service: it is mainly used in CLI.

**Dealer**

A dealer is used with streaming and batch jobs to distribute a set of tasks or data partitions/shards
among the available function instances, and to guarantee that all tasks are completed successfully.

TBD: this is under development.

**Dashboard**

The dashboard is a standalone service deployed in platform.

*References*

- https://github.com/nuclio/nuclio/tree/0.7.4#high-level-architecture
- https://github.com/nuclio/nuclio/blob/0.7.4/docs/concepts/architecture.md

# Experiment

*Date: 12/23/2018, v0.7.4*

Install nuclio:

```
$ kubectl apply -f https://raw.githubusercontent.com/nuclio/nuclio/master/hack/k8s/resources/nuclio-rbac.yaml
$ kubectl apply -f https://raw.githubusercontent.com/nuclio/nuclio/master/hack/k8s/resources/nuclio.yaml

$ kubectl get all -n nuclio
NAME                                     READY   STATUS    RESTARTS   AGE
pod/nuclio-controller-5cb7479c54-nkdqh   1/1     Running   0          15h
pod/nuclio-dashboard-64d4bc9879-hr44d    1/1     Running   0          15h

NAME                       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)          AGE
service/nuclio-dashboard   ClusterIP   10.0.0.105   <none>        8070/TCP         15h

NAME                                DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/nuclio-controller   1         1         1            1           15h
deployment.apps/nuclio-dashboard    1         1         1            1           15h

NAME                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/nuclio-controller-5cb7479c54   1         1         1       15h
replicaset.apps/nuclio-dashboard-64d4bc9879    1         1         1       15h
```

Run a registry:

```
$ docker run -d -p 5000:5000 --name registry -v /tmp/registry:/var/lib/registry registry:2
```

Now deploy a function using `nuctl`:

```
$ cd experiments

$ nuctl deploy my-function \
        --path my_function.py \
        --runtime python:2.7 \
        --handler my_function:my_entry_point \
        --namespace nuclio \
        --registry localhost:5000 --run-registry localhost:5000
18.12.23 17:32:43.230                     nuctl (I) Deploying function {"name": "my-function"}
18.12.23 17:32:43.255                     nuctl (I) Building {"name": "my-function"}
18.12.23 17:32:43.285                     nuctl (I) Staging files and preparing base images
18.12.23 17:32:43.285                     nuctl (I) Pulling image {"imageName": "quay.io/nuclio/handler-builder-python-onbuild:0.7.4-amd64"}
18.12.23 17:32:47.955                     nuctl (I) Building processor image {"imageName": "nuclio/processor-my-function:latest"}
18.12.23 17:32:48.125                     nuctl (I) Pushing image {"from": "nuclio/processor-my-function:latest", "to": "localhost:5000/nuclio/processor-my-function:latest"}
18.12.23 17:32:50.471                     nuctl (I) Build complete {"result": {"Image":"nuclio/processor-my-function:latest","UpdatedFunctionConfig":{"metadata":{"name":"my-function","namespace":"nuclio"},"spec":{"handler":"my_function:my_entry_point","runtime":"python:2.7","resources":{},"replicas":1,"targetCPU":75,"build":{"path":"my_function.py","functionSourceCode":"aW1wb3J0IG9zCgpkZWYgbXlfZW50cnlfcG9pbnQoY29udGV4dCwgZXZlbnQpOgogICMgdXNlIHRoZSBsb2dnZXIsIG91dHB1dHRpbmcgdGhlIGV2ZW50IGJvZHkKICBjb250ZXh0LmxvZ2dlci5pbmZvX3dpdGgoCiAgICAnR290IGludm9rZWQnLAogICAgdHJpZ2dlcl9raW5kPWV2ZW50LnRyaWdnZXIua2luZCwKICAgIGV2ZW50X2JvZHk9ZXZlbnQuYm9keSwKICAgIHNvbWVfZW52PW9zLmVudmlyb24uZ2V0KCdNWV9FTlZfVkFMVUUnKSkKCiAgIyBjaGVjayBpZiB0aGUgZXZlbnQgY2FtZSBmcm9tIGNyb24KICBpZiBldmVudC50cmlnZ2VyLmtpbmQgPT0gJ2Nyb24nOgogICAgIyBsb2cgc29tZXRoaW5nCiAgICBjb250ZXh0LmxvZ2dlci5pbmZvKCdJbnZva2VkIGZyb20gY3JvbicpCiAgZWxzZToKICAgICMgcmV0dXJuIGEgcmVzcG9uc2UKICAgIHJldHVybiAnQSBzdHJpbmcgcmVzcG9uc2UnCg==","registry":"localhost:5000"},"runRegistry":"localhost:5000","platform":{},"readinessTimeoutSeconds":30}}}}
18.12.23 17:32:54.488                     nuctl (I) Function deploy complete {"httpPort": 31617}
```

Since we are submitting source code, an image will be built *locally* from where nuctl is running,
and then pushed to given docker registry. If we are using image directly, there's no build process.
Following is the images so far:

```
$ docker images | grep nuc
nuclio/processor-my-function                                     latest                                  0da259ffe25a        5 hours ago         80.2MB
localhost:5000/nuclio/processor-my-function                      latest                                  0da259ffe25a        5 hours ago         80.2MB
quay.io/nuclio/handler-builder-python-onbuild                    0.7.4-amd64                             e381053c0eb4        12 days ago         21.9MB
quay.io/nuclio/dashboard                                         0.7.4-amd64                             43a3af4c989d        12 days ago         186MB
quay.io/nuclio/controller                                        0.7.4-amd64                             77687ddda27c        12 days ago         27.5MB
```

After building and pushing image, a `Function` custom resource is created from nuctl:

```
$ kubectl get functions -n nuclio my-function -o yaml
apiVersion: nuclio.io/v1beta1
kind: Function
metadata:
  creationTimestamp: 2018-12-23T09:30:03Z
  generation: 1
  name: my-function
  namespace: nuclio
  resourceVersion: "781"
  selfLink: /apis/nuclio.io/v1beta1/namespaces/nuclio/functions/my-function
  uid: 53ee2a1b-0695-11e9-b100-2c4d54ed3845
spec:
  alias: latest
  build:
    functionSourceCode: aW1wb3J0IG9zCgpkZWYgbXlfZW50cnlfcG9pbnQoY29udGV4dCwgZXZlbnQpOgogICMgdXNlIHRoZSBsb2dnZXIsIG91dHB1dHRpbmcgdGhlIGV2ZW50IGJvZHkKICBjb250ZXh0LmxvZ2dlci5pbmZvX3dpdGgoCiAgICAnR290IGludm9rZWQnLAogICAgdHJpZ2dlcl9raW5kPWV2ZW50LnRyaWdnZXIua2luZCwKICAgIGV2ZW50X2JvZHk9ZXZlbnQuYm9keSwKICAgIHNvbWVfZW52PW9zLmVudmlyb24uZ2V0KCdNWV9FTlZfVkFMVUUnKSkKCiAgIyBjaGVjayBpZiB0aGUgZXZlbnQgY2FtZSBmcm9tIGNyb24KICBpZiBldmVudC50cmlnZ2VyLmtpbmQgPT0gJ2Nyb24nOgogICAgIyBsb2cgc29tZXRoaW5nCiAgICBjb250ZXh0LmxvZ2dlci5pbmZvKCdJbnZva2VkIGZyb20gY3JvbicpCiAgZWxzZToKICAgICMgcmV0dXJuIGEgcmVzcG9uc2UKICAgIHJldHVybiAnQSBzdHJpbmcgcmVzcG9uc2UnCg==
    path: my_function.py
    registry: localhost:5000
    timestamp: 1545557570
  handler: my_function:my_entry_point
  image: localhost:5000/nuclio/processor-my-function:latest
  imageHash: "1545557563283626352"
  platform: {}
  readinessTimeoutSeconds: 30
  replicas: 1
  resources: {}
  runRegistry: localhost:5000
  runtime: python:2.7
  targetCPU: 75
  version: -1
status:
  httpPort: 31617
  state: ready
```

The controller component receives the `Function` custom resource, and then create corresponding
deployment, service and hpa. Note that service is type `NodePort`:

```
$ kubectl get all -n nuclio
NAME                                     READY   STATUS    RESTARTS   AGE
pod/my-function-7ffb5b5789-j5hwx         1/1     Running   0          15h
pod/nuclio-controller-5cb7479c54-nkdqh   1/1     Running   0          15h
pod/nuclio-dashboard-64d4bc9879-hr44d    1/1     Running   0          15h

NAME                       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)          AGE
service/my-function        NodePort    10.0.0.193   <none>        8080:31617/TCP   15h
service/nuclio-dashboard   ClusterIP   10.0.0.105   <none>        8070/TCP         15h

NAME                                DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-function         1         1         1            1           15h
deployment.apps/nuclio-controller   1         1         1            1           15h
deployment.apps/nuclio-dashboard    1         1         1            1           15h

NAME                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/my-function-7ffb5b5789         1         1         1       15h
replicaset.apps/nuclio-controller-5cb7479c54   1         1         1       15h
replicaset.apps/nuclio-dashboard-64d4bc9879    1         1         1       15h

NAME                                              REFERENCE                TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/my-function   Deployment/my-function   <unknown>/75%   1         10        1          3m8s
```

At this point, pod starts running and we can query nodeport for response:

```
$ http 192.168.3.34:31617
HTTP/1.1 200 OK
Content-Length: 17
Content-Type: text/plain
Date: Mon, 24 Dec 2018 00:59:27 GMT
Server: nuclio

A string response

```

The entrypoint of the container is `processor`, as mentioned above, processor is the core component
in nuclio and it takes care of request handling, event listening, etc. Following is the pod data and
logs:

```
$ kubectl describe pods -n nuclio my-function-7ffb5b5789-j5hwx
Name:               my-function-7ffb5b5789-j5hwx
Namespace:          nuclio
Priority:           0
PriorityClassName:  <none>
Node:               127.0.0.1/127.0.0.1
Start Time:         Sun, 23 Dec 2018 17:32:50 +0800
Labels:             nuclio.io/app=functionres
                    nuclio.io/class=function
                    nuclio.io/function-name=my-function
                    nuclio.io/function-version=latest
                    pod-template-hash=7ffb5b5789
Annotations:        nuclio.io/image-hash: 1545557563283626352
Status:             Running
IP:                 172.17.0.6
Controlled By:      ReplicaSet/my-function-7ffb5b5789
Containers:
  nuclio:
    Container ID:   docker://4265e0268475a9c281cd47050b758805eaf6c7935a370d46f6ee6c8743415d9c
    Image:          localhost:5000/nuclio/processor-my-function:latest
    Image ID:       docker-pullable://localhost:5000/nuclio/processor-my-function@sha256:dc94a4120a477290fb08e67b8bc605bb0c64e57fde84707fdc522831d0d9f2a6
    Port:           8080/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Sun, 23 Dec 2018 17:32:51 +0800
    Ready:          True
    Restart Count:  0
    Requests:
      cpu:      25m
    Liveness:   http-get http://:8082/live delay=10s timeout=3s period=5s #success=1 #failure=3
    Readiness:  http-get http://:8082/ready delay=1s timeout=1s period=1s #success=1 #failure=3
    Environment:
      NUCLIO_FUNCTION_NAME:      my-function
      NUCLIO_FUNCTION_VERSION:   latest
      NUCLIO_FUNCTION_INSTANCE:  my-function-7ffb5b5789-j5hwx (v1:metadata.name)
    Mounts:
      /etc/nuclio/config/platform from platform-config-volume (rw)
      /etc/nuclio/config/processor from processor-config-volume (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-lp95m (ro)
Conditions:
  Type              Status
  Initialized       True
  Ready             True
  ContainersReady   True
  PodScheduled      True
Volumes:
  processor-config-volume:
    Type:      ConfigMap (a volume populated by a ConfigMap)
    Name:      my-function
    Optional:  false
  platform-config-volume:
    Type:      ConfigMap (a volume populated by a ConfigMap)
    Name:      platform-config
    Optional:  true
  default-token-lp95m:
    Type:        Secret (a volume populated by a Secret)
    SecretName:  default-token-lp95m
    Optional:    false
QoS Class:       Burstable
Node-Selectors:  <none>
Tolerations:     node.kubernetes.io/not-ready:NoExecute for 300s
                 node.kubernetes.io/unreachable:NoExecute for 300s
Events:          <none>



$ kubectl logs -n nuclio my-function-7ffb5b5789-j5hwx
18.12.23 09:32:51.606                 processor (D) Read configuration {"config": {"metadata":{"name":"my-function","namespace":"nuclio"},"spec":{"handler":"my_function:my_entry_point","runtime":"python:2.7","resources":{},"image":"localhost:5000/nuclio/processor-my-function:latest","imageHash":"1545557563283626352","replicas":1,"targetCPU":75,"version":-1,"alias":"latest","build":{"path":"my_function.py","functionSourceCode":"aW1wb3J0IG9zCgpkZWYgbXlfZW50cnlfcG9pbnQoY29udGV4dCwgZXZlbnQpOgogICMgdXNlIHRoZSBsb2dnZXIsIG91dHB1dHRpbmcgdGhlIGV2ZW50IGJvZHkKICBjb250ZXh0LmxvZ2dlci5pbmZvX3dpdGgoCiAgICAnR290IGludm9rZWQnLAogICAgdHJpZ2dlcl9raW5kPWV2ZW50LnRyaWdnZXIua2luZCwKICAgIGV2ZW50X2JvZHk9ZXZlbnQuYm9keSwKICAgIHNvbWVfZW52PW9zLmVudmlyb24uZ2V0KCdNWV9FTlZfVkFMVUUnKSkKCiAgIyBjaGVjayBpZiB0aGUgZXZlbnQgY2FtZSBmcm9tIGNyb24KICBpZiBldmVudC50cmlnZ2VyLmtpbmQgPT0gJ2Nyb24nOgogICAgIyBsb2cgc29tZXRoaW5nCiAgICBjb250ZXh0LmxvZ2dlci5pbmZvKCdJbnZva2VkIGZyb20gY3JvbicpCiAgZWxzZToKICAgICMgcmV0dXJuIGEgcmVzcG9uc2UKICAgIHJldHVybiAnQSBzdHJpbmcgcmVzcG9uc2UnCg==","registry":"localhost:5000","timestamp":1545557570},"runRegistry":"localhost:5000","platform":{},"readinessTimeoutSeconds":30},"PlatformConfig":null}, "platformConfig": {"kind":"kube","webAdmin":{"enabled":true,"listenAddress":":8081"},"healthCheck":{"enabled":true,"listenAddress":":8082"},"logger":{"sinks":{"stdout":{"kind":"stdout"}},"system":[{"level":"debug","sink":"stdout"}],"functions":[{"level":"debug","sink":"stdout"}]},"metrics":{},"scaleToZero":{},"autoScale":{}}}
18.12.23 09:32:51.608                 processor (D) Creating default HTTP event source {"configuration": {"class":"sync","kind":"http","maxWorkers":1,"url":":8080","workerAllocatorName":"defaultHTTPWorkerAllocator"}}
18.12.23 09:32:51.608            processor.http (D) Creating worker pool {"num": 1}
18.12.23 09:32:51.608 sor.http.w0.python.logger (D) Creating listener socket {"path": "/tmp/nuclio-rpc-bgflcgt60b80009t0fog.sock"}
18.12.23 09:32:51.608 sor.http.w0.python.logger (D) Using Python wrapper script path {"path": "/opt/nuclio/_nuclio_wrapper.py"}
18.12.23 09:32:51.608 sor.http.w0.python.logger (D) Using Python handler {"handler": "my_function:my_entry_point"}
18.12.23 09:32:51.608 sor.http.w0.python.logger (D) Using Python executable {"path": "/usr/local/bin/python2"}
18.12.23 09:32:51.608 sor.http.w0.python.logger (D) Setting PYTHONPATH {"value": "PYTHONPATH=/opt/nuclio"}
18.12.23 09:32:51.608 sor.http.w0.python.logger (D) Running wrapper {"command": "/usr/local/bin/python2 -u /opt/nuclio/_nuclio_wrapper.py --handler my_function:my_entry_point --socket-path /tmp/nuclio-rpc-bgflcgt60b80009t0fog.sock --platform-kind kube --namespace nuclio"}
18.12.23 09:32:51.731 sor.http.w0.python.logger (I) Wrapper connected
Python> 2018-12-23 09:32:51,731 [info] Replacing logger output
18.12.23 09:32:51.731 sor.http.w0.python.logger (D) Waiting for start
18.12.23 09:32:51.731 sor.http.w0.python.logger (D) Started
18.12.23 09:32:51.731 .webadmin.server.triggers (D) Registered custom route {"pattern": "/{id}/stats", "method": "GET"}
18.12.23 09:32:51.731 processor.webadmin.server (D) Registered resource {"name": "triggers"}
18.12.23 09:32:51.731                 processor (W) No metric sinks configured, metrics will not be published
18.12.23 09:32:51.731                 processor (D) Starting
18.12.23 09:32:51.731 cessor.healthcheck.server (I) Listening {"listenAddress": ":8082"}
18.12.23 09:32:51.731            processor.http (I) Starting {"listenAddress": ":8080", "readBufferSize": 4096}
18.12.23 09:32:51.731 processor.webadmin.server (I) Listening {"listenAddress": ":8081"}
18.12.23 14:05:31.723 sor.http.w0.python.logger (D) Processing event {"name": "my-function", "version": -1, "eventID": "905b873a-9a88-4203-8f4f-6ace0fe44897"}
18.12.23 14:05:31.723 sor.http.w0.python.logger (D) Sending event to wrapper {"size": 0}
18.12.23 14:05:31.723 sor.http.w0.python.logger (I) Got invoked {"some_env": null, "event_body": "", "trigger_kind": "http"}
18.12.23 14:05:31.724 sor.http.w0.python.logger (D) Event executed {"name": "my-function", "status": 200, "eventID": "905b873a-9a88-4203-8f4f-6ace0fe44897"}
18.12.24 00:59:28.201 sor.http.w0.python.logger (D) Processing event {"name": "my-function", "version": -1, "eventID": "635a0707-9340-463a-94da-863fbd173512"}
18.12.24 00:59:28.201 sor.http.w0.python.logger (D) Sending event to wrapper {"size": 0}
18.12.24 00:59:28.202 sor.http.w0.python.logger (I) Got invoked {"trigger_kind": "http", "some_env": null, "event_body": ""}
18.12.24 00:59:28.202 sor.http.w0.python.logger (D) Event executed {"name": "my-function", "status": 200, "eventID": "635a0707-9340-463a-94da-863fbd173512"}
```

**Using nats**

```
nuctl deploy nats-function \
	--path nats_function.py \
	--runtime python:2.7 \
	--handler nats_function:my_entry_point \
	--namespace nuclio \
	--registry localhost:5000 --run-registry localhost:5000 \
	--env MY_ENV_VALUE='my value' \
	--triggers '{"myNatsTopic": {"kind": "nats", "url": "http://10.0.0.3:4222", "attributes": {"topic": "my.topic"}}}'
```

The log shows that process starts listening on triggers and spawns workers for processing events:

```
$ kubectl logs -n nuclio nats-function-9fff94d89-48bg9
18.12.24 02:12:22.918                 processor (D) Read configuration {"config": {"metadata":{"name":"nats-function","namespace":"nuclio"},"spec":{"handler":"nats_function:my_entry_point","runtime":"python:2.7","env":[{"name":"MY_ENV_VALUE","value":"my value"}],"resources":{},"image":"localhost:5000/nuclio/processor-nats-function:latest","imageHash":"1545617537468583784","replicas":1,"targetCPU":75,"triggers":{"myNatsTopic":{"class":"","kind":"nats","url":"http://10.0.0.3:4222","attributes":{"topic":"my.topic"}}},"version":-1,"alias":"latest","build":{"path":"nats_function.py","functionSourceCode":"aW1wb3J0IG9zCgpkZWYgbXlfZW50cnlfcG9pbnQoY29udGV4dCwgZXZlbnQpOgogICMgdXNlIHRoZSBsb2dnZXIsIG91dHB1dHRpbmcgdGhlIGV2ZW50IGJvZHkKICBjb250ZXh0LmxvZ2dlci5pbmZvX3dpdGgoCiAgICAnR290IGludm9rZWQnLAogICAgdHJpZ2dlcl9raW5kPWV2ZW50LnRyaWdnZXIua2luZCwKICAgIGV2ZW50X2JvZHk9ZXZlbnQuYm9keSwKICAgIHNvbWVfZW52PW9zLmVudmlyb24uZ2V0KCdNWV9FTlZfVkFMVUUnKSkKCiAgIyBjaGVjayBpZiB0aGUgZXZlbnQgY2FtZSBmcm9tIGNyb24KICBpZiBldmVudC50cmlnZ2VyLmtpbmQgPT0gJ2Nyb24nOgogICAgIyBsb2cgc29tZXRoaW5nCiAgICBjb250ZXh0LmxvZ2dlci5pbmZvKCdJbnZva2VkIGZyb20gY3JvbicpCiAgZWxpZiBldmVudC50cmlnZ2VyX2tpbmQgPT0gJ25hdHMnOgogICAgY29udGV4dC5sb2dnZXIuaW5mbygnSW52b2tlZCBmcm9tIG5hdHMnKQogIGVsc2U6CiAgICAjIHJldHVybiBhIHJlc3BvbnNlCiAgICByZXR1cm4gJ0Egc3RyaW5nIHJlc3BvbnNlJwo=","registry":"localhost:5000","timestamp":1545617541},"runRegistry":"localhost:5000","platform":{},"readinessTimeoutSeconds":30},"PlatformConfig":null}, "platformConfig": {"kind":"kube","webAdmin":{"enabled":true,"listenAddress":":8081"},"healthCheck":{"enabled":true,"listenAddress":":8082"},"logger":{"sinks":{"stdout":{"kind":"stdout"}},"system":[{"level":"debug","sink":"stdout"}],"functions":[{"level":"debug","sink":"stdout"}]},"metrics":{},"scaleToZero":{},"autoScale":{}}}
18.12.24 02:12:22.919            processor.nats (D) Creating worker pool {"num": 1}
18.12.24 02:12:22.920 sor.nats.w0.python.logger (D) Creating listener socket {"path": "/tmp/nuclio-rpc-bgg411hic5h0009eu970.sock"}
18.12.24 02:12:22.920 sor.nats.w0.python.logger (D) Using Python wrapper script path {"path": "/opt/nuclio/_nuclio_wrapper.py"}
18.12.24 02:12:22.920 sor.nats.w0.python.logger (D) Using Python handler {"handler": "nats_function:my_entry_point"}
18.12.24 02:12:22.920 sor.nats.w0.python.logger (D) Using Python executable {"path": "/usr/local/bin/python2"}
18.12.24 02:12:22.920 sor.nats.w0.python.logger (D) Setting PYTHONPATH {"value": "PYTHONPATH=/opt/nuclio"}
18.12.24 02:12:22.920 sor.nats.w0.python.logger (D) Running wrapper {"command": "/usr/local/bin/python2 -u /opt/nuclio/_nuclio_wrapper.py --handler nats_function:my_entry_point --socket-path /tmp/nuclio-rpc-bgg411hic5h0009eu970.sock --platform-kind kube --namespace nuclio"}
Python> 2018-12-24 02:12:23,047 [info] Replacing logger output
18.12.24 02:12:23.047 sor.nats.w0.python.logger (I) Wrapper connected
18.12.24 02:12:23.047 sor.nats.w0.python.logger (D) Waiting for start
18.12.24 02:12:23.047 sor.nats.w0.python.logger (D) Started
18.12.24 02:12:23.047                 processor (D) Creating default HTTP event source {"configuration": {"class":"sync","kind":"http","maxWorkers":1,"url":":8080","workerAllocatorName":"defaultHTTPWorkerAllocator"}}
18.12.24 02:12:23.047            processor.http (D) Creating worker pool {"num": 1}
18.12.24 02:12:23.047 sor.http.w0.python.logger (D) Creating listener socket {"path": "/tmp/nuclio-rpc-bgg411pic5h0009eu97g.sock"}
18.12.24 02:12:23.047 sor.http.w0.python.logger (D) Using Python wrapper script path {"path": "/opt/nuclio/_nuclio_wrapper.py"}
18.12.24 02:12:23.047 sor.http.w0.python.logger (D) Using Python handler {"handler": "nats_function:my_entry_point"}
18.12.24 02:12:23.047 sor.http.w0.python.logger (D) Using Python executable {"path": "/usr/local/bin/python2"}
18.12.24 02:12:23.047 sor.http.w0.python.logger (D) Setting PYTHONPATH {"value": "PYTHONPATH=/opt/nuclio"}
18.12.24 02:12:23.047 sor.http.w0.python.logger (D) Running wrapper {"command": "/usr/local/bin/python2 -u /opt/nuclio/_nuclio_wrapper.py --handler nats_function:my_entry_point --socket-path /tmp/nuclio-rpc-bgg411pic5h0009eu97g.sock --platform-kind kube --namespace nuclio"}
Python> 2018-12-24 02:12:23,072 [info] Replacing logger output
18.12.24 02:12:23.072 sor.http.w0.python.logger (I) Wrapper connected
18.12.24 02:12:23.073 sor.http.w0.python.logger (D) Waiting for start
18.12.24 02:12:23.073 sor.http.w0.python.logger (D) Started
18.12.24 02:12:23.073 .webadmin.server.triggers (D) Registered custom route {"pattern": "/{id}/stats", "method": "GET"}
18.12.24 02:12:23.073 processor.webadmin.server (D) Registered resource {"name": "triggers"}
18.12.24 02:12:23.073                 processor (W) No metric sinks configured, metrics will not be published
18.12.24 02:12:23.073                 processor (D) Starting
18.12.24 02:12:23.073 cessor.healthcheck.server (I) Listening {"listenAddress": ":8082"}
18.12.24 02:12:23.073 rocessor.nats.myNatsTopic (I) Starting {"serverURL": "http://10.0.0.3:4222", "topic": "my.topic", "queueName": "nuclio.nats-function-myNatsTopic"}
18.12.24 02:12:23.073            processor.http (I) Starting {"listenAddress": ":8080", "readBufferSize": 4096}
18.12.24 02:12:23.073 processor.webadmin.server (I) Listening {"listenAddress": ":8081"}
```
