<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [Components](#components)
  - [Features](#features)
- [Experiments](#experiments)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

## Introduction

Micro is a microservice ecosystem simplifying distributed development. It provides the fundamental
building blocks for developing distributed applications. Compared to go-kit, micro has a broader
view: it is described as a platform than a toolkip library, think of it as Spring Cloud for Go (or
Cloud Native).

## Components

- [Go-micro](https://github.com/micro/go-micro): A pluggable RPC framework for Go. Following
  components, i.e. API, web, cli, bot and sidecar are all located at a different [repository](https://github.com/micro/micro),
  and use go-micro internally to implement their feature.
- [API](https://github.com/micro/micro/tree/master/api): An API Gateway. A single HTTP entry point.
  Dynamically routing HTTP requests to RPC services.
- [Web](https://github.com/micro/micro/tree/master/web): A UI and Web Gateway. Build your web apps
  as micro services.
- [CLI](https://github.com/micro/micro/tree/master/cli): A command line interface. Interact with your
  micro services.
- [Bot](https://github.com/micro/micro/tree/master/bot): A bot for slack and hipchat. CLI equivalent
  via messaging.
- [Sidecar](https://github.com/micro/micro/tree/master/car): A go-micro proxy. All the features of
  go-micro over HTTP. The micro sidecar builds on go-micro with the same defaults and pluggability.

## Features

- Service Discovery: Automatic service registration and name resolution. All services written in
  micro has built-in service discovery, which by default depends on consul.
- Load Balancing: Client side load balancing built on discovery.
- Sync Communication: RPC based communication with support for bidirectional streaming.
- Async Communication: Native PubSub messaging built in for event driven architectures. By default,
  it uses consul for messaging (same instance as service discovery).
- Message Encoding: Dynamic encoding based on content-type with protobuf and json out of the box.
- Service Interface: All features are wrapped up in a simple high level interface.

# Experiments

Follows: https://github.com/micro/examples/tree/master/greeter

Note: run consul with:

```
docker run --net=host -d consul:1.0.6
```

List consul services with:

```
docker run --net=host consul:1.0.6 consul catalog services
```

# References

- https://micro.mu/blog/2016/03/20/micro.html
- https://micro.mu/blog/2016/04/18/micro-architecture.html
- https://micro.mu/blog/2016/12/28/micro-past-present-future.html
- https://micro.mu/docs/index.html
- https://micro.mu/docs/architecture.html
