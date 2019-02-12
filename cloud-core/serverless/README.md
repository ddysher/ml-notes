<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Projects](#projects)
  - [cloudevents](#cloudevents)
  - [fnproject](#fnproject)
  - [ironfunctions](#ironfunctions)
  - [fission](#fission)
  - [kubeless](#kubeless)
  - [knative](#knative)
  - [nuclio](#nuclio)
  - [openfaas](#openfaas)
  - [openwhisk](#openwhisk)
- [Comparison](#comparison)
  - [architecture](#architecture)
  - [gateway](#gateway)
  - [execution model](#execution-model)
  - [language support](#language-support)
  - [build support](#build-support)
  - [trigger support](#trigger-support)
  - [sync/async execution](#syncasync-execution)
  - [workflow extension](#workflow-extension)
  - [monitoring and logging](#monitoring-and-logging)
  - [performance and scalability](#performance-and-scalability)
  - [other features](#other-features)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Projects

## cloudevents

*Date: 12/21/2018, v0.2*

CloudEvents, at its core, defines a set of metadata, called attributes, about the event being
transferred between systems, and how those pieces of metadata should appear in that message. This
metadata is meant to be the minimal set of information needed to route the request to the proper
component and to facilitate proper processing of the event by that component. Data that is not
intended for that purpose should instead be placed within the event (the `data` attribute) itself.

Example:

```json
{
    "specversion" : "0.2",
    "type" : "com.github.pull.create",
    "source" : "https://github.com/cloudevents/spec/pull/123",
    "id" : "A234-1234-1234",
    "time" : "2018-04-05T17:31:00Z",
    "comexampleextension1" : "value",
    "comexampleextension2" : {
        "othervalue": 5
    },
    "contenttype" : "text/xml",
    "data" : "<much wow=\"xml\"/>"
}
```

## fnproject

**Overview**

The Fn project is an open-source container-native serverless platform from Oracle.

The core of fn is a component called `fnserver`, which handles CRUD operations for routes and
functions, sync and async function invocation, etc. For each function, fnserver saves the information
into sql database, including request, source code, response, etc. For each invocation of a function,
fnserver will start a container, or if invocation interval is short, it will reuse existing container.
fnserver will clean up idle containers automatically, and containers that have done function execution
but haven't been cleaned up, will enter `Paused` status. The supporting services for `fnserver`
includes:
- SQL: MySQL, sqlite3, Postgres
- Queue: Redis, Kafka
- Registry: Docker Registry

There are two sub-project in fn:
- fn-lb: fn-lb deals with load balancing and intelligent traffic routing. It manages a pool of
  fnservers and routes invocations to these hot functions to ensure optimal performance. If fn-lb
  is running, client interacts with fn-lb instead of fnservers.
- fn-flow: fn-flow is a code-first approach to orchestrate function execution flow by using the Java
  8 CompletableFutures API with methods such as thenApply() or then thenCompose(), etc. No graphical
  tool or lengthy YAML file is required; the composition of functions is done with Java 8 constructs
  only and is therefore easily readable.

**Caveats**

Unlike a 'real' serverless platform, in Fn, user uses `fn` command line to build a container and
then push to a registry. Even though everything is wrapped via the cli, user is still exposed to
the concept of container. For similar reasons, Fn's Kubernetes integration is not quite native.

Another difference is that unlike other serverless platform, user code contains full runnable source,
i.e. not just a function. For example:

```go
package main

import (
	...
	fdk "github.com/fnproject/fdk-go"
)

func main() {
	fdk.Handle(fdk.HandlerFunc(myHandler))
}

func myHandler(ctx context.Context, in io.Reader, out io.Writer) {
	...
}
```

*References*

- https://hackernoon.com/playing-with-the-fn-project-8c6939cfe5cc
- https://developer.oracle.com/opensource/serverless-with-fn-project
- https://www.n-k.de/2017/10/fnproject-first-impressions.html

## ironfunctions

IronFunctions is a serverless microservices platform by https://iron.io.

The core team working on serverless platform from iron.io joined Oracle to build fnproject, and the
concepts and architecture in ironfunctions and fnproject are quite similar. ironfunctions are not
actively maintained, thus it can be seen as superceded by fnproject.

## fission

ref: [fission](./fission)

## kubeless

ref: [kubeless](./kubeless)

## knative

ref: [knative](./knative)

## nuclio

ref: [nuclio](./nuclio)

## openfaas

ref: [openfaas](./openfaas)

## openwhisk

Apache OpenWhisk (Incubating) is an open source, distributed Serverless platform that executes functions
(fx) in response to events at any scale. OpenWhisk manages the infrastructure, servers and scaling using
Docker containers so you can focus on building amazing and efficient applications.

The OpenWhisk platform supports a programming model in which developers write functional logic (called
`Actions`), in any supported programming language, that can be dynamically scheduled and run in response
to associated events (via `Triggers`) from external sources (`Feeds`) or from HTTP requests. The project
includes a REST API-based Command Line Interface (CLI) along with other tooling to support packaging,
catalog services and many popular container deployment options.

OpenWhisk itself mainly consists of only two custom components: the `Controller` and the `Invoker`.
Everything else is already there, i.e. Nginx, Kafka, Docker, CouchDB, Consul.

*References*

- https://thenewstack.io/behind-scenes-apache-openwhisk-serverless-platform/
- https://github.com/apache/incubator-openwhisk/blob/0.9.0-incubating/docs/about.md

# Comparison

Following is a list of comparisons between different faas options.

## architecture

Most platforms use control plane + data plane architecture: the difference is the division of work,
i.e. how many work is done in control plane and how many work is done in data plane.

## gateway

kubeless, nulico, etc have no built-in gateway: it creates ingress rules dynamically based on user
function.

openfaas, fission, etc have built-in gateway which will be programmed by those components themselves.

## execution model

kubeless, openfaas, nulico, etc is "new deployment" based execution mode, i.e. for each function,
they will create a new deployment with 1 replica. Given the runtime, we can create function directly.

fission, etc is "pool based" based execution mode by default, i.e. fission manages a pool of pods
and dynamically load funtions when request comes. To use pool based execution, we need to create
environment (abstraction over runtime) first, then create functions using the environment.

Note this is not a strict difference: a platform can support both execution model, e.g. fission
supports `newdeploy` and `poolmgr` executor type.

## language support

kubeless, fission, etc by default use "souce code based approach", that is, user only needs to submit
code and doesn't deal with containers: it is the platform that creates containers based on requested
runtime and user code.

openfaas, etc use "container based approach", i.e. user directly submits container to the platform,
which then directly launch the container.

Note this is not a strict difference: a platform can support both approaches.

## build support

kubeless, fnproject, nuclio, etc use "registry based approach", that is, they build a docker image
then push it to registry.

fission, etc use "artifact based approach", where build artifacts like binary will be pushed to a
storage service.

At runtime, most platforms dynamically load user code, e.g. using golang plugin, python module, etc.

## trigger support

All platforms support triggers, though implementation might vary.

In kubeless, the control plane handles trigger management: it directly sends events to function
through kubernetes service, not through gateway (e.g. ingress).

In openfaas, fission, etc, trigger is 'external' to faas platform: standalone trigger components
receive events and send events to functions through gateway.

In nuclio, etc, the data plane handles trigger management: a per-function shim is responsible to
watch trigger event and send to in-process function.

## sync/async execution

Not all platoform support async execution. For those who support, a message queue is usually needed,

fission, nuclio, openfaas, etc support async execution and use nats by default.

openwhisk, etc support async execution and use kafka by default.

## workflow extension

Workflow extension means chaining function executions. Not all platoform support workflow.

fission, etc support DAG style workflow, user needs to deploy a yaml file defining the workflow.

fnproject, etc support workflow using code approach, i.e. user codes workflow directly using java.

## monitoring and logging

Some platforms have built-in monitoring with prom, some delegate to external ones.

## performance and scalability

performance and scalability varies depending on architecture.

## other features

- live reload: live reload container when funciton code changes
- record replay: record request and replay in the future
- canary deployment: rollout and rollback new functions automatically
- concurrent execution: multiple workers in a container to leverage multiple cpus
- data binding: provides easy access to external data services like database, message queue
- partition: partition streams or data to multiple replicas of the same function
