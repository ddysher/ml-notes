<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Platform](#platform)
  - [CaaS](#caas)
  - [PaaS](#paas)
  - [IaaS](#iaas)
- [Application](#application)
  - [Packaging](#packaging)
  - [Framework](#framework)
  - [Serverless](#serverless)
  - [EdgeCompute](#edgecompute)
  - [Specification](#specification)
- [Container](#container)
  - [Runtime](#runtime)
  - [Build](#build)
  - [Registry](#registry)
  - [Specification](#specification-1)
- [Insight](#insight)
  - [Monitoring](#monitoring)
  - [Logging](#logging)
  - [Tracing](#tracing)
  - [Specification](#specification-2)
- [Middleware](#middleware)
  - [Workflow](#workflow)
  - [Messaging](#messaging)
- [Storage](#storage)
  - [Filesystem](#filesystem)
  - [Database](#database)
  - [Management](#management)
- [Network](#network)
  - [Agent](#agent)
  - [Server](#server)
  - [APIGateway](#apigateway)
  - [Servicemesh](#servicemesh)
  - [Specification](#specification-3)
- [Security](#security)
  - [AuthN/Z](#authnz)
  - [Policy](#policy)
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

_**For more Kubernetes centric projects, see [kubernetes projects](../cloud-core/kubernetes/projects).**_

## PaaS

- [mesos](./platforms/mesos)
- [cloudfoundry](./platforms/cloudfoundry)
- [choerodon](./platforms/simple.md#choerodon)

## IaaS

- [openstack](./platforms/openstack)
- [opennebula](./platforms/simple.md#opennebula)

# Application

## Packaging

- [buildpacks](./application/packaging/buildpacks)

## Framework

- [spring](./application/framework/spring)
- [dapr](./application/framework/dapr)
- [micro](./application/framework/micro)

## Serverless

- [fnproject](./application/serverless/fnproject)
- [ironfunctions](./application/serverless/ironfunctions)
- [fission](./application/serverless/fission)
- [kubeless](./application/serverless/kubeless)
- [knative](./application/serverless/knative)
- [nuclio](./application/serverless/nuclio)
- [openfaas](./application/serverless/openfaas)
- [openwhisk](./application/serverless/openwhisk)
- [riff](https://projectriff.io/)

## EdgeCompute

- [kubeedge](./application/edgecompute/kubeedge)

## Specification

- [oam](./application/packaging/oam)
- [cnab](./application/packaging/cnab)
- [servicebroker](./application/framework/servicebroker)
- [cloudevents](./application/serverless/cloudevents)
- [serverless workflow](https://github.com/cncf/wg-serverless/blob/master/workflow/spec)

# Container

## Runtime

- [docker](../cloud-core/docker)
- [containerd](./container/runtime/containerd.md)
- [nvidia-docker](./container/runtime/nvidia.md)
- [runc](./container/runtime/runc.md)
- [runv](./container/runtime/runv.md)
- [rkt](./container/runtime/rkt.md)
- [cri-o](./container/runtime/cri.md#cri-o)
- [kata](https://github.com/kata-containers)
- [podman](./container/simple.md#podman)

## Build

- [jib](./container/build/jib)
- [s2i](./container/build/s2i)
- [img](./container/simple.md#img)
- [kaniko](./container/build/kaniko)
- [buildah](./container/simple.md#buildah)

## Registry

- [harbor](./container/registry/harbor)
- [dragonfly](./container/registry/dragonfly)
- [kraken](./container/registry/kraken)
- [oras](./container/registry/oras)
- [skopeo](./container/simple.md#skopeo)

## Specification

- [oci-specs](./container/oci-specs.md)
- [cni](./container/cni.md)
- [cri](./container/cri.md)
- [csi](https://github.com/container-storage-interface/spec)

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

# Middleware

## Workflow

- [argoproj](./middleware/argoproj)
- [luigi](./middleware/luigi)
- [tekton](./middleware/tekton)

## Messaging

- [nats](./middleware/nats)

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

# Network

## Agent

- [calico](./network/agent/calico)
- [canal](./network/agent/canal)
- [flannel](./network/agent/flannel)
- [weave](./network/agent/weave)
- [consul](./network/agent/consul)

## Server

- [envoy](./network/server/envoy)
- [openresty](./network/server/openresty)
- [coredns](./network/server/coredns)

## APIGateway

- [gloo](https://docs.solo.io/gloo/latest/)
- [ambassador](./network/apigateway/ambassador)

## Servicemesh

- [istio](../cloud-core/istio)
- [linkerd](./network/servicemesh/linkerd)
- [kuma](./network/servicemesh/kuma)
- [maesh](./network/servicemesh/maesh)
- [supergloo](./network/servicemesh/supergloo)
- [osm](./network/servicemesh/osm)
- [meshery](./network/servicemesh/meshery/)

## Specification

- [smi](./network/servicemesh/smi)

# Security

## AuthN/Z

- [dex](./security/dex)

## Policy

- [trireme](./security/trireme)

## Container

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
