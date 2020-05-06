<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Architecture](#architecture)
  - [Concepts](#concepts)
  - [Dapr APIs](#dapr-apis)
- [Experiments](#experiments)
  - [Local Hello-world](#local-hello-world)
  - [Kubernetes Hello-world](#kubernetes-hello-world)
  - [More Samples](#more-samples)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 01/18/2020, v0.3*

> Dapr is a portable, serverless, event-driven runtime that makes it easy for developers to build
> resilient, stateless and stateful microservices that run on the cloud and edge and embraces the
> diversity of languages and developer frameworks.

Dapr stands for Distributed Application Runtime.

## Architecture

Dapr architecture is fairly simple: a sidecar container or process is running for each application
service. This sidecar/process contains most of the features mentioned below, e.g. pub/sub, state
management. Application service needs to talk to dapr API to leverage these features, either via
direct HTTP call or SDKs generated for different programming languages.

For more information, refer to [dapr overview](https://github.com/dapr/docs/blob/v0.3.0/overview.md).

## Concepts

The core concepts (or building blocks) of Dapr are:
- [Service Invocation](https://github.com/dapr/docs/blob/v0.3.0/concepts/service-invocation/service-invocation.md)
  - services communicate with each other through well-known dapr endpoints in the form of http or gRPC messages
  - all traffic go through dapr sidecar with app-id, thus eliminating the requirement of service discovery
- [State Management](https://github.com/dapr/docs/blob/v0.3.0/concepts/state-management/state-management.md)
  - support different policies for concurrency, consistency, etc
  - state store is pluggable, include redis, azure cosmosdb, aws dynamodb, gcp cloud spanner, cassandra, etc
- [Publish/Subscribe Messaging](https://github.com/dapr/docs/blob/v0.3.0/concepts/publish-subscribe-messaging/README.md)
  - messaging bus is pluggable, include rabbitmq, nats, etc, and is developed as [contrib](https://github.com/dapr/components-contrib/tree/master/pubsub)
- [Event driven resource binding](https://github.com/dapr/docs/blob/v0.3.0/concepts/bindings/README.md)
  - input bindings are used to trigger your application when an event from an external resource has occurred
  - output bindings allow users to invoke external resources
  - supported resource bindings are kafka, redis, aws s3, kubernetes events, etc
- [Distributing tracing](https://github.com/dapr/docs/blob/v0.3.0/concepts/distributed-tracing/README.md)
  - dapr adds a http/grpc middleware to the dapr sidecar; the middleware intercepts all dapr and
    application traffic and automatically injects correlation IDs to trace distributed transactions.
  - dapr uses opentelemetry for distributed traces and metrics collection
  - metrics backend is pluggable, include zipkin, jaeger, azure monitor, etc
- [Actors](https://github.com/dapr/docs/tree/v0.3.0/concepts/actor)
  - dapr provides an implementation of the [actor model](https://www.brianstorti.com/the-actor-model/)

Other concepts:
- [Component](https://github.com/dapr/components-contrib): components are grouped into different group
  and implements its API interfaces to support different backends; for example, pub/sub components
  include nats, rabbitmq, etc, each impelements a Go interface `PubSub`. Each component has configuration
  file to describe its metadata information, e.g. [an example redis component configuration](https://github.com/dapr/docs/blob/v0.3.0/concepts/components/redis.md#configuration)
- [Secret](https://github.com/dapr/docs/blob/v0.3.0/concepts/components/secrets.md): used for component encryption.

## Dapr APIs

For each of the above features, Dapr provides following APIs:
- [service invocation](https://github.com/dapr/docs/blob/v0.3.0/reference/api/service_invocation.md), e.g. `v1.0/invoke`
- [state management](https://github.com/dapr/docs/blob/v0.3.0/reference/api/state.md), e.g. `/v1.0/state`
- [pub/sub messaging](https://github.com/dapr/docs/blob/v0.3.0/reference/api/pubsub.md), e.g. `/v1.0/publish`
- [resource binding](https://github.com/dapr/docs/blob/v0.3.0/reference/api/bindings.md), e.g. `/v1.0/binding`
- [actors](https://github.com/dapr/docs/blob/v0.3.0/reference/api/actors.md)

# Experiments

*Date: 01/18/2020, v0.3*

## [Local Hello-world](https://github.com/dapr/samples/tree/v0.3.0/1.hello-world)

To run dappr locally:

```
$ dapr init --install-path $HOME/code/workspace/bin
```

Then two containers are created:

```
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                      NAMES
48e7ad8b4682        daprio/dapr         "./placement"            32 seconds ago      Up 29 seconds       0.0.0.0:50005->50005/tcp   dapr_placement
fd7126bed921        redis               "docker-entrypoint.s…"   46 seconds ago      Up 44 seconds       0.0.0.0:6379->6379/tcp     dapr_redis
```

Now run node application, note there:
- the first port option `--app-port` is the port where application listens;
- the second option `--port` provides information about the port where `daprd` listens.

The `daprd` port is passed to application code via `DAPR_HTTP_PORT` environment variable.

```
$ dapr run --app-id nodeapp --app-port 3000 --port 3500 node app.js
ℹ️  Starting Dapr with id nodeapp. HTTP Port: 3500. gRPC Port: 37557
✅  You're up and running! Both Dapr and your app logs will appear here.

== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="starting Dapr Runtime -- version 0.3.0 -- commit v0.3.0-rc.0-1-gfe6c306-dirty"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="log level set to: info"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="standalone mode configured"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="dapr id: nodeapp"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="loaded component messagebus (pubsub.redis)"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="loaded component statestore (state.redis)"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="application protocol: http. waiting on port 3000"
== APP == Node App listening on port 3000!
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="application discovered on port 3000"
== DAPR == 2020-01-18 11:29:28.788073 I | redis: connecting to localhost:6379
== DAPR == 2020-01-18 11:29:28.788604 I | redis: connected to localhost:6379 (localAddr: [::1]:51510, remAddr: [::1]:6379)
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="Initialized service discovery to standalone"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actor runtime started. actor idle timeout: 1h0m0s. actor scan interval: 30s"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actors: starting connection attempt to placement service at localhost:50005"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="http server is running on port 3500"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="gRPC server is running on port 37557"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="local service entry announced"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="dapr initialized. Status: Running. Init Elapsed 111.513315ms"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actors: established connection to placement service at localhost:50005"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actors: placement order received: lock"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actors: placement order received: update"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actors: placement tables updated"
== DAPR == time="2020-01-18T11:29:28+08:00" level=info msg="actors: placement order received: unlock"
```

Default component configurations are created:
```
$ ls components
redis_messagebus.yaml  redis.yaml
```

Here daprd is spawned from dapr, which listens on:
- port 3500 for http; this can be given in `dapr --port` option, or a random port
- port 37557 for grpc; this can be given in `dapr --grpc-port` option, or a random port

In addition, daprd knows:
- where application is running, via its `--app-port` option
- where dapr-placement is running (a docker container created from `dapr init`), via its `--placement-address` option

```
$ ps aux | grep dapr
deyuan    8048  0.2  0.2 134220 23728 pts/0    Sl+  11:29   0:00 dapr run --app-id nodeapp --app-port 3000 --port 3500 node app.js
deyuan    8070  0.4  0.4 165956 38412 pts/0    Sl+  11:29   0:00 daprd --dapr-id nodeapp --dapr-http-port 3500 --dapr-grpc-port 37557 --log-level info --max-concurrency -1 --protocol http --app-port 3000 --placement-address localhost:50005
```

Send request to application. Note here we are POSTing against daprd port, not application port.

```
dapr invoke --app-id nodeapp --method neworder --payload '{"data": { "orderId": "41" } }'
```

Or via raw HTTP. Pay attention to application id `nodeapp`.
```
curl -XPOST -d @sample.json http://localhost:3500/v1.0/invoke/nodeapp/method/neworder
```

```
curl http://localhost:3500/v1.0/invoke/nodeapp/method/order
```


Run Python app

```
$ dapr run --app-id pythonapp python app.py
ℹ️  Starting Dapr with id pythonapp. HTTP Port: 43779. gRPC Port: 34731
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="starting Dapr Runtime -- version 0.3.0 -- commit v0.3.0-rc.0-1-gfe6c306-dirty"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="log level set to: info"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="standalone mode configured"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="dapr id: pythonapp"
✅  You're up and running! Both Dapr and your app logs will appear here.

== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="loaded component messagebus (pubsub.redis)"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="loaded component statestore (state.redis)"
== DAPR == 2020-01-18 12:20:10.420164 I | redis: connecting to localhost:6379
== DAPR == 2020-01-18 12:20:10.423128 I | redis: connected to localhost:6379 (localAddr: [::1]:51792, remAddr: [::1]:6379)
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="Initialized service discovery to standalone"
== DAPR == time="2020-01-18T12:20:10+08:00" level=warning msg="failed to init input bindings: app channel not initialized"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actor runtime started. actor idle timeout: 1h0m0s. actor scan interval: 30s"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actors: starting connection attempt to placement service at localhost:50005"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="http server is running on port 43779"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="gRPC server is running on port 34731"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="local service entry announced"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="dapr initialized. Status: Running. Init Elapsed 5.6097600000000005ms"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actors: established connection to placement service at localhost:50005"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actors: placement order received: lock"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actors: placement order received: update"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actors: placement tables updated"
== DAPR == time="2020-01-18T12:20:10+08:00" level=info msg="actors: placement order received: unlock"

deyuan    8048  0.0  0.3 134220 24676 pts/0    Sl+  11:29   0:01 dapr run --app-id nodeapp --app-port 3000 --port 3500 node app.js
deyuan    8070  0.3  0.4 165956 39152 pts/0    Sl+  11:29   0:10 daprd --dapr-id nodeapp --dapr-http-port 3500 --dapr-grpc-port 37557 --log-level info --max-concurrency -1 --protocol http --app-port 3000 --placement-address localhost:50005
deyuan   14971  0.1  0.2 134156 23872 pts/3    Sl+  12:20   0:00 dapr run --app-id pythonapp python app.py
deyuan   14992  0.6  0.4 165956 39020 pts/3    Sl+  12:20   0:00 daprd --dapr-id pythonapp --dapr-http-port 43779 --dapr-grpc-port 34731 --log-level info --max-concurrency -1 --protocol http --placement-address localhost:50005

$ curl http://localhost:3500/v1.0/invoke/nodeapp/method/order
```

List all applications. The information is saved to `/tmp` directory from `dapr`.

```
$ dapr list
  APP ID     HTTP PORT  GRPC PORT  APP PORT  COMMAND        AGE  CREATED              PID
  nodeapp    3500       37557      3000      node app.js    51m  2020-01-18 11:29.28  8048
  pythonapp  43779      34731      0         python app.py  1m   2020-01-18 12:20.10  14971
```

## [Kubernetes Hello-world](https://github.com/dapr/samples/tree/v0.3.0/2.hello-kubernetes)

Run dapr in Kubernetes with a single command (non-prod):

```
$ dapr init --kubernetes
```

Then, inspect resources created:

```
$ kubectl get all -n default
NAME                                         READY   STATUS    RESTARTS   AGE
pod/dapr-operator-6b8d659466-8gn9r           1/1     Running   0          3h22m
pod/dapr-placement-6494df4f78-l9nzc          1/1     Running   0          3h22m
pod/dapr-sidecar-injector-588d69dc9b-7l6sl   1/1     Running   0          3h22m

NAME                            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/dapr-api                ClusterIP   10.0.0.99    <none>        80/TCP    3h22m
service/dapr-placement          ClusterIP   10.0.0.46    <none>        80/TCP    3h22m
service/dapr-sidecar-injector   ClusterIP   10.0.0.212   <none>        443/TCP   3h22m
service/kubernetes              ClusterIP   10.0.0.1     <none>        443/TCP   3h25m

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dapr-operator           1/1     1            1           3h22m
deployment.apps/dapr-placement          1/1     1            1           3h22m
deployment.apps/dapr-sidecar-injector   1/1     1            1           3h22m

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/dapr-operator-6b8d659466           1         1         1       3h22m
replicaset.apps/dapr-placement-6494df4f78          1         1         1       3h22m
replicaset.apps/dapr-sidecar-injector-588d69dc9b   1         1         1       3h22m


$ kubectl get crds
NAME                     CREATED AT
components.dapr.io       2020-01-18T09:01:35Z
configurations.dapr.io   2020-01-18T09:01:35Z


$ kubectl get components
No resources found.


$ kubectl get configurations.dapr.io
No resources found.
```

## More Samples

- https://github.com/dapr/samples
