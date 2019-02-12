<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Components](#components)
  - [Authentication](#authentication)
- [Experiments](#experiments)
  - [Installation](#installation)
  - [Run MQ and Consumer](#run-mq-and-consumer)
  - [Run MQ Publisher](#run-mq-publisher)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 06/02/2020, v1.4*

[KEDA](https://keda.sh/) is a Kubernetes-based Event Driven Autoscaler: it scales Kubernetes
deployments based on custom event sources. KEDA works alongside standard Kubernetes components like
the Horizontal Pod Autoscaler and can extend functionality without overwriting or duplication.

## Components

KEDA performs two key roles within Kubernetes:
- Agent (keda-operator) — KEDA activates and deactivates Kubernetes Deployments to scale to and from
  zero on no events. This is one of the primary roles of the keda-operator container that runs when
  you install KEDA.
- Metrics (keda-opertor-metrics-apiserver, or adaptor) — KEDA acts as a Kubernetes metrics server
  that exposes rich event data like queue length or stream lag to the Horizontal Pod Autoscaler to
  drive scale out. It is up to the Deployment to consume the events directly from the source. This
  preserves rich event integration and enables gestures like completing or abandoning queue messages
  to work out of the box. The metric serving is the primary role of the keda-operator-metrics-apiserver
  container that runs when you install KEDA.

## Authentication

Often a scaler will require authentication or secrets and config to check for events. KEDA provides
a few secure patterns to manage authentication flows:
- Configure authentication per `ScaledObject`
- Re-use credentials or delegate authentication with `TriggerAuthentication`

Using `ScaledObject` is the most straightforward way: set the secret name in the `ScaledObject` used
to connect to event source. The downside is:
- hard to share authentication information across multiple `ScaledObject`
- no support for referencing a secret directly, only secrets that are referenced by the container
- no support for other types of authentication flow, like "Pod Identity" where secrets are acquired
  from external provider like AWS IAM

# Experiments

## Installation

Deploying KEDA will create:
- two components: an agent and a metrics server
- two crds: scaledobjects and triggerauthentications
- one apiservice: the custom metrics apiserver registration

```
$ helm install keda kedacore/keda --namespace keda
...

$ kubectl get pods -n keda
NAME                                               READY   STATUS    RESTARTS   AGE
keda-operator-5895ff46b9-2j9sc                     1/1     Running   0          7m54s
keda-operator-metrics-apiserver-6774776dbc-ldhgg   1/1     Running   0          7m54s

$ kubectl get crds
NAME                                 CREATED AT
scaledobjects.keda.k8s.io            2020-06-02T13:04:08Z
triggerauthentications.keda.k8s.io   2020-06-02T13:04:08Z

$ kubectl get apiservices | grep -v Local
NAME                                   SERVICE                                AVAILABLE   AGE
v1beta1.external.metrics.k8s.io        keda/keda-operator-metrics-apiserver   True        8m10s
```

The external metrics is backed by `keda-operator-metrics-apiserver`:

<details><summary>API Service</summary><p>

```
$ kubectl get apiservices v1beta1.external.metrics.k8s.io -o yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  annotations:
    meta.helm.sh/release-name: keda
    meta.helm.sh/release-namespace: keda
  creationTimestamp: "2020-06-02T13:04:13Z"
  labels:
    app.kubernetes.io/instance: keda
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: v1beta1.external.metrics.k8s.io
    app.kubernetes.io/part-of: keda-operator
    app.kubernetes.io/version: 1.4.1
  name: v1beta1.external.metrics.k8s.io
  resourceVersion: "437"
  selfLink: /apis/apiregistration.k8s.io/v1/apiservices/v1beta1.external.metrics.k8s.io
  uid: 516d4b53-c2d1-41e6-899d-fd3c6bd8b43d
spec:
  group: external.metrics.k8s.io
  groupPriorityMinimum: 100
  insecureSkipTLSVerify: true
  service:
    name: keda-operator-metrics-apiserver
    namespace: keda
    port: 443
  version: v1beta1
  versionPriority: 100
status:
  conditions:
  - lastTransitionTime: "2020-06-02T13:04:27Z"
    message: all checks passed
    reason: Passed
    status: "True"
    type: Available
```

</p></details></br>

## Run MQ and Consumer

Run a RabbitMQ container for eventing:

```
$ helm install rabbitmq --set rabbitmq.username=user,rabbitmq.password=PASSWORD stable/rabbitmq
...

$ kubectl get sts
NAME       READY   AGE
rabbitmq   1/1     118s
```

Run a client consumer which will receive one message from RabbitMQ at a time and then sleep for 1s.
In addition, a `scaledobject` CR will be created to autoscale the client consumer:

```
$ kubectl apply -f experiments/deploy-consumer.yaml
secret/rabbitmq-consumer created
deployment.apps/rabbitmq-consumer created
scaledobject.keda.k8s.io/rabbitmq-consumer created
```

As soon as the consumer is created, it will be scaled to zero since there is no message in RabbitMQ.
Also, an HPA is created for the consumer by KEDA agent (keda-operator):

```
$ kubectl get pods
NAMESPACE     NAME                                               READY   STATUS        RESTARTS   AGE
default       rabbitmq-0                                         1/1     Running       0          50m
default       rabbitmq-consumer-655c58fcfb-cfmnc                 0/1     Terminating   0          3s

$ kubectl get events
LAST SEEN   TYPE      REASON                  OBJECT                                    MESSAGE
...
78s         Normal    SuccessfulCreate        replicaset/rabbitmq-consumer-655c58fcfb   Created pod: rabbitmq-consumer-655c58fcfb-cfmnc
78s         Normal    SuccessfulDelete        replicaset/rabbitmq-consumer-655c58fcfb   Deleted pod: rabbitmq-consumer-655c58fcfb-cfmnc
78s         Normal    ScalingReplicaSet       deployment/rabbitmq-consumer              Scaled up replica set rabbitmq-consumer-655c58fcfb to 1
78s         Normal    ScalingReplicaSet       deployment/rabbitmq-consumer              Scaled down replica set rabbitmq-consumer-655c58fcfb to 0
...

$ kubectl get hpa
NAME                         REFERENCE                      TARGETS             MINPODS   MAXPODS   REPLICAS   AGE
keda-hpa-rabbitmq-consumer   Deployment/rabbitmq-consumer   <unknown>/5 (avg)   1         30        0          86s
```

Based on the information from HPA and keda-operator, it's obvious to see that it's the keda-operator
that sets the number of replicas to zero for the consumer:

```
$ kubectl describe hpa keda-hpa-rabbitmq-consumer
Name:                                    keda-hpa-rabbitmq-consumer
...
Deployment pods:                         0 current / 0 desired
Conditions:
  Type           Status  Reason             Message
  ----           ------  ------             -------
  AbleToScale    True    SucceededGetScale  the HPA controller was able to get the target's current scale
  ScalingActive  False   ScalingDisabled    scaling is disabled since the replica count of the target is zero
Events:          <none>


$ kubectl logs -n keda keda-operator-5895ff46b9-2j9sc
{"level":"info","ts":1591107158.6683712,"logger":"controller_scaledobject","msg":"Reconciling ScaledObject","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107158.6684446,"logger":"controller_scaledobject","msg":"Adding Finalizer for the ScaledObject","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107158.6850407,"logger":"controller_scaledobject","msg":"Detected ScaleType = Deployment","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107158.6850953,"logger":"controller_scaledobject","msg":"Creating a new HPA","Request.Namespace":"default","Request.Name":"rabbitmq-consumer","HPA.Namespace":"default","HPA.Name":"keda-hpa-rabbitmq-consumer"}
{"level":"info","ts":1591107158.9408524,"logger":"scalehandler","msg":"Successfully scaled deployment to 0 replicas","ScaledObject.Namespace":"default","ScaledObject.Name":"rabbitmq-consumer","ScaledObject.ScaleType":"deployment","Deployment.Namespace":"default","Deployment.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107158.9448137,"logger":"controller_scaledobject","msg":"Reconciling ScaledObject","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107158.9448369,"logger":"controller_scaledobject","msg":"Detected ScaleType = Deployment","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107174.328443,"logger":"controller_scaledobject","msg":"Reconciling ScaledObject","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107174.3285174,"logger":"controller_scaledobject","msg":"Detected ScaleType = Deployment","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
```

## Run MQ Publisher

Now run the publisher, which will send 300 messages to RabbitMQ:

```
$ kubectl apply -f experiments/deploy-publisher-job.yaml
```

After a while, the HPA will scale the consumer deployment to 30 pods:

```
$ kubectl describe hpa keda-hpa-rabbitmq-consumer
Name:                                    keda-hpa-rabbitmq-consumer
Namespace:                               default
Labels:                                  app.kubernetes.io/managed-by=keda-operator
                                         app.kubernetes.io/name=keda-hpa-rabbitmq-consumer
                                         app.kubernetes.io/part-of=rabbitmq-consumer
                                         app.kubernetes.io/version=1.4.1
Annotations:                             <none>
CreationTimestamp:                       Tue, 02 Jun 2020 22:12:38 +0800
Reference:                               Deployment/rabbitmq-consumer
Metrics:                                 ( current / target )
  "queueLength" (target average value):  <unknown> / 5
Min replicas:                            1
Max replicas:                            30
Deployment pods:                         0 current / 0 desired
Conditions:
  Type            Status  Reason             Message
  ----            ------  ------             -------
  AbleToScale     True    SucceededGetScale  the HPA controller was able to get the target's current scale
  ScalingActive   False   ScalingDisabled    scaling is disabled since the replica count of the target is zero
  ScalingLimited  True    TooManyReplicas    the desired replica count is more than the maximum replica count
Events:
  Type    Reason             Age    From                       Message
  ----    ------             ----   ----                       -------
  Normal  SuccessfulRescale  2m16s  horizontal-pod-autoscaler  New size: 4; reason: external metric queueLength(&LabelSelector{MatchLabels:map[string]string{deploymentName: rabbitmq-consumer,},MatchExpressions:[]LabelSelectorRequirement{},}) above target
  Normal  SuccessfulRescale  2m2s   horizontal-pod-autoscaler  New size: 8; reason: external metric queueLength(&LabelSelector{MatchLabels:map[string]string{deploymentName: rabbitmq-consumer,},MatchExpressions:[]LabelSelectorRequirement{},}) above target
  Normal  SuccessfulRescale  106s   horizontal-pod-autoscaler  New size: 16; reason: external metric queueLength(&LabelSelector{MatchLabels:map[string]string{deploymentName: rabbitmq-consumer,},MatchExpressions:[]LabelSelectorRequirement{},}) above target
  Normal  SuccessfulRescale  92s    horizontal-pod-autoscaler  New size: 30; reason: external metric queueLength(&LabelSelector{MatchLabels:map[string]string{deploymentName: rabbitmq-consumer,},MatchExpressions:[]LabelSelectorRequirement{},}) above target
```

We can manually query the queue length externel metrics via API Server:

```
$ curl localhost:8080/apis/external.metrics.k8s.io/v1beta1/namespaces/default/queueLength
{
  "kind": "ExternalMetricValueList",
  "apiVersion": "external.metrics.k8s.io/v1beta1",
  "metadata": {
    "selfLink": "/apis/external.metrics.k8s.io/v1beta1/namespaces/default/queueLength"
  },
  "items": [
    {
      "metricName": "queueLength",
      "metricLabels": null,
      "timestamp": "2020-06-02T14:34:33Z",
      "value": "294"
    }
  ]
}%
```

During the above process, we can see from the log of keda-operator that:
- it scales the replica from 0 to 1 in reaction of the new message load
- it won't scale the replica anymore: scaling from 1 to many is done by HPA
- it scales the replica to 0 when load is gone

This proves that KEDA scales for 0->1 and 1->0, and will let HPA scale for 1->n and n->1.

```
$ kubectl logs -n keda keda-operator-5895ff46b9-2j9sc -f
...
{"level":"info","ts":1591107870.713445,"logger":"scalehandler","msg":"Successfully updated deployment","ScaledObject.Namespace":"default","ScaledObject.Name":"rabbitmq-consumer","ScaledObject.ScaleType":"deployment","Deployment.Namespace":"default","Deployment.Name":"rabbitmq-consumer","Original Replicas Count":0,"New Replicas Count":1}
{"level":"info","ts":1591107872.251296,"logger":"controller_scaledobject","msg":"Reconciling ScaledObject","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107872.251322,"logger":"controller_scaledobject","msg":"Detected ScaleType = Deployment","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107886.925802,"logger":"controller_scaledobject","msg":"Reconciling ScaledObject","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
{"level":"info","ts":1591107886.9258764,"logger":"controller_scaledobject","msg":"Detected ScaleType = Deployment","Request.Namespace":"default","Request.Name":"rabbitmq-consumer"}
...
...
{"level":"info","ts":1591107976.1182473,"logger":"scalehandler","msg":"Successfully scaled deployment to 0 replicas","ScaledObject.Namespace":"default","ScaledObject.Name":"rabbitmq-consumer","ScaledObject.ScaleType":"deployment","Deployment.Namespace":"default","Deployment.Name":"rabbitmq-consumer"}
```
