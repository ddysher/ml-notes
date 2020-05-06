<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Platform](#platform)
  - [CaaS](#caas)
  - [PaaS](#paas)
  - [IaaS](#iaas)
- [Application](#application)
  - [Packaging](#packaging)
  - [Specification](#specification)
- [Microservice](#microservice)
  - [Runtime](#runtime)
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
  - [Runtime](#runtime-1)
  - [Image](#image)
  - [Registry](#registry)
  - [Specification](#specification-3)
- [Network](#network)
  - [Agents](#agents)
  - [Proxy](#proxy)
  - [Misc](#misc)
- [Storage](#storage)
  - [Filesystem](#filesystem)
  - [Database](#database)
  - [Management](#management)
- [Security](#security)
  - [AuthN/Z](#authnz)
  - [Container](#container-1)
- [System](#system)
  - [Virtualization](#virtualization)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A non-comprehensive list of cloud related libraries, systems, toolkits, etc (that I've investigated).

# Platform

## CaaS

- [kubernetes](../cloud-core/kubernetes)
- [openshift](./platforms/openshift)
- [rancher](./platforms/rancher)
- [kubesphere](./platforms/kubesphere)
- [rainbond](./platforms/simple.md#rainbond)

For more Kubernetes centric projects, see [kubernetes projects](../cloud-core/kubernetes/projects).

## PaaS

- [mesos](./platforms/mesos)
- [cloudfoundry](./platforms/cloudfoundry)
- [choerodon](./platforms/simple.md#choerodon)

## IaaS

- [openstack](./platforms/openstack)

# Application

## Packaging

- [buildpacks](./application/buildpacks/buildpacks.md)
- [duffle (cnab implementation)](https://duffle.sh/)

## Specification

- [servicebroker](./application/servicebroker)
- [oam](https://github.com/oam-dev/)
- [cnab](./application/cnab)

# Microservice

## Runtime

- [spring](./microservice/runtime/spring)
- [dapr](./microservice/runtime/dapr)
- [micro](./microservice/runtime/micro)

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

- [smi](./microservice/servicemesh/smi)
- [cloudevents](./microservice/serverless/cloudevents)
- [serverless workflow](https://github.com/cncf/wg-serverless/blob/master/workflow/spec)

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

## Registry

- [dragonfly](./container/dragonfly.md)
- [kraken](./container/kraken.md)
- [oras](./container/oras.md)

## Specification

- [oci-specs](./container/oci-specs.md)
- [cni](./container/cni.md)
- [cri](./container/cri.md)
- [csi](https://github.com/container-storage-interface/spec)

# Network

## Agents

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

## Filesystem

- [glusterfs](./storage/glusterfs)
- [torus](./storage/torus)

## Database

- [graphite](./storage/graphite)

## Management

- [rook](./storage/rook)
- [heketi](./storage/heketi)
- [noobaa](./storage/simple.md#noobaa)

# Security

## AuthN/Z

- [dex](./security/dex)

## Container

- [trireme](./security/trireme)
- [anchore](./security/simple.md#anchore)
- [clair](./security/simple.md#clair)

# System

## Virtualization

- [kvm](./system/virtualization/kvm)
- [qemu](./system/virtualization/qemu)
- [hyper](./system/virtualization/hyper)
- [firecracker](./system/virtualization/firecracker)
- [rust-vmm](./system/virtualization/rust-vmm)
- [crosvm](https://chromium.googlesource.com/chromiumos/platform/crosvm/)
- [cloud-hypervisor](https://github.com/cloud-hypervisor/cloud-hypervisor)
- [gVisor](https://github.com/google/gvisor)
