<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
  - [Probe](#probe)
  - [App](#app)
- [Implementation](#implementation)
  - [Probe: Reporter](#probe-reporter)
- [Experiments](#experiments)
  - [Start local kubernetes](#start-local-kubernetes)
  - [Run weave scope](#run-weave-scope)
  - [Run applications](#run-applications)
  - [Use locally built weave scope](#use-locally-built-weave-scope)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Weave Scope automatically generates a map of your application, enabling you to intuitively understand,
monitor, and control your containerized, microservices based application.

[Features of weave scope](https://www.weave.works/docs/scope/latest/features/):
- Topology Mapping
- Views in Scope
- Graphic or Table Mode
- Flexible Filtering
- Powerful Search
- Real-time App and Container Metrics
- Troubleshoot and Manage Containers
- Generate Custom Metrics using the Plugin API

# Architecture

Weave Scope consists of two components: the app and the probe. The components are deployed as a single
Docker container using the scope script. A single binary is built for the two components; it uses
command line flag to determine its role.

## Probe

The probe is responsible for gathering information about the host on which it is running. This
information is sent to the app in the form of a report. probe is also called agent, it runs on
every machine. In kubernetes, probe is usually deployed as Daemonset.

## App

The app processes reports from the probe into usable topologies, serving the UI, as well as pushing
these topologies to the UI. In kubernetes, app is deployed as Deployment. Weave Cloud also has hosted
service for app; probe can need to be configured to report to Weave Cloud.

# Implementation

## Probe: Reporter

In weave scope, there is a concept "Reporter", which is a golang interface of two methods: "Name"
and "Report". Since weave scope is not just for kubernetes, there are quite a few reporters defined,
each implments the two methods, for example, docker reporter, kubernetes reporter, ecs reporter, etc.

The reporter interface is used for probe agent to report to app. The main control logic of prober
loops all reporters to make a report. app address is passed to probe agent at start time, and app
accepts reports via endpoint "/api/report".

If we comment out the "endpointReporter" in "scope/prog/prober.go", build and restart weave scope pod
(so it picks up our change), there is no connectivity information anymore. This tells that the
connectivity info is collected from endpoint reporter.

# Experiments

*Date: 12/22/2017, v1.6.7*

## Start local kubernetes

For scope 1.6.7, we use kubernetes release 1.8.6

```
# Use 'git fetch -t' if tag doesn't exist.
$ git checkout v1.8.6
$ ALLOW_PRIVILEGED=Y ALLOW_SECURITY_CONTEXT=Y KUBE_ENABLE_CLUSTER_DNS=true ENABLE_RBAC=true ./hack/local-up-cluster.sh
```

## Run weave scope

This will install a daemonset which runs weave scope agent on every node, and a deployment for weave
scope app.

```
$ kubectl apply --namespace kube-system -f "https://cloud.weave.works/k8s/scope.yaml?k8s-version=$(kubectl version | base64 | tr -d '\n')"
$ kubectl port-forward -n kube-system "$(kubectl get -n kube-system pod --selector=weave-scope-component=app -o jsonpath='{.items..metadata.name}')" 4040
```

Now we are able to access weave UI in http://localhost:4040

## Run applications

Run two pair of applications:

```
$ kubectl create -f front-back-services.yaml
$ kubectl create -f front-back-standalone.yaml
```

In the first pair of application, frontend queries backend; while in second one, there is no connection
between frontend and backend. We'll be able to see this from weave scope UI.

## Use locally built weave scope

Building weave scope is done using docker, just run "make" in root directory, a new docker image will
be available after successfully building weave scope, i.e. weaveworks/scope:latest.

We can then use "kubectl edit" to replace the versioned weave scope image to the local latest image.
