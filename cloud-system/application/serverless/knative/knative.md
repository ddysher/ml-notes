<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Component](#component)
  - [Build](#build)
  - [Serving](#serving)
  - [Eventing](#eventing)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 12/29/2018*

Knative is not a native serverless framework, e.g. it doesn't support source (function) to deployment,
rather, it extends Kubernetes to provide a set of middleware components that are essential to build
modern, source-centric, and container-based applications that can run anywhere. Each of the components
under the Knative project attempt to identify common patterns and codify the best practices that are
shared by successful real-world Kubernetes-based frameworks and applications. The components in knative
include (can be used independently):
- Build: Source-to-container build orchestration
- Eventing: Management and delivery of events
- Serving: Request-driven compute that can scale to zero

In short, Knative builds on top of Kubernetes (Istio) to provide a more developer and operator
friendly framework layer.

# Component

## Build

*Date: 12/29/2018, v0.2.0*

The build component provides a framework to run a series of steps to completion and can provide
status. Each step is a container performing some tasks, e.g. build container, push container, or
just send some message. A few notes:
- Build component itself is not a CI/CD pipeline, but it provides a framework that can be used to
  build higher-level concepts.
- Build component is not a general workflow engine like argo: it focuses on creating and runing
  on-cluster processes to completion, and doesn't provide a lot of features like conditions, loops,
  DAGs, etc.
- Build component provides two CRDs: Build and BuildTemplate.

Once running, the build framework contains following sub-component. Not this doesn't include any
init containers or sidecar containers.

```
$ kubectl get pods -n knative-build
NAME                                READY   STATUS    RESTARTS   AGE
build-controller-7b58f7cd8c-4bccd   1/1     Running   0          85m
build-webhook-db9fc4d97-7gsd5       1/1     Running   0          85m
```

Following is a simple example:

```
apiVersion: build.knative.dev/v1alpha1
kind: Build
metadata:
  name: example-build
spec:
  serviceAccountName: build-auth-example
  source:
    git:
      url: https://github.com/example/build-example.git
      revision: master
  steps:
  - name: ubuntu-example
    image: ubuntu
    args: ["ubuntu-build-example", "SECRETS-example.md"]
  steps:
  - image: gcr.io/example-builders/build-example
    args: ['echo', 'hello-example', 'build']
```

*References*

- https://github.com/knative/build
- https://github.com/knative/docs/tree/master/build

## Serving

*Date: 12/29/2018, v0.2.2*

Knative Serving builds on Kubernetes and Istio to support deploying and serving of serverless
applications and functions. The Knative Serving project provides middleware primitives that enable:
- Rapid deployment of serverless containers
- Automatic scaling up and down to zero
- Routing and network programming for Istio components
- Point-in-time snapshots of deployed code and configurations

Knative Serving contains following CRDs:
- Service
- Route
- Configuration
- Revision

Serving component and build component can be used jointly to provide source-to-url, i.e.
- Fetch the revision specified from GitHub and build it into a container
- Push the container to Docker Hub
- Create a new immutable revision for this version of the app.
- Network programming to create a route, ingress, service, and load balance for your app.
- Automatically scale your pods up and down (including to zero active pods).

Once running, the serving framework contains following sub-component. Not this doesn't include any
init containers or sidecar containers.

```
$ kubectl get pods -n knative-serving
NAME                          READY   STATUS    RESTARTS   AGE
activator-5d4b58b86d-8c7cp    2/2     Running   0          150m
activator-5d4b58b86d-rkt8v    2/2     Running   0          150m
activator-5d4b58b86d-xt545    2/2     Running   0          150m
autoscaler-59f694cbfc-rjjpj   2/2     Running   0          150m
controller-c657b6496-n6rxk    1/1     Running   0          150m
webhook-6f9bd9d9d7-clxwg      1/1     Running   0          150m
```

If we install the [example go application](https://github.com/knative/docs/tree/master/serving/samples/helloworld-go),
serving will create a deployment with 1 replica, along with all other resources. To save resources,
if the pods sit idle for around 5min, knative serving will scale the deployment to 0.

```
$ kubectl get all
NAME                                                 READY   STATUS    RESTARTS   AGE
pod/helloworld-go-00001-deployment-bc6588957-rx4sl   3/3     Running   0          37s

NAME                                  TYPE           CLUSTER-IP   EXTERNAL-IP                                             PORT(S)   AGE
service/helloworld-go                 ExternalName   <none>       knative-ingressgateway.istio-system.svc.cluster.local   <none>    32s
service/helloworld-go-00001-service   ClusterIP      10.0.0.77    <none>                                                  80/TCP    37s
service/kubernetes                    ClusterIP      10.0.0.1     <none>                                                  443/TCP   158m

NAME                                             DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/helloworld-go-00001-deployment   1         1         1            1           37s

NAME                                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/helloworld-go-00001-deployment-bc6588957   1         1         1       37s

NAME                                              REFERENCE                TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/istio-pilot   Deployment/istio-pilot   <unknown>/80%   1         5         0          157m

NAME                                                                 READY   REASON
podautoscaler.autoscaling.internal.knative.dev/helloworld-go-00001   True

NAME                                                           AGE
image.caching.internal.knative.dev/helloworld-go-00001-cache   37s

NAME                                                                 READY   REASON
clusteringress.networking.internal.knative.dev/helloworld-go-8fmv8   True

NAME                                        DOMAIN                              LATESTCREATED         LATESTREADY           READY   REASON
service.serving.knative.dev/helloworld-go   helloworld-go.default.example.com   helloworld-go-00001   helloworld-go-00001   True

NAME                                              LATESTCREATED         LATESTREADY           READY   REASON
configuration.serving.knative.dev/helloworld-go   helloworld-go-00001   helloworld-go-00001   True

NAME                                               SERVICE NAME                  READY   REASON
revision.serving.knative.dev/helloworld-go-00001   helloworld-go-00001-service   True

NAME                                      DOMAIN                              READY   REASON
route.serving.knative.dev/helloworld-go   helloworld-go.default.example.com   True
```

The pod contains:
- init containers: istio-init
- sidecar containers: user-container, istio-proxy, queue-proxy (knative/serving/cmd/queue)

*References*

- https://github.com/knative/serving
- https://github.com/knative/docs/tree/master/serving

## Eventing

*Date: 12/29/2018, v0.2.1*

Knative eventing is an eventing system that provides composable primitives to enable late-binding
event sources and event consumers. Eventing component contains following CRDs:
- Channel: defines a single event forwarding and persistence layer
- ClusterChannelProvisioner: defines the provisioner backing a channel, e.g. in-memory, kafka, etc
- KubernetesEventSource, GitHubSource, etc: each source has its own CRD
- Subscription: routes events received on a Channel to subscriber, e.g. Knative Service

Note `ClusterChannelProvisioner` works similar to Kubernetes storage dynamic provisioner or ingress:
a provisioner must be deployed to watch its CRD and act accordingly. Channel implementation ensures
that messages are delivered to the requested destinations and should buffer the events if the
destination Service is unavailable.

Once running, the eventing framework contains following sub-component. Not this doesn't include any
init containers or sidecar containers.

```
# kubectl apply --filename https://github.com/knative/eventing/releases/download/v0.2.1/release.yaml
$ kubectl get all -n knative-eventing
NAME                                                READY   STATUS    RESTARTS   AGE
pod/eventing-controller-7f697d9b9c-9mbvh            1/1     Running   0          48m
pod/in-memory-channel-controller-85bcb5c547-rjlm2   1/1     Running   0          48m
pod/in-memory-channel-dispatcher-5999b49b97-dwlj7   2/2     Running   2          48m
pod/webhook-85b85776f-gf9hv                         1/1     Running   0          48m

NAME                                   TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/in-memory-channel-dispatcher   ClusterIP   10.0.0.159   <none>        80/TCP    48m
service/webhook                        ClusterIP   10.0.0.228   <none>        443/TCP   48m

NAME                                           DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/eventing-controller            1         1         1            1           48m
deployment.apps/in-memory-channel-controller   1         1         1            1           48m
deployment.apps/in-memory-channel-dispatcher   1         1         1            1           48m
deployment.apps/webhook                        1         1         1            1           48m

NAME                                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/eventing-controller-7f697d9b9c            1         1         1       48m
replicaset.apps/in-memory-channel-controller-85bcb5c547   1         1         1       48m
replicaset.apps/in-memory-channel-dispatcher-5999b49b97   1         1         1       48m
replicaset.apps/webhook-85b85776f                         1         1         1       48m

NAME                                                               AGE
clusterchannelprovisioner.eventing.knative.dev/in-memory-channel   48m
```

and eventing sources:

```
# kubectl apply --filename https://github.com/knative/eventing-sources/releases/download/v0.2.1/release.yaml
$ kubectl get all -n knative-sources
NAME                       READY   STATUS    RESTARTS   AGE
pod/controller-manager-0   1/1     Running   0          49m

NAME                                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/controller-manager-service   ClusterIP   10.0.0.9     <none>        443/TCP   49m

NAME                                  DESIRED   CURRENT   AGE
statefulset.apps/controller-manager   1         1         49m

NAME                                                               AGE
clusterchannelprovisioner.eventing.knative.dev/in-memory-channel   50m
```

If we follow the [kubernetes event example](https://github.com/knative/docs/tree/master/eventing/samples/kubernetes-event-source),
we'll have the following data:

```
$ kubectl get all
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/message-dumper-00001-deployment-6766c8d8d8-j2qbt   3/3     Running   0          59m
pod/testevents-8d7vk-cnqv9-655565dc85-tml8z            2/2     Running   0          60m

NAME                                   TYPE           CLUSTER-IP   EXTERNAL-IP                                             PORT(S)   AGE
service/kubernetes                     ClusterIP      10.0.0.1     <none>                                                  443/TCP   25h
service/message-dumper                 ExternalName   <none>       knative-ingressgateway.istio-system.svc.cluster.local   <none>    59m
service/message-dumper-00001-service   ClusterIP      10.0.0.134   <none>                                                  80/TCP    59m
service/testchannel-channel            ClusterIP      10.0.0.65    <none>                                                  80/TCP    62m

NAME                                              DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/message-dumper-00001-deployment   1         1         1            1           59m
deployment.apps/testevents-8d7vk-cnqv9            1         1         1            1           60m

NAME                                                         DESIRED   CURRENT   READY   AGE
replicaset.apps/message-dumper-00001-deployment-6766c8d8d8   1         1         1       59m
replicaset.apps/testevents-8d7vk-cnqv9-655565dc85            1         1         1       60m

NAME                                              REFERENCE                TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/istio-pilot   Deployment/istio-pilot   <unknown>/80%   1         5         0          25h

NAME                                                                  READY   REASON
podautoscaler.autoscaling.internal.knative.dev/message-dumper-00001   True

NAME                                                            AGE
image.caching.internal.knative.dev/message-dumper-00001-cache   59m

NAME                                                               AGE
clusterchannelprovisioner.eventing.knative.dev/in-memory-channel   1h

NAME                                       AGE
channel.eventing.knative.dev/testchannel   1h

NAME                                                        AGE
subscription.eventing.knative.dev/testevents-subscription   59m

NAME                                                                  READY   REASON
clusteringress.networking.internal.knative.dev/message-dumper-7pzts   True

NAME                                               LATESTCREATED          LATESTREADY            READY   REASON
configuration.serving.knative.dev/message-dumper   message-dumper-00001   message-dumper-00001   True

NAME                                                SERVICE NAME                   READY   REASON
revision.serving.knative.dev/message-dumper-00001   message-dumper-00001-service   True

NAME                                       DOMAIN                               READY   REASON
route.serving.knative.dev/message-dumper   message-dumper.default.example.com   True

NAME                                         DOMAIN                               LATESTCREATED          LATESTREADY            READY   REASON
service.serving.knative.dev/message-dumper   message-dumper.default.example.com   message-dumper-00001   message-dumper-00001   True

NAME                                                            AGE
containersource.sources.eventing.knative.dev/testevents-8d7vk   1h

NAME                                                            AGE
kuberneteseventsource.sources.eventing.knative.dev/testevents   1h
```

There is a virtual service not outputed from `get all`:

```
$ kubectl get virtualservices.networking.istio.io
NAME                  AGE
testchannel-channel   1h
```

Below is the configmap used by `in-memory-channel-dispatcher`:

```
$ kubectl get configmap -n knative-eventing in-memory-channel-dispatcher-config-map -o yaml
apiVersion: v1
data:
  multiChannelFanoutConfig: '{"channelConfigs":[{"namespace":"default","name":"testchannel","fanoutConfig":{"subscriptions":[{"ref":{"namespace":"default","name":"testevents-subscription","uid":"58c35289-0bcc-11e9-ba38-2c4d54ed3845"},"subscriberURI":"http://message-dumper.default.svc.cluster.local/"}]}}]}'
kind: ConfigMap
metadata:
  creationTimestamp: 2018-12-30T00:43:30Z
  name: in-memory-channel-dispatcher-config-map
  namespace: knative-eventing
  resourceVersion: "40823"
  selfLink: /api/v1/namespaces/knative-eventing/configmaps/in-memory-channel-dispatcher-config-map
  uid: ed6161de-0bcb-11e9-ba38-2c4d54ed3845
```

Following is short discription of the flow:
- pod `testevents-8d7vk-cnqv9-655565dc85-tml8z` listens to kubernetes events, running "knatve/event-sources/cmd/kuberneteseventsource";
  it is configured to send message to sink `http://testchannel-channel.default.svc.cluster.local/`
- the istio virtualservice points the sink url to `in-memory-channel-dispatcher.knative-eventing.svc.cluster.local`
- the dispatcher runs "knative/eventing/cmd/fanoutsidecar", which sends message to knative service `message-dumper`

For other provisioners, refer to https://github.com/knative/eventing/tree/master/config/provisioners.
Note that for these channels, there are two extra hops, e.g. kubernetes events are first sent to
channel receiver, then to kafka, then from kafka to channel subscriber. The reason is to build a
standard eventing system to hide protocol specific implementation.

*References*

- https://github.com/knative/eventing
- https://github.com/knative/docs/tree/master/eventing
