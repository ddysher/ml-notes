<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

OpenFaaS (Functions as a Service) is a framework for building serverless functions with Docker and
Kubernetes which has first class support for metrics. Any process can be packaged as a function
enabling you to consume a range of web events without repetitive boiler-plate coding.

OpenFaaS is written in Golang with support from VMWare.

# Components

*Date: 12/20/2018*

OpenFaaS contains a couple of components:

```
# Under github.com/openfaas/faas
$ kubectl apply -f ./yaml

$ kubectl get pods -n openfaas
NAME                            READY   STATUS    RESTARTS   AGE
alertmanager-f5b4dfb8b-9pf42    1/1     Running   0          2h
gateway-66698df8cf-cr9fk        2/2     Running   0          2h
nats-776b844b7-4xd7r            1/1     Running   0          2h
prometheus-7d78d54b57-6z6pb     1/1     Running   0          2h
queue-worker-68c56d7ff6-rcsgg   1/1     Running   0          2h
```

**Gateway**

Gateway is the core component in openfaas. It defines several endpoints and proxies requests from
users to functions.

To use openfaas, user first creates/deploys functions via:

```
$ faas-cli deploy -f stack.yml
Deploying: wordcount.

Deployed. 202 Accepted.
URL: http://127.0.0.1:31112/function/wordcount
```

```yaml
# stack.yml
provider:
  name: faas
  gateway: http://127.0.0.1:31112  # can be a remote server

functions:
  # Counts words in request with `wc` utility
  wordcount:
    lang: dockerfile
    image: functions/alpine:latest
    fprocess: "wc"
    skip_build: true
```

`faas-cli` sends requests to gateway via  `POST /system/functions` endpoint, which then proxies the
request to backend provider. In case of Kubernetes, the backend provider is `faas-netes`, which is
a container running along side with gateway:

```
$ kubectl describe pods -n openfaas gateway-66698df8cf-cr9fk | grep "Container ID" -C 1
  gateway:
    Container ID:   docker://f00d91400e73e4c2125c095cbb4236154c8204496e7ab8fb0e04b63af895ac6c
    Image:          openfaas/gateway:0.9.11
--
--
  faas-netes:
    Container ID:   docker://54cc95aa4eeac300a0c432d90605cf989fa85debb804e508c9fc6be39fd0fe63
    Image:          openfaas/faas-netes:0.6.3
```

The `faas-netes` will create Deployment (default 1 replica) and Service in Kubernetes. There is no
storage in gateway: everything is proxied to backend provider. Example providers are Kubernetes,
Swarm, etc.

Now when user sends real request to function, request first hits gateway via url `/functions/<name>`,
then it is forwarded to backend provider. Backend provider locates function (e.g. use Service in Kubernetes)
then forwards the request to function. Note as we'll see below, the request is actually fowarded to
watchdog, which will then fork user process, i.e.

```
                            proxy                      proxy                        fork
request --------> gateway --------> backend provider ---------> function watchdog -------> user code
                    |                         |                        |                      |
                    |        same pod         |                        |     same container   |
```

The two `proxy` uses golang `io.Copy`.

**Watchdog**

Every function in openfaas runs in a container and is wrapped around a `watchdog`; in an other words,
it is the init process for all openfaas functions.

watchdog will fork user process, handles request/response with gateway. User code only needs to work
with stdin and stdout that are piped from watchdog. There is a new project called `of-watchdog`, which
is the next generation watchdog. It defines several modes for user code, i.e. not just stdin/stdout.

**NATS**

nats is used for async processing. For async invocation, user sends request to `/async-functions/<name>`
instead of `/function/<name>`. In this case, gateway returns `202 Accepted` immediately. Under the hood,
gateway will simply put the request into nats.

Note here it is the gateway that puts the request into nats, it will not proxy the request to backend,
i.e. backend provider doesn't handle async invocation.

**queue worker**

Queue worker is used for async processing. It subscribes to nats topics from gateway, and invokes
functions whenever there's message from nats queue.

**prometheus + alertmanager**

Prometheus is used for monitoring, it has function metrics, e.g. number of invocation for each function.
Alertmanager is for alert as well as autoscaling.

**connector**

There are connectors in openfaas which connects external sources to openfaas. External connector needs
to be deployed to cluster as well (e.g. deployment in kubernetes).

Connectors are external to openfaas gateway. For example, kafka connector will consume topics from
kafka, and invokes functions through openfaas gateway just like normal user. The connector is responsible
to keep a map of functions <-> topics.

*References*

- https://github.com/openfaas/faas/
- https://github.com/openfaas/faas-netes/
- https://github.com/openfaas/nats-queue-worker
- https://github.com/openfaas-incubator/kafka-connector
