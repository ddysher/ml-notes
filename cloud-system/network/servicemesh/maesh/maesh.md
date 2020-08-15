<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiments](#experiments)
  - [Installation](#installation)
  - [Run application](#run-application)
  - [Use Maesh](#use-maesh)
  - [Analysis](#analysis)
  - [Sidenote](#sidenote)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 11/18/2019, v0.8.0*

Maesh is a service mesh solution for Kubernetes. Maesh support Service Mesh Interface (SMI) and is
strictly opt-in, which means adding Maesh to Kubernetes doesn't automatically equipt all traffic.
Note though built for Kubernetes, Maesh doesn't use CRDs for its configuration.

Architecture-wise, Maesh is different from istio, kuma, etc, in that is runs a per-node agent for
its data-plane, similar to linkerd v1. To use Maesh, application needs to be modified to call Maesh
per-node agent instead, see below.

In short, Maesh differentiates itself from other projects by:
- non-intrusive, application doesn't have to use Maesh unless it desires to
- the use of per-node agent architecture, and use Traefik (instead of envoy) for dataplane

Maesh is built by Traefik team; thus the per-node agent is a Traefik instance.

<p align="center"><img src="./assets/after-maesh-graphic.png" height="480px" width="auto"></p>

# Experiments

## Installation

After installing Maesh, we have
- a deployment `maesh-controller` for service mesh control plane
- a daemonset `maesh-mesh` for per-node data plane

Additional components are installed for observability, i.e. Jaeger, Prometheus, Grafana. Here they
are Pending because of pulling image and waiting for PV.

```
$ helm install --name=maesh --namespace=maesh maesh/maesh
...


$ kubectl get all -n maesh
NAME                                    READY   STATUS    RESTARTS   AGE
pod/grafana-core-7cb56c69cb-mjj65       0/1     Pending   0          9m3s
pod/jaeger-787f575fbd-mhcm5             1/1     Running   0          9m3s
pod/maesh-controller-6cbc9dd67b-cf5jb   1/1     Running   0          9m3s
pod/maesh-mesh-p4gg5                    1/1     Running   0          9m3s
pod/prometheus-core-996d966fb-5wn9c     0/2     Pending   0          9m3s


NAME                       TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                               AGE
service/grafana            NodePort    10.104.184.40    <none>        3000:31239/TCP                        9m3s
service/jaeger-agent       ClusterIP   None             <none>        5775/UDP,6831/UDP,6832/UDP,5778/TCP   9m3s
service/jaeger-collector   ClusterIP   10.110.4.218     <none>        14267/TCP,14268/TCP,9411/TCP          9m3s
service/jaeger-query       ClusterIP   10.108.194.220   <none>        16686/TCP                             9m3s
service/maesh-mesh-api     ClusterIP   10.100.248.15    <none>        8080/TCP                              9m3s
service/prometheus         NodePort    10.104.27.227    <none>        9090:30057/TCP                        9m3s
service/zipkin             ClusterIP   None             <none>        9411/TCP                              9m3s

NAME                        DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
daemonset.apps/maesh-mesh   1         1         1       1            1           <none>          9m3s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/grafana-core       0/1     1            0           9m3s
deployment.apps/jaeger             1/1     1            1           9m3s
deployment.apps/maesh-controller   1/1     1            1           9m3s
deployment.apps/prometheus-core    0/1     1            0           9m3s

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/grafana-core-7cb56c69cb       1         1         0       9m3s
replicaset.apps/jaeger-787f575fbd             1         1         1       9m3s
replicaset.apps/maesh-controller-6cbc9dd67b   1         1         1       9m3s
replicaset.apps/prometheus-core-996d966fb     1         1         0       9m3s
```

## Run application

Now let's deploy a regular application:

```
$ kubectl create -f experiments/sample.yaml
namespace/whoami created
serviceaccount/whoami-server created
serviceaccount/whoami-client created
deployment.apps/whoami created
deployment.apps/whoami-tcp created
service/whoami created
service/whoami-tcp created
pod/whoami-client created

$ kubectl get svc -n whoami
NAME         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
whoami       ClusterIP   10.111.200.187   <none>        80/TCP     46s
whoami-tcp   ClusterIP   10.101.41.180    <none>        8080/TCP   46s
```

Here:
- deployment `whoami` is an echo service speaking HTTP, i.e. `kubectl -n whoami exec whoami-client -- curl -s whoami.whoami.svc.cluster.local`
- deployment `whoami-tcp` is an echo service speaking TCP, i.e. `kubectl -n whoami exec -ti whoami-client -- nc whoami-tcp.whoami.svc.cluster.local 8080`
- pod `whoami-client` is a pod with client tools (e.g. curl, nc)

## Use Maesh

Now to use Maesh, application needs to change endpoint address, i.e. instead of using:

```
$ kubectl -n whoami exec whoami-client -- curl -s whoami.whoami.svc.cluster.local
Hostname: whoami-8cc58c56c-spq2m
IP: 127.0.0.1
IP: 172.17.0.11
RemoteAddr: 172.17.0.14:58520
GET / HTTP/1.1
Host: whoami.whoami.svc.cluster.local
User-Agent: curl/7.64.0
Accept: */*
```

application should use:

```
$ kubectl -n whoami exec whoami-client -- curl -s whoami.whoami.maesh
Hostname: whoami-8cc58c56c-spq2m
IP: 127.0.0.1
IP: 172.17.0.11
RemoteAddr: 172.17.0.7:45876
GET / HTTP/1.1
Host: whoami.whoami.maesh
User-Agent: curl/7.64.0
Accept: */*
Accept-Encoding: gzip
X-Forwarded-For: 172.17.0.14
X-Forwarded-Host: whoami.whoami.maesh
X-Forwarded-Port: 80
X-Forwarded-Proto: http
X-Forwarded-Server: maesh-mesh-5j574
X-Real-Ip: 172.17.0.14
```

Note, from official doc, we need to run `kubectl apply -f ./experiments/sample-patch.yaml`, but this
doesn't seem to be strictly required.

## Analysis

If we login to minikube host, we'll find following DNS records. Here 10.96.0.10 is the CoreDNS endpoint.

```
$ nslookup whoami.whoami.svc.cluster.local 10.96.0.10
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      whoami.whoami.svc.cluster.local
Address 1: 10.111.200.187 whoami.whoami.svc.cluster.local


$ nslookup whoami.whoami.maesh 10.96.0.10
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      whoami.whoami.maesh
Address 1: 10.99.132.241 maesh-whoami-whoami.maesh.svc.cluster.local


$ nslookup whoami-tcp.whoami.svc.cluster.local 10.96.0.10
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      whoami-tcp.whoami.svc.cluster.local
Address 1: 10.101.41.180 whoami-tcp.whoami.svc.cluster.local


$ nslookup whoami-tcp.whoami.maesh 10.96.0.10
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      whoami-tcp.whoami.maesh
Address 1: 10.107.193.108 maesh-whoami-tcp-whoami.maesh.svc.cluster.local
```

Following is all the services:

```
$ kubectl get svc --all-namespaces
NAMESPACE     NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)      AGE
...
maesh         maesh-whoami-tcp-whoami   ClusterIP   10.107.193.108   <none>        8080/TCP     9m10s
maesh         maesh-whoami-whoami       ClusterIP   10.99.132.241    <none>        80/TCP       9m10s
...
whoami        whoami                    ClusterIP   10.111.200.187   <none>        80/TCP       9m11s
whoami        whoami-tcp                ClusterIP   10.101.41.180    <none>        8080/TCP     9m11s
```

Pod that backing the services in maesh namespace is, as expected, the per-node daemon. For example:

```
$ kubectl get endpoints -n maesh maesh-whoami-whoami
NAME                  ENDPOINTS         AGE
maesh-whoami-whoami   172.17.0.4:5000   26m

$ kubectl get endpoints -n maesh maesh-whoami-tcp-whoami
NAME                      ENDPOINTS         AGE
maesh-whoami-tcp-whoami   172.17.0.4:5000   28m

$ kubectl get pods -n maesh -o wide | grep 172.17.0.4
maesh-mesh-p4gg5                    1/1     Running   0          38m   172.17.0.4   minikube   <none>           <none>
```

From Corefile, we'll see that Maesh rewrite the query to corresponding service in Maesh:

```
Corefile: ".:53 {
    errors
    health
    kubernetes cluster.local in-addr.arpa
    ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
    }
    prometheus :9153
    forward . /etc/resolv.conf
    cache 30
    loop

    reload
    loadbalance
    ready
}

maesh:53 {
    errors
    rewrite
    continue {
        name regex ([a-zA-Z0-9-_]*)\\.([a-zv0-9-_]*)\\.maesh maesh-{1}-{2}.maesh.svc.cluster.local

        answer name maesh-([a-zA-Z0-9-_]*)-([a-zA-Z0-9-_]*)\\.maesh\\.svc\\.cluster\\.local
        {1}.{2}.maesh
    }
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods
        insecure
        upstream
        fallthrough in-addr.arpa ip6.arpa
    }
    forward
    . /etc/resolv.conf
    cache 30
    loop
    reload
    loadbalance
}
```

In summary, when user access `whoami.whoami.maesh`, it will return service address of `maesh-whoami-whoami.maesh.svc.cluster.local`,
which is backed by per-node traefik agent.

## Sidenote

The configuration built by Maesh controller, using `curl 172.17.0.7:9000/api/configuration/current`:

```json
{
   "http":{
      "routers":{
         "readiness":{
            "entryPoints":[
               "readiness"
            ],
            "service":"readiness",
            "rule":"Path(`/ping`)"
         },
         "whoami-whoami-80-9fb41f1b6a35ef9f":{
            "entryPoints":[
               "http-5000"
            ],
            "middlewares":[
               "whoami-whoami-80-9fb41f1b6a35ef9f"
            ],
            "service":"whoami-whoami-80-9fb41f1b6a35ef9f",
            "rule":"Host(`whoami.whoami.maesh`) || Host(`10.111.200.187`)"
         }
      },
      "middlewares":{
         "whoami-whoami-80-9fb41f1b6a35ef9f":{
            "retry":{
               "attempts":2
            }
         }
      },
      "services":{
         "readiness":{
            "loadBalancer":{
               "servers":[
                  {
                     "url":"http://127.0.0.1:8080"
                  }
               ],
               "passHostHeader":true
            }
         },
         "whoami-whoami-80-9fb41f1b6a35ef9f":{
            "loadBalancer":{
               "servers":[
                  {
                     "url":"http://172.17.0.11:80"
                  },
                  {
                     "url":"http://172.17.0.8:80"
                  }
               ],
               "passHostHeader":true
            }
         }
      }
   },
   "tcp":{
      "routers":{
         "whoami-tcp-whoami-8080-5da0568567492733":{
            "entryPoints":[
               "tcp-10000"
            ],
            "service":"whoami-tcp-whoami-8080-5da0568567492733",
            "rule":"HostSNI(`*`)"
         }
      },
      "services":{
         "whoami-tcp-whoami-8080-5da0568567492733":{
            "loadBalancer":{
               "servers":[
                  {
                     "address":"172.17.0.3:8080"
                  },
                  {
                     "address":"172.17.0.9:8080"
                  }
               ]
            }
         }
      }
   }
}
```
