<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Platform](#platform)
  - [CaaS](#caas)
  - [PaaS](#paas)
  - [IaaS](#iaas)
- [Application](#application)
  - [Specification](#specification)
- [Microservice](#microservice)
  - [Framework](#framework)
  - [APIGateway](#apigateway)
  - [Servicemesh](#servicemesh)
  - [Serverless](#serverless)
  - [Specification](#specification-1)
- [Middleware](#middleware)
  - [Workflow](#workflow)
  - [Messaging](#messaging)
- [Insight](#insight)
  - [Monitoring](#monitoring)
  - [Logging](#logging)
  - [Tracing](#tracing)
  - [Specification](#specification-2)
- [Container](#container)
  - [Runtime](#runtime)
  - [Image](#image)
  - [Specification](#specification-3)
- [Network](#network)
  - [CNIs](#cnis)
  - [Proxy](#proxy)
  - [Misc](#misc)
- [Storage](#storage)
- [Security](#security)
- [System](#system)
  - [Virtualization](#virtualization)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A non-comprehensive list of cloud related libraries, systems, toolkits, etc (that I've investigated).

# Platform

## CaaS

- [kubernetes](../cloud-core/kubernetes)
- [openshift](./platforms/openshift)
- [rancher](./platforms/rancher)

## PaaS

- [mesos](./platforms/mesos)
- [micro](./platforms/micro)
- [cloudfoundry](./platforms/cloudfoundry)

## IaaS

- [openstack](./platforms/openstack)

# Application

## Specification

- [servicebroker](./application/servicebroker)
- [oam](https://github.com/oam-dev/)

# Microservice

## Framework

- [spring](./microservice/framework/spring)

## APIGateway

- [gloo](https://docs.solo.io/gloo/latest/)
- [ambassador](./microservice/apigateway/ambassador)

## Servicemesh

- [istio](../cloud-core/istio)
- [linkerd](./microservice/servicemesh/linkerd)
- [kuma](./microservice/servicemesh/kuma)
- [maesh](./microservice/servicemesh/maesh)
- [consul](./microservice/servicemesh/consul)
- [supergloo](./microservice/servicemesh/supergloo)
- [meshery](./microservice/servicemesh/meshery/)

## Serverless

- [fnproject](./microservice/serverless/fnproject)
- [ironfunctions](./microservice/serverless/ironfunctions)
- [fission](./microservice/serverless/fission)
- [kubeless](./microservice/serverless/kubeless)
- [knative](./microservice/serverless/knative)
- [nuclio](./microservice/serverless/nuclio)
- [openfaas](./microservice/serverless/openfaas)
- [openwhisk](./microservice/serverless/openwhisk)
- [riff](https://projectriff.io/)

For comparisions of the projects, refer to [README](./microservice/serverless/README.md).

## Specification

- [smi](./servicemesh/smi)
- [cloudevents](./serverless/cloudevents)

# Middleware

## Workflow

- [argoproj](./middleware/argoproj)
- [luigi](./middleware/luigi)

## Messaging

- [nats](./middleware/nats)

# Insight

## Monitoring

- [prometheus](./insight/prometheus)

## Logging

- [elastic](./insight/elastic)
- [fluent](./insight/fluent)

## Tracing

- [jaeger](./insight/jaeger)

## Specification

- [opencensus](./insight/specifications/opencensus.md)
- [opentracing](./insight/specifications/opentracing.md)
- [opentelemetry](./insight/specifications/opentelemetry.md)
- [openmetrics](./insight/specifications/openmetrics.md)

# Container

## Runtime

- [docker](../cloud-core/docker)
- [containerd](./container/containerd.md)
- [nvidia-docker](./container/nvidia.md)
- [runc](./container/runc.md)
- [runv](./container/runv.md)
- [rkt](./container/rkt.md)

## Image

- [jib](./container/jib.md)
- [s2i](./container/s2i.md)
- [buildpacks](./container/buildpacks/buildpacks.md)
- [dragonfly](./container/dragonfly.md)
- [kraken](./container/kraken.md)

## Specification

- [oci-specs](./container/oci-specs.md)
- [cni](./container/cni.md)
- [cri](./container/cri.md)
- [csi](https://github.com/container-storage-interface/spec)

# Network

## CNIs

- [calico](./network/calico)
- [canal](./network/canal)
- [flannel](./network/flannel)
- [weave](./network/weave)

## Proxy

- [envoy](./network/envoy)
- [openresty](./network/openresty)

## Misc

- [coredns](./network/coredns)

# Storage

- [glusterfs](./storage/glusterfs)
- [graphite](./storage/graphite)
- [heketi](./storage/heketi)
- [rook](./storage/rook)
- [torus](./storage/torus)

# Security

- [dex](./security/dex)
- [trireme](./security/trireme)

# System

## Virtualization

- [hyper](./system/hyper)
- [qemu-kvm](./system/qemu-kvm)
