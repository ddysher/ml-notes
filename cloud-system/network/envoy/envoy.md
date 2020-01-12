<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [Service mesh](#service-mesh)
  - [Filter architecture](#filter-architecture)
  - [Observability](#observability)
  - [Built-in dynamic routing](#built-in-dynamic-routing)
- [Implementation](#implementation)
  - [Thread model](#thread-model)
  - [Hot restart](#hot-restart)
  - [Envoy stats](#envoy-stats)
- [DataPlane API](#dataplane-api)
  - [API v1](#api-v1)
  - [API v2](#api-v2)
- [Experiment](#experiment)
  - [Build](#build)
  - [Helloworld envoy with static binary](#helloworld-envoy-with-static-binary)
  - [Envoy sds with docker](#envoy-sds-with-docker)
  - [Envoy rds with docker](#envoy-rds-with-docker)
  - [Envoy cds with docker](#envoy-cds-with-docker)
  - [sds vs rds vs cds](#sds-vs-rds-vs-cds)
- [Experiment with kubernetes](#experiment-with-kubernetes)
  - [Run application without envoy](#run-application-without-envoy)
  - [Run edge envoy](#run-edge-envoy)
  - [Run application envoy](#run-application-envoy)
  - [Run edge envoy with sds](#run-edge-envoy-with-sds)
  - [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 07/31/2017, v1.3*
- *Date: 03/11/2018, v1.5*

## Introduction

[Envoy](https://github.com/envoyproxy/envoy) is an L7 proxy and communication bus designed for large
modern service oriented architectures. IMO, Envoy is different from other proxies (e.g. nginx, haproxy)
in the following aspects.

## Service mesh

Envoy is typically deployed along side with applications to form a service mesh. That is, each
application has an envoy instance running with it; all trafic goes in and out from this envoy. All
envoys share routing information to form this service mesh. The goal is to provide compelling feature
set for modern service oriented architectures.

## Filter architecture

At its core, envoy is an L3/L4 network proxy. A pluggable filter framework allows filters to be
written to perform different TCP proxy tasks. However, apart from L3/L4, envoy also has an additional
L7 filtering layer.

## Observability

Since envoy aims to provide a service mesh and insights into service architecture. It provides rich
dataset to monitor services, and integrates with third-party tracing tools.

## Built-in dynamic routing

Routing information can be retrived via external services, eliminate the needs to keep restarting envoy.

# Implementation

## Thread model

Three types of threads: main, worker and file flusher. All worker threads listen on all listeners
without any sharding, and kernel will take care of spreading load. Envoy's threading model is designed
to favor simplicity of programming and massive parallelism at the expense of potentially wasteful
memory and connection use if not tuned correctly.

- https://blog.envoyproxy.io/envoy-threading-model-a8d44b922310

## Hot restart

Envoy supports a large number of dynamic configuration APIs which make reloading the local configuration
almost never necessary in practice. Thus, deploying and upgrading Envoy itself is by far the most common
reason that a restart is needed and why a full binary reload is the only supported.

- https://blog.envoyproxy.io/envoy-hot-restart-1d16b14555b5

## Envoy stats

- https://blog.envoyproxy.io/envoy-stats-b65c7f363342

# DataPlane API

## API v1

The v1 APIs are JSON/REST only and polling in nature. This has a number of downsides:
- Although Envoy uses JSON schema internally, the APIs themselves are not typed, and it’s difficult
  to safely write generic servers that implement them.
- Although polling works fine in practice, more capable control planes would prefer a streaming API
  in which updates can be pushed to each Envoy as they are ready. This might lower update propagation
  time from 30–60s to 250–500ms even in extremely large deployments.

## API v2

The envoy v2 API lays the ground for standardizing data plane APIs, allowing more innovations from
the control plane.

- https://blog.envoyproxy.io/the-universal-data-plane-api-d15cec7a
- https://github.com/envoyproxy/data-plane-api

# Experiment

## Build

envoy uses bazel build system. Follow build information from github and the final binary locates at
`bazel-bin/source/exe/envoy-static`

- https://github.com/lyft/envoy/blob/29361deae91575a1d46c7a21e913f19e75622ebe/DEVELOPER.md

## Helloworld envoy with static binary

This is the simplest way of running envoy proxy:

```
$ cp ./helloworld/envoy.json /tmp/envoy.json
$ cd ~/code/workspace/src/github.com/lyft/envoy
$ ./bazel-bin/source/exe/envoy-static -c /tmp/envoy.json
$ cd -
```

## Envoy sds with docker

sds stands for service discovery service. If any defined clusters (i.e. upstream in nginx) use the
sds cluster type, a global SDS configuration must be specified. The service discovery service is a
generic REST based API used by Envoy to fetch cluster members. For each SDS cluster, Envoy will
periodically fetch the cluster members from the discovery service; and send request to these members
when request come. Here, we run envoy in docker with sds config:

```
# Run docker container using envoy config with sds.
docker run --net host -v `pwd`/basic-sds/edge-envoy.json:/etc/envoy.json lyft/envoy:1.3.0 bash -c "/usr/local/bin/envoy -c /etc/envoy.json"

# Run sds service.
cd basic-sds && python sds-service.py

# Since sds-service doesn't return anything, we don't have healthy upstream.
curl localhost:10000/lucky
```

From sds-service output, we can see that envoy calls sds service asynchronously; it will not call sds
when requests come. Here is the [sds api](https://envoyproxy.github.io/envoy/configuration/cluster_manager/sds_api.html#config-cluster-manager-sds-api).
It shows that sds service needs only expose one endpoint `GET /v1/registration/(string: service_name)`,
which accepts a service name and returns a list of hosts.

## Envoy rds with docker

rds stands for route discovery service. The connection manager configuration must specify one of rds
or route_config. If route_config is specified, the route table for the connection manager is static
and is specified in this property. If rds is specified, the connection manager’s route table will be
dynamically loaded via the RDS API. Here, we run envoy in docker with rds config:

```
# Run docker container using envoy config with rds.
docker run --net host -v `pwd`/basic-rds/edge-envoy.json:/etc/envoy.json lyft/envoy:1.3.0 bash -c "/usr/local/bin/envoy -c /etc/envoy.json --service-cluster local --service-node local"

# Run rds service.
cd basic-rds && python rds-service.py

# Since sds-service doesn't return anything, we don't have healthy upstream.
curl localhost:10000/lucky
```

The same happens where envoy periodically syncs data from rds service.

- https://envoyproxy.github.io/envoy/configuration/http_conn_man/rds.html#config-http-conn-man-rds-api

## Envoy cds with docker

cds stands for cluster discovery service. The cluster discovery service (CDS) is an optional API that
Envoy will call to dynamically fetch cluster manager members. Envoy will reconcile the API response
and add, modify, or remove known clusters depending on what is required.

## sds vs rds vs cds

They all have similar workflow.

"cds" is used to dynamically fetch clusters, whereas for "sds", we already have pre-defined clusters,
"sds" will retrieve members of a specific cluster. Not sure if it makes sense but theoretically, you
can have envoy query "cds" to find a cluster, then the cluster uses "sds" to find its members. "rds"
is different, it is used in a connection manager to find its routes, if dynamic routes configuration
is desired. For example, instead of keep restarting envoy to configure routes, we can have envoy queries
external services to update routes.

# Experiment with kubernetes

## Run application without envoy

The following digest runs an application without envoy:

```
# Create a postgres database.
kubectl create -f 1-postgres/kube-resources.yaml

# Build application "usersvc:v1" (without using envoy)
docker build -t usersvc:v1 2-usersvc-v1
kubectl create -f 2-usersvc-v1/kube-resources.yaml

# Now find host port and service port and verify it works, e.g.
curl 192.168.3.34:30272/user/health
# Create user 'alice'.
curl -X PUT -H "Content-Type: application/json" \
     -d '{ "fullname": "Alice", "password": "alicerules" }' \
     192.168.3.34:30272/user/alice
# Create user 'bob'.
curl -X PUT -H "Content-Type: application/json" \
     -d '{ "fullname": "Bob", "password": "bobrules" }' \
     192.168.3.34:30272/user/bob
# Get user
curl 192.168.3.34:30272/user/alice
curl 192.168.3.34:30272/user/bob
```

## Run edge envoy

The following digest runs an "edge envoy" which proxies request with "/user" prefix to the "usersvc"
service.

```
# Build edge proxy "edge-envoy:v1"
docker build -t edge-envoy:v1 3-edge-envoy-v1
kubectl create -f 3-edge-envoy-v1/kube-resources.yaml
```

Note that we can't test anything at this moment since the edge envoy will send request to cluster
"usersvc", which in turn has endpoint "tcp://usersvc:80", see "3-edge-envoy-v1/envoy.json". This
endpoint is the yet-to-be-created application envoy, i.e. the sidecar.

## Run application envoy

Now we run application with envoy proxy; note envoy proxy is not running as a sidecar in kubernetes;
it is launched via "entrypoint.sh".

```
# Build application "usersvc:v2" (with application envoy)
docker build -t usersvc:v2 4-usersvc-v2
kubectl delete -f 2-usersvc-v1/kube-resources.yaml
kubectl create -f 4-usersvc-v2/kube-resources.yaml

# Now that we can access application via edge proxy.
$ kubectl get svc
NAME               CLUSTER-IP   EXTERNAL-IP   PORT(S)          AGE
edge-envoy         10.0.0.95    <nodes>       8000:32202/TCP   3h
edge-envoy-admin   10.0.0.195   <nodes>       8001:31311/TCP   3h
kubernetes         10.0.0.1     <none>        443/TCP          7h
postgres           10.0.0.83    <none>        5432/TCP         7h
usersvc            10.0.0.37    <none>        80/TCP           4m

$ curl 192.168.3.34:32202/user/alice
```

In summary, at this point, we are querying edge envoy proxy which sends requests to application
sidecar envoy proxy, which in turn, accepts request and sends it to local application. The edge
proxy has endpoint 'usersvc:80'; sidecar proxy listens on port 80 and has backend '127.0.0.1:5000';
real application runs in the same pod with sidecar proxy and listens on 5000.

## Run edge envoy with sds

"sds" in envoy stands for "service discovery service". We'll skip it here since kubernetes already
handles this. In general, sds is a service that conforms to a pre-defined discovery API endpoints.
Previously, the edge envoy is configured to talk to application envoy directly; with sds, the edge
envoy is configured to first ask sds about service endpoints (API: /v1/registration/<service_name>),
then contact each endpoint.

## References

- https://www.datawire.io/guide/traffic/getting-started-lyft-envoy-microservices-resilience/
