<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
  - [Jaeger Backend](#jaeger-backend)
  - [Jaeger Client](#jaeger-client)
  - [Storage Backend](#storage-backend)
  - [Spark Dependencies](#spark-dependencies)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 02/13/2018, v1.2*

Jaeger, inspired by Dapper and OpenZipkin, is a distributed tracing system released as open source
by Uber Technologies.

# Architecture

## Jaeger Backend

Jaeger backend consists of three components: jaeger-agent, jaeger-collector and jaeger query.

jaeger-agent is a daemon program that runs on every host and receives tracing information submitted
by applications via Jaeger client libraries. In Kubernetes, jaeger agent can be deployed as a
sidecar along side with applicaation process, or be deployed as a daemonset.

jaeger-collector receives traces from Jaeger agents and runs them through a processing pipeline.
The collectors are stateless and thus many instances of jaeger-collector can be run in parallel:
loadbalancing is done at jaeger agent side, e.g. pass a single DNS record to jaeger-agent with
multiple collector or pass a static list of collectors to agent.

jaeger-query serves the API endpoints and a React/Javascript UI. The service is stateless and is
typically run behind a load balancer, e.g. nginx.

## Jaeger Client

Jaeger project provides several opentracing compatibly client library. Application code will import
the libraries to interact with jaeger.

In golang client library, there is a sampler and reporter. The reporter starts a background goroutine
to send span out of process via a concept called `Sender`. Once there is a call to `span.Finish()`,
it will send the span to an internal channel, where the background goroutine will read out and put
to an internal buffer. Span will be sent to agent if buffer reaches limit, or batchFlushInterval
second has reached.

In python client library, it uses `tornado` library to do async processing.

## Storage Backend

Collectors require a persistent storage backend. Cassandra and ElasticSearch are the primary
supported storage backends. An in-memory backend is provided for testing.

## Spark Dependencies

This is a Spark job that collects spans from storage, analyze links between services, and stores
them for later presentation in the UI.

# References

- https://github.com/jaegertracing/jaeger
- https://github.com/jaegertracing/jaeger-kubernetes
- https://github.com/jaegertracing/spark-dependencies
- http://jaeger.readthedocs.io
