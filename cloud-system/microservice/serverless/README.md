<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

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
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

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

# References

- [CNCF WG Serverless Landscape](https://docs.google.com/spreadsheets/d/10rSQ8rMhYDgf_ib3n6kfzwEuoE88qr0amUPRxKbwVCk/edit)
