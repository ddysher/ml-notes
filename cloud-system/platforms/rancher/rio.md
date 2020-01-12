<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

- *Date: 10/07/2019, v0.5*

[Rio](https://rio.io/) is a MicroPaaS running on compatible Kubernetes cluster. The motivation
behind rio is:

> We saw how people were frustrated by the effort required to manage tools like Istio and Knative,
> so we built Rio. Now developers can deploy, manage, scale, and version their applications with a
> few simple commands.

At its core, rio is a Kubernetes operator, aiming to be a lightweight PaaS (MicroPaaS), to make it
easy to manage critical Kubernetes echosystm.

## Components

Rio has a couple custom resources and a CLI for ease of use, but the core is built on top of few open
source projects, including:
- istio (linkerd)
- knative
- prometheus
- grafana
- kiali
- letsencrypt
- etc.

Rio encapuslates underline components with its own concepts, mainly:
- service (different from kubernetes or istio service)
- external service
- route
- public domain

Pods and Services after running `rio up`:

```
$ kubectl get pods -n rio-system
NAME                                      READY   STATUS    RESTARTS   AGE
activator-6cf84cd794-w7twm                1/1     Running   0          154m
autoscaler-5879bc7c4b-8tkj8               1/1     Running   0          154m
build-controller-79c6d8d4b4-qstx6         1/1     Running   0          154m
buildkitd-dev-7454d484c5-z2h7s            1/1     Running   0          154m
cert-manager-77dc4d9c45-vsp72             1/1     Running   0          153m
controller-bb5bd7875-zw665                1/1     Running   0          154m
gateway-684475bbb4-lfh74                  2/2     Running   0          153m
grafana-7f687979cd-qvlm5                  1/1     Running   0          153m
istio-citadel-58b877957-n2nrk             1/1     Running   0          153m
istio-pilot-77df9c5d77-68g4b              1/1     Running   0          153m
istio-sidecar-injector-7694b75675-lqsjt   1/1     Running   8          153m
istio-telemetry-65fd7c7b54-mbtl8          2/2     Running   0          153m
kiali-754dc879cc-txr9l                    1/1     Running   0          153m
prometheus-6d9f5c6d79-7l7mc               1/1     Running   0          153m
registry-5cf4b7dd45-ps6wv                 1/1     Running   0          154m
rio-controller-64b47769b9-jcrcb           1/1     Running   6          68m
socat-6q6zv                               1/1     Running   0          154m
socat-socket-969d5fc8f-k6fzq              1/1     Running   0          154m
webhook-6fd8c49b99-hkchw                  1/1     Running   0          154m

$ kubectl get svc -n rio-system
NAME                        TYPE           CLUSTER-IP   EXTERNAL-IP   PORT(S)                                 AGE
activator                   ClusterIP      10.0.0.103   <none>        8012/TCP,8013/TCP,9090/TCP              152m
activator-service           ClusterIP      10.0.0.79    <none>        80/TCP,81/TCP,9090/TCP                  153m
activator-v0                ClusterIP      10.0.0.98    <none>        8012/TCP,8013/TCP,9090/TCP              153m
autoscaler                  ClusterIP      10.0.0.101   <none>        8080/TCP,9090/TCP                       153m
autoscaler-v0               ClusterIP      10.0.0.47    <none>        8080/TCP,9090/TCP                       153m
build-controller            ClusterIP      10.0.0.231   <none>        80/TCP                                  153m
build-controller-v0         ClusterIP      10.0.0.214   <none>        80/TCP                                  153m
buildkitd-dev               ClusterIP      10.0.0.178   <none>        80/TCP                                  153m
buildkitd-dev-v0            ClusterIP      10.0.0.120   <none>        80/TCP                                  153m
cert-manager                ClusterIP      10.0.0.17    <none>        80/TCP                                  152m
cert-manager-v0             ClusterIP      10.0.0.220   <none>        80/TCP                                  152m
controller                  ClusterIP      10.0.0.95    <none>        9090/TCP                                153m
controller-v0               ClusterIP      10.0.0.148   <none>        9090/TCP                                153m
gateway                     ClusterIP      10.0.0.25    <none>        9080/TCP,9443/TCP                       153m
gateway-v0                  LoadBalancer   10.0.0.78    <pending>     9080:30388/TCP,9443:31075/TCP           153m
grafana                     ClusterIP      10.0.0.149   <none>        3000/TCP                                152m
grafana-v0                  ClusterIP      10.0.0.209   <none>        3000/TCP                                153m
istio-citadel               ClusterIP      10.0.0.208   <none>        80/TCP                                  153m
istio-citadel-v0            ClusterIP      10.0.0.216   <none>        80/TCP                                  153m
istio-pilot                 ClusterIP      10.0.0.237   <none>        8080/TCP,15010/TCP,15014/TCP            153m
istio-pilot-v0              ClusterIP      10.0.0.122   <none>        8080/TCP,15010/TCP,15014/TCP            153m
istio-sidecar-injector      ClusterIP      10.0.0.12    <none>        443/TCP                                 153m
istio-sidecar-injector-v0   ClusterIP      10.0.0.114   <none>        443/TCP                                 153m
istio-telemetry             ClusterIP      10.0.0.88    <none>        9091/TCP,9093/TCP,15004/TCP,42422/TCP   152m
istio-telemetry-v0          ClusterIP      10.0.0.102   <none>        42422/TCP,15004/TCP,9091/TCP,9093/TCP   153m
kiali                       ClusterIP      10.0.0.187   <none>        20001/TCP                               153m
kiali-v0                    ClusterIP      10.0.0.73    <none>        20001/TCP                               153m
prometheus                  ClusterIP      10.0.0.251   <none>        9090/TCP                                153m
prometheus-v0               ClusterIP      10.0.0.184   <none>        9090/TCP                                153m
registry                    ClusterIP      10.0.0.203   <none>        80/TCP                                  153m
registry-v0                 ClusterIP      10.0.0.223   <none>        80/TCP                                  153m
socat-socket                ClusterIP      10.0.0.121   <none>        80/TCP                                  153m
socat-socket-v0             ClusterIP      10.0.0.234   <none>        80/TCP                                  153m
webhook                     ClusterIP      10.0.0.215   <none>        8090/TCP                                153m
webhook-v0                  ClusterIP      10.0.0.222   <none>        8090/TCP                                153m
```
