<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[OSM](https://github.com/openservicemesh/osm) introduction:

> Open Service Mesh (OSM) is a lightweight, extensible, Cloud Native service mesh that allows users
> to uniformly manage, secure, and get out-of-the-box observability features for highly dynamic
> microservice environments.

> The OSM project builds on the ideas and implementations of many cloud native ecosystem projects
> including Linkerd, Istio, Consul, Envoy, Kuma, Helm, and the SMI specification.

The main advantanges of OSM compared to Istio is:
- simplicity
- open governance

Apart from Jaeger, Grafana, etc, OSM itself only contains one controller, which includes a couple
of components:
- proxy control-plane: implements envoy xDS API
- endpoint provicer: discovers underline services like kubernetes Pods, VM processes, etc
- certificate manager: provides each service in the mesh a certificate
- mesh specification: wrapps around SMI
- mesh catalog: combines all the above information and generates configuration for Envoy proxy

Each container or process will be fronted with an Envoy proxy.
