<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiments](#experiments)
  - [Install SuperGloo](#install-supergloo)
  - [Install Mesh](#install-mesh)
  - [Configure Mesh](#configure-mesh)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 11/20/2019, v0.3*

[SuperGloo](https://supergloo.solo.io/) is a project to manage and orchestrate service meshes. The
project itself is not a service mesh implementation, but rather, it manages underline meshes using
opinioned management APIs. It supports:
- istio
- linkerd
- aws appmesh
- consul
- etc

Apart from being a unified management console for different meshes, SuperGloo also manages ingress
uniformly, to avoid running separate ingress controller along side with service meshes. In addition,
SuperGloo can discover already installed service meshes, thus it's not required to install SuperGloo
before running service meshes.

SuperGloo is built by [Gloo](https://github.com/solo-io/gloo) team, an Envoy-powered API Gateway
from [solo.io](https://www.solo.io).

# Experiments

## Install SuperGloo

SuperGloo can be installed using helm or its own command line, after installation, we have:

```
kubectl --namespace supergloo-system get all
NAME                                 READY   STATUS    RESTARTS   AGE
pod/discovery-68df78f9c-rk2w4        1/1     Running   0          2m49s
pod/mesh-discovery-bc9fbcb7f-z84r9   1/1     Running   0          2m49s
pod/supergloo-59445698c5-p2fvm       1/1     Running   0          2m49s

NAME                             DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/discovery        1         1         1            1           2m49s
deployment.apps/mesh-discovery   1         1         1            1           2m49s
deployment.apps/supergloo        1         1         1            1           2m49s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/discovery-68df78f9c        1         1         1       2m49s
replicaset.apps/mesh-discovery-bc9fbcb7f   1         1         1       2m49s
replicaset.apps/supergloo-59445698c5       1         1         1       2m49s
```

## Install Mesh

Installation of service mesh can be done using CRD, e.g, following YAML installs Istio:

```
cat <<EOF | kubectl apply --filename -
apiVersion: supergloo.solo.io/v1
kind: Install
metadata:
  name: my-istio
  namespace: supergloo-system
spec:
  installationNamespace: istio-system
  mesh:
    istio:
      enableAutoInject: true
      enableMtls: true
      installGrafana: true
      installJaeger: true
      installPrometheus: true
      version: 1.0.6
EOF
```

For AWS, instead of installing App Mesh, we register App Mesh to SuperGloo, e.g.

```
cat <<EOF | kubectl apply --filename -
apiVersion: supergloo.solo.io/v1
kind: Mesh
metadata:
  name: demo-appmesh
  namespace: supergloo-system
spec:
  awsAppMesh:
    awsSecret:
      name: aws
      namespace: supergloo-system
    enableAutoInject: true
    injectionSelector:
      namespaceSelector:
        namespaces:
        - bookinfo-appmesh
    region: us-west-2
    virtualNodeLabel: vn-name
EOF
```

## Configure Mesh

Now to configure service meshes, users don't access them directly, instead, they use SuperGloo APIs,
e.g. to confgiure route traffic:

```yaml
apiVersion: supergloo.solo.io/v1
kind: RoutingRule
metadata:
  name: reviews-v3
  namespace: supergloo-system
  resourceVersion: "22111"
spec:
  destinationSelector:
    upstreamSelector:
      upstreams:
      - name: default-reviews-9080
        namespace: supergloo-system
  spec:
    trafficShifting:
      destinations:
        destinations:
        - destination:
            upstream:
              name: default-reviews-v3-9080
              namespace: supergloo-system
          weight: 1
  targetMesh:
    name: istio-istio-system
    namespace: supergloo-system
status:
  reported_by: istio-config-reporter
  state: 1
```
