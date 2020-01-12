<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Features](#features)
  - [Context](#context)
  - [Tags](#tags)
  - [Trace](#trace)
  - [Stats](#stats)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

From official website:

> OpenCensus is a single distribution of libraries that automatically collects traces and metrics
> from your app, displays them locally, and sends them to any analysis tool.

At its core, OpenCensus is an **instrumentation library**: you import OpenCensus, use its API, then
you get traces, metrics, stats, tags, etc. In another words, it is **NOT** a system, which means if
you want trace, you need to deploy jaeger or zipkin; if you want monitoring, you need to deploy
prometheus, etc.

Another thing to note here is "single distribution". Unlike other standard, e.g. opentracing, where
only specification is defined and actual implementations varies, OpenCensus defines its API, as well
as a standard, single distribution for client to use.

One of OpenCensus features is to integrate with web and rpc framework, making traces and metrics
available out of box. Some of the frameworks are Spring, gRPC, Dropwizard, Django, etc. Applications
do not need to understand much about OpenCensus, they just enable its features along with web & rpc
framework.

As can be seen from above description, OpenCensus is not yet another implementation of OpenTracing;
they overlap with each other and have different APIs, besides, OpenCensus has a larger scope,
including metrics, stats, etc.

*References*

- http://openCensus.io/
- https://github.com/Census-instrumentation/openCensus-specs
- https://github.com/Census-instrumentation/openCensus-go/tree/v0.3.0/examples

# Features

## Context

OpenCensus aims to provide a standard approach to support context propagation, i.e. propagate a
specific context (trace, tags) in-process (possibly between threads) and between function calls.
Some languages already have this support, like Go (context.Context) or C# (Activity). grpc has a
generic context implementation.

## Tags

Tags are values propagated through the Context subsystem inside a process and among processes by any
transport (e.g. RPC, HTTP, etc.). OpenCensus defines the API (key/value pair) and corresponding
requirements (e.g. key length limitation), as well as serialization, etc.

## Trace

OpenCensus provides tracing support, which overlaps with OpenTracing (note it overlaps with OT, not
support OT). OpenCensus has its own implementation of dealing with traces, though both OT and OC
have similar concepts from Dapper. OpenCensus supports jaeger backend, where spans are sent directly
from OpenCensus library to jaeger collector, bypassing jaeger agent (collector port 14267 is used
for jaeger agent to send span, 14268 is used for client to directly send span to jaeger collector).

*References*

https://github.com/gomods/athens/issues/392

## Stats

OpenCensus defines its own API to record metrics, and support various backend to expose metrics,
e.g. prometheus, stackdriver.
