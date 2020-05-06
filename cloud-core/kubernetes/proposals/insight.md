<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [20181106 - metrics overhaul](#20181106---metrics-overhaul)
  - [20190131 - event series](#20190131---event-series)
  - [20190404 - metrics stability (plus validation & migration)](#20190404---metrics-stability-plus-validation--migration)
  - [20190425 - metrics watch api](#20190425---metrics-watch-api)
- [Feature & Design](#feature--design)
  - [(large) monitoring architecture](#large-monitoring-architecture)
  - [(large) event redesign](#large-event-redesign)
  - [(large) horizontal pod autoscaler v2](#large-horizontal-pod-autoscaler-v2)
  - [(large) vertical pod autoscaler](#large-vertical-pod-autoscaler)
  - [(medium) resource metrics api](#medium-resource-metrics-api)
  - [(medium) custom metrics api](#medium-custom-metrics-api)
  - [(medium) external metrics api](#medium-external-metrics-api)
  - [(medium) metrics server](#medium-metrics-server)
  - [(medium) horizontal pod autoscaler v2 extension API](#medium-horizontal-pod-autoscaler-v2-extension-api)
  - [(small) horizontal pod autoscaler status conditions](#small-horizontal-pod-autoscaler-status-conditions)
  - [(small) volume stats pvc reference](#small-volume-stats-pvc-reference)
  - [(discussion) performance monitoring](#discussion-performance-monitoring)
  - [(deprecated) initial resources](#deprecated-initial-resources)
- [Implementation](#implementation)
  - [how cluster monitoring works](#how-cluster-monitoring-works)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes instrumentation and autoscaling.

- [SIG-Instrumentation KEPs](https://github.com/kubernetes/enhancements/blob/master/keps/sig-instrumentation)
- [SIG-Instrumentation Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/instrumentation)
- [SIG-Instrumentation Community](https://github.com/kubernetes/community/tree/master/sig-instrumentation)
- [SIG-Autoscaling KEPs](https://github.com/kubernetes/enhancements/blob/master/keps/sig-autoscaling)
- [SIG-Autoscaling Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/autoscaling)
- [SIG-Autoscaling Community](https://github.com/kubernetes/community/tree/master/sig-autoscaling)

# KEPs

## 20181106 - metrics overhaul

- *Date: 03/25/2019, v1.14, stable*
- *Date: 12/09/2019, v1.17, deprecated metrics removed*

SIG-instrumentation proposes a "Instrumentation Guidelines" to make Kubernetes metrics instrumentation
more consistent. The KEP aims to fix various parts of the kubernetes/kubernetes repository to conform
to this guideline. Some of the fixes include:
- rename "pod_name" to "pod" to make naming consistent
- switch some kubelet, etcd, etc, metrics from "summary" to "histogram" metrics type for aggregation
  (summary metrics type doesn't support aggregation)
- change unit, e.g. from `sync_proxy_rules_latency_microseconds` to `sync_proxy_rules_latency_seconds`
- etc.

*References*

- [metrics overhaul KEP link](https://github.com/kubernetes/enhancements/blob/f701ae66b466a9c8e6789b7c5135924949617ea7/keps/sig-instrumentation/20181106-kubernetes-metrics-overhaul.md)

## 20190131 - event series

- *Date: 04/04/2020, v1.18, beta*

This is the KEP for the previously event redesign proposal. To graduate event series to beta & stable,
the considerations are:
- there is no

*References*

- [event series KEP link](https://github.com/kubernetes/enhancements/blob/d7306177022e9af921e5f6196b0dd592d01e5c28/keps/sig-instrumentation/20190131-event-series.md)

## 20190404 - metrics stability (plus validation & migration)

- *Date: 09/18/2019, v1.16, stable*

Kubernetes control-plane components, i.e. apiserver, scheduler, controller manager, provide quite a
few prometheus metrics for external usages, those metrics can be queried via `/metrics` endpoint in
respective component server (listening ports can be found at `pkg/master/ports/ports.go`). However,
those metrics are added without API review, and stability is not guaranteed, meaning that metric
name, set of labels, etc, can change without notice, making it hard to build external systems on top
of the metrics.

The KEP proposes a way to mitigate this issue by:
- customizing prometheus client to add two fields to each metric, i.e. `StabilityLevel`, `DeprecatedVersion`
- enforcing a formal review process (and conformance test)

For example, following is an alpha-level metric:

```go
var alphaMetricDefinition = kubemetrics.CounterOpts{
    Name: "some_alpha_metric",
    Help: "some description",
    StabilityLevel: kubemetrics.ALPHA, // this is also a custom metadata field
    DeprecatedVersion: "1.15", // this can optionally be included on alpha metrics, although there is no change to contractual stability guarantees
}

var alphaMetric = kubemetrics.NewCounterVec{
    alphaMetricDefinition, // this is also our custom wrapped metric definition from above
    []string{"some-label", "other-label"},
}

kubemetrics.MustRegister(alphaMetric)
```

The KEP is implementable, with on-going changes in [component-base](https://github.com/kubernetes/component-base/blob/master/metrics/).
Another two KEPs are written,
- one for migrating the metrics to this stability framework
- one for enforcing the stability framework via static code analysis

*References*

- [kubernetes control-plane metrics stability KEP link](https://github.com/kubernetes/enhancements/blob/f701ae66b466a9c8e6789b7c5135924949617ea7/keps/sig-instrumentation/20190404-kubernetes-control-plane-metrics-stability.md)
- [metrics stability migration KEP link](https://github.com/kubernetes/enhancements/blob/f701ae66b466a9c8e6789b7c5135924949617ea7/keps/sig-instrumentation/20190605-metrics-stability-migration.md)
- [metrics validation and verification KEP link](https://github.com/kubernetes/enhancements/blob/f701ae66b466a9c8e6789b7c5135924949617ea7/keps/sig-instrumentation/20190605-metrics-validation-and-verification.md)

## 20190425 - metrics watch api

- *Date: 04/25/2019, v1.14, design*

The KEP proposes adding watch capability to all resource metrics APIs, i.e. `metrics.k8s.io`,
`custom.metrics.k8s.io` and `external.metrics.k8s.io`, similarly to regular Kubernetes APIs. Right
now, external clients have to poll metrics APIs to find latest changes.

*References*

- [metrics watch api KEP link](https://github.com/kubernetes/enhancements/blob/f701ae66b466a9c8e6789b7c5135924949617ea7/keps/sig-instrumentation/20190425-metrics-watch-api.md)

# Feature & Design

## (large) monitoring architecture

- *Date: 01/14/2018*

**Overview**

Since kubernetes 1.6+ (roughly), sig-instrumentation is working on new monitoring architecture to
fix a few problems in kubernetes monitoring. The new architecture aims to remove the maintaining
burden on heapster, and to allow third-party monitoring solutions to seamlessly integrate with
kubernetes.

The proposal splits monitoring architecture into two parts: core monitoring pipeline and monitoring
pipeline:
- A core metrics pipeline consisting of Kubelet, a resource estimator, a slimmed-down Heapster called
  `metrics-server`, and the API server serving the master metrics API. These metrics are used by core
  system components, such as scheduling logic (e.g. scheduler and horizontal pod autoscaling based
  on system metrics) and simple out-of-the-box UI components (e.g. kubectl top). This pipeline is
  not intended for integration with third-party monitoring systems.
- A monitoring pipeline used for collecting various metrics from the system and exposing them to
  end-users, as well as to the Horizontal Pod Autoscaler (for custom metrics) and Infrastore via
  adapters. Users can choose from many monitoring system vendors, or run none at all. In open-source,
  Kubernetes will not ship with a monitoring pipeline, but third-party options will be easy to
  install. We expect that such pipelines will typically consist of a per-node agent and a cluster-level
  aggregator.

For each pipeline, there are two types of metrics to consider: system metrics and service metrics.
- System metrics are generic metrics that are generally available from every entity that is monitored
  (e.g. usage of CPU and memory by container and node). System metrics are further divided into core
  metrics and non-core metrics, where core system metrics are metrics that Kubernetes understands
  and uses for operation of its internal components and core utilities.
- Service metrics are explicitly defined in application code and exported (e.g. number of 500s served
  by the API server). Service metrics used as input to horizontal pod autoscaling are sometimes
  called custom metrics.

**Core Monitoring Pipeline**

The core metrics pipeline collects a set of core system metrics. Core monitoring pipeline consists
of Kubelet, a resource estimator, a slimmed-down Heapster called `metrics-server`, and the API server
serving the master metrics API.
- Kubelet has in-process cAdvisor just as before, but will only provide core metrics in the future.
- Resource estimator runs as a DaemonSet and turns raw usage values scraped from Kubelet into resource
  estimates (values used by scheduler for a more advanced usage-based scheduler).
- Metrics server scrapes the source from kubelet and resource estimator, it is like a slimmed-down
  version of today's Heapster. metrics-server stores locally only latest values and has no sinks.
  metrics-server exposes the master metrics API, i.e. metrics server uses kubernetes style API, and
  uses kubernetes API aggregation feature to expose the APIs.
- Infrastore is a component (likely OSS tools) for serving historical queries over core system
  metrics and events.

**Monitoring Pipeline**

The monitoring pipeline here allows third-party tools to integrate with kubernetes. By default,
kubernetes will not come with such pipeline. To integrate, we need to provide an adaptor to convert
tool specific format (e.g. prometheus query) to Kubernetes API. The monitoring pipeline here is
commonly used for custom metrics.

By publishing core metrics, the kubelet is relieved of its responsibility to provide metrics for
monitoring. The third party monitoring pipeline also is relieved of any responsibility to provide
these metrics to system components.

*References*

- [monitoring architecture design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/instrumentation/monitoring_architecture.md)

## (large) event redesign

- *Data: 10/28/2018*

The goal of the proposal is to:
- reduce performance impact that Events have on the rest of the cluster
- add more structure to the Event object which is first and necessary step to make it possible to automate Event analysis

**Current API**

Current event object consists of:
- InvolvedObject (ObjectRef)
- First/LastSeenTimestamp (1s precision time when Event in a given group was first/last seen)
- Reason (short, machine understandable description of what happened that Event was emitted, e.g. ImageNotFound)
- Message (longer description of what happened, e.g. "failed to start a Pod "
- Source (component that emits event + its host)
- Standard object stuff (ObjectMeta)
- Type (Normal/Warning)

Deduplication logic groups together Event which have the same:
- Source Component and Host
- InvolvedObject Kind, Namespace, Name, API version and UID
- Type (works as Severity)
- Reason

Problem with the API:
- deduplication logic mixes `message`, which makes it hard for user to debug
  - events dedup with same `message` happens after 10 occurance, with message set to "those events were deduped"
  - events with same `message` (thus mostly likely same Source, Type, etc) will be deduped
- it's hard to query event with various conditions, e.g. all events mentioning a specific Pod
- 1s granularity of timestamps is too long since most system components react quicker than 1s
- performance degration since components patch Event object every time when deduplicated Event occurs

**Proposed API**

Two main API changes are made:
- all semantic information about Events are made first-class fields (previously encoded into `message`
  field by client), including Action, Regarding, ReportingController, etc
- a new `EventSeries` struct is added for better deduplication

The new API is created under `events` API group, the full API is:

```go
type Event struct {
	// <type and object metadata>

	// Time when this Event was first observed.
	EventTime metav1.MicroTime

	// Data about the Event series this event represents or nil if it's
	// a singleton Event.
	// +optional
	Series *EventSeries

	// Name of the controller that emitted this Event, e.g. `kubernetes.io/kubelet`.
	ReportingController string

	// ID of the controller instance, e.g. `kubelet-xyzf`.
	ReportingInstance string

	// What action was taken or what failed regarding the Regarding object.
	Action string

	// Why the action was taken or why the operation failed.
	Reason string

	// The object this Event is “about”. In most cases it's the object that the
	// given controller implements.
	// +optional
	Regarding ObjectReference

	// Optional secondary object for more complex actions.
	// +optional
	Related *ObjectReference

	// Human readable description of the Event. Possibly discarded when and
	// Event series is being deduplicated.
	// +optional
	Note string

	// Type of this event (Normal, Warning), new types could be added in the
	// future.
	// +optional
	Type string
}

type EventSeries struct {
	Count int32
	LastObservedTime MicroTime
	State EventSeriesState
}

const (
	EventSeriesStateOngoing  = "Ongoing"
	EventSeriesStateFinished = "Finished"
	EventSeriesStateUnknown  = "Unknown"
)
```

Behavior change: instead of patching Event everytime event occurs, now we'll only update EventSeries
every 30min. For example, when a crashloop happens, one event will be emitted with nil EventSeries.
Later a second event will be emitted and EventSeries will be updated with count=2 and stage=Ongoing.
For the next ~30min, no API call will be made to API server, but EventRecorder library will keep
increasing its in-memory count. After 30min, EventRecorder will send a request to API server with
aggregated count (e.g. count=2121), and stage=Ongoing. EventRecorder will check events emission every
6min, if there weren't any events it assumes that series is finished and emits closing Event call
with stage=Finished.

For more information, see the design doc.
- design considerations: what's the performance impact of the new API (e.g. event object is bigger)
- backward compatibility: use internal, core group and eveng group with conversion
- alternative considered

The API is checked in, but looks like there is no futhur plan.

*References*

- [event redesign design doc](https://github.com/kubernetes/community/blob/38d96e9eaa25da80b6757e6b5b9212259865245f/contributors/design-proposals/instrumentation/events-redesign.md)
- [event compression design doc](https://github.com/kubernetes/community/blob/d09814f618cfeae6f3a19744520fc13773409c92/contributors/design-proposals/api-machinery/event_compression.md)
- [redesign event enhancement issue](https://github.com/kubernetes/enhancements/issues/383)

## (large) horizontal pod autoscaler v2

- *Data: 01/14/2018*
- *Data: 04/04/2020, v1.18, beta*

Before kubernetes 1.6, Kubernetes only supports scaling pods based on CPU utilization. Support for
other metrics can be accomplished using annotations. Since then, new APIs have been proposed to
support scaling based on more resource metrics (e.g. memory), custom metrics (e.g. connections, 500
errors, etc.) and multiple metrics (scale based on cpu and connections together).

The HPA will derive metrics from two sources: resource metrics (i.e. CPU request percentage) will
come from the master metrics API, while other metrics will come from the custom metrics API, which
is an adapter API which sources metrics directly from the monitoring pipeline.

At the API level, HPA has four different types of metrics:
- ObjectMetricSource: metrics for a kubernetes object, e.g. hits-per-second on an Ingress object
- PodsMetricSource: metrics for pod, e.g. transactions-processed-per-second
- ResourceMetricSource: resource metrics such as cpu, memory
- ExternalMetricSource: external metrics such as QPS from loadbalancer running outside of cluster

```yaml
apiVersion: autoscaling/v2beta1
kind: HorizontalPodAutoscaler
metadata:
  name: php-apache
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-apache
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        kind: AverageUtilization
        averageUtilization: 50
  - type: Pods
    pods:
      metric:
        name: packets-per-second
      targetAverageValue: 1k
  - type: Object
    object:
      metric:
        name: requests-per-second
      describedObject:
        apiVersion: extensions/v1beta1
        kind: Ingress
        name: main-route
      target:
        kind: Value
        value: 10k
```

*References*

- [horizontal pod autoscaler v1 design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/autoscaling/horizontal-pod-autoscaler.md)
- [horizontal pod autoscaler v2 design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/autoscaling/hpa-v2.md)
- https://github.com/kubernetes/enhancements/issues/117
- https://blog.jetstack.io/blog/resource-and-custom-metrics-hpa-v2/
- https://github.com/stefanprodan/k8s-prom-hpa/tree/617a98c5d921c3413599bbbb1438dfb125e3bd21

## (large) vertical pod autoscaler

- *Date: 09/27/2018, v1.12, beta*
- *Date: 04/04/2020, v1.18, beta*

TODO

*References*

- [vertical pod autoscaler design doc](https://github.com/kubernetes/community/blob/a4a1d2f561eac609403f0db7d31d764daaea3b00/contributors/design-proposals/autoscaling/vertical-pod-autoscaler.md)
- https://github.com/kubernetes/autoscaler

## (medium) resource metrics api

- *Date: 01/14/2018*

Resource Metrics API is part of new monitoring architecture above. At its core, it is a new API group
`metrics` (can be multiple groups in the future), providing a set of APIs for accessing resource
metrics like cpu usage, memory usage, etc. This is to solve the problem where previously, no standard
representation of metric exists in Kubernetes. The resource metrics APIs are usually core metrics:

```go
type NodeMetrics struct {
  unversioned.TypeMeta
  ObjectMeta

  // The following fields define time interval from which metrics were
  // collected in the following format [Timestamp-Window, Timestamp].
  Timestamp unversioned.Time
  Window    unversioned.Duration

  // The memory usage is the memory working set.
  Usage v1.ResourceList
}

type PodMetrics struct {
  unversioned.TypeMeta
  ObjectMeta

  // The following fields define time interval from which metrics were
  // collected in the following format [Timestamp-Window, Timestamp].
  Timestamp unversioned.Time
  Window    unversioned.Duration

  // Metrics for all containers are collected within the same time window.
  Containers []ContainerMetrics
}

type ContainerMetrics struct {
  // Container name corresponding to the one from v1.Pod.Spec.Containers.
  Name string
  // The memory usage is the memory working set.
  Usage v1.ResourceList
}
```

And endpoints:

```
/apis/metrics/v1alpha1/nodes - all node metrics; type []NodeMetrics
/apis/metrics/v1alpha1/nodes/{node} - metrics for a specified node; type NodeMetrics
/apis/metrics/v1alpha1/namespaces/{namespace}/pods - all pod metrics within namespace with support for all-namespaces; type []PodMetrics
/apis/metrics/v1alpha1/namespaces/{namespace}/pods/{pod} - metrics for a specified pod; type PodMetrics
```

For example, following is the pod running metrics server. `172.17.0.4` is the pod IP.

```
$ curl -k https://172.17.0.4/
{
  "paths": [
    "/apis",
    "/apis/metrics.k8s.io",
    "/apis/metrics.k8s.io/v1beta1",
    "/healthz",
    "/healthz/healthz",
    "/healthz/ping",
    "/healthz/poststarthook/generic-apiserver-start-informers",
    "/swaggerapi"
  ]
}

$ curl -k https://172.17.0.4/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-dns-86f6f55dd5-bbjvt
{
  "kind": "PodMetrics",
  "apiVersion": "metrics.k8s.io/v1beta1",
  "metadata": {
    "name": "kube-dns-86f6f55dd5-bbjvt",
    "namespace": "kube-system",
    "selfLink": "/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-dns-86f6f55dd5-bbjvt",
    "creationTimestamp": "2018-01-14T04:49:39Z"
  },
  "timestamp": "2018-01-14T04:49:00Z",
  "window": "1m0s",
  "containers": [
    {
      "name": "kubedns",
      "usage": {
        "cpu": "0",
        "memory": "8364Ki"
      }
    },
    {
      "name": "dnsmasq",
      "usage": {
        "cpu": "0",
        "memory": "6664Ki"
      }
    },
    {
      "name": "sidecar",
      "usage": {
        "cpu": "0",
        "memory": "11336Ki"
      }
    }
  ]
}
```

It's also possible to query Kubernetes API server, provided we've registered the API endpoints as a
service (the default behavior from metrics-server):

```
$ kubectl get apiservices
NAME                                   SERVICE                      AVAILABLE   AGE
...
v1.storage.k8s.io                      Local                        True        30h
v1beta1.metrics.k8s.io                 kube-system/metrics-server   True        29m
v1beta1.networking.k8s.io              Local                        True        30h
...

$ curl -k https://localhost:8443/apis/metrics.k8s.io/v1beta1/namespaces/kube-system/pods/kube-dns-86f6f55dd5-bbjvt
...
```

Note the APIs are defined in [metrics](https://github.com/kubernetes/metrics) repository, along with
other types of metrics (e.g. custom metrics). The target use case of the resource metrics API are:
- Horizontal Pod Autoscaler
- Scheduler (usage based scheduling in the future)
- kubectl top
- Kubernetes dashboard
- etc

*References*

- [resource metrics API design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/instrumentation/resource-metrics-api.md)
- [core metrics design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/instrumentation/core-metrics-pipeline.md)
- [metrics API definition repository](https://github.com/kubernetes/metrics)

## (medium) custom metrics api

- *Date: 01/14/2018*

Similar to resource metrics API above, custom metrics API proposes a set of APIs for accessing user
defined metrics in a standard way. The new API is created under `custom-metrics` group:

```go
// a metric value for some object
type MetricValue struct {
	metav1.TypeMeta `json:",inline"`

	// a reference to the described object
	DescribedObject ObjectReference `json:"describedObject"`

	// the name of the metric
	MetricName string `json:"metricName"`

	// indicates the time at which the metrics were produced
	Timestamp metav1.Time `json:"timestamp"`

	// indicates the window ([Timestamp-Window, Timestamp]) from
	// which these metrics were calculated, when returning rate
	// metrics calculated from cumulative metrics (or zero for
	// non-calculated instantaneous metrics).
	WindowSeconds *int64 `json:"window,omitempty"`

	// the value of the metric for this
	Value resource.Quantity `json:"value"`
}
```

And endpoints:

```
/apis/custom-metrics/v1alpha1/{object-type}/{object-name}/{metric-name...}: retrieve the given metric for the given non-namespaced object (e.g. Node, PersistentVolume)
/apis/custom-metrics/v1alpha1/{object-type}/*/{metric-name...}: retrieve the given metric for all non-namespaced objects of the given type
/apis/custom-metrics/v1alpha1/{object-type}/*/{metric-name...}?labelSelector=foo: retrieve the given metric for all non-namespaced objects of the given type matching the given label selector
/apis/custom-metrics/v1alpha1/namespaces/{namespace-name}/{object-type}/{object-name}/{metric-name...}: retrieve the given metric for the given namespaced object
/apis/custom-metrics/v1alpha1/namespaces/{namespace-name}/{object-type}/*/{metric-name...}: retrieve the given metric for all namespaced objects of the given type
/apis/custom-metrics/v1alpha1/namespaces/{namespace-name}/{object-type}/*/{metric-name...}?labelSelector=foo: retrieve the given metric for all namespaced objects of the given type matching the given label selector
/apis/custom-metrics/v1alpha1/namespaces/{namespace-name}/metrics/{metric-name}: retrieve the given metric which describes the given namespace.
```

For example:

```
GET /apis/custom-metrics/v1alpha1/namespaces/webapp/ingress.extensions/*/hits-per-second?labelSelector=app%3Dfrontend`

{
    "kind": "MetricValueList",
    "apiVersion": "custom-metrics/v1alpha1",
    "items": [
        {
            "metricName": "hits-per-second",
            "describedObject": {
                "kind": "Ingress",
                "apiVersion": "extensions",
                "name": "server1",
                "namespace": "webapp"
            },
            "timestamp": SOME_TIMESTAMP_HERE,
            "windowSeconds": "10",
            "value": "10"
        },
        {
            "metricName": "hits-per-second",
            "describedObject": {
                "kind": "Ingress",
                "apiVersion": "extensions",
                "name": "server2",
                "namespace": "webapp"
            },
            "timestamp": ANOTHER_TIMESTAMP_HERE,
            "windowSeconds": "10",
            "value": "15"
        }
    ]
}
```

Pay attention to two points here, which are not part of Kubernetes API convetion:
- The proposal uses `*` to represent subresource (i.e. metrics) of all object types
- For metrics related to namespace object itself, the propsosal uses `metrics` in the path

Note the APIs are defined in [metrics](https://github.com/kubernetes/metrics) repository as well, and
a [framework](https://github.com/kubernetes-incubator/custom-metrics-apiserver) exists to facilitate
implementing custom metrics API server. As mentioned above, custom metrics is commonly used in monitoring
pipeline, for example, [k8s-prometheus-adapter](https://github.com/directXMan12/k8s-prometheus-adapter)
is an implementation of the `custom-metrics.metrics.k8s.io` API using Prometheus.

*References*

- [custom metrics API design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/instrumentation/custom-metrics-api.md)
- [metrics API definition repository](https://github.com/kubernetes/metrics)
- [custom metrics apiserver framework repository](https://github.com/kubernetes-incubator/custom-metrics-apiserver)
- https://brancz.com/2018/01/05/prometheus-vs-heapster-vs-kubernetes-metrics-apis/
- https://github.com/directXMan12/k8s-prometheus-adapter

## (medium) external metrics api

- *Date: 10/29/2018*

External metrics API is very similar to custom metrics, except that metrics are not coming from
Kubernetes cluster, but some other out-of-cluster system. Target consumer is HPA.

Below is the proposed API:

```go
// a list of values for a given metric for some set labels
type ExternalMetricValueList struct {
       metav1.TypeMeta `json:",inline"`
       metav1.ListMeta `json:"metadata,omitempty"`

       // value of the metric matching a given set of labels
       Items []ExternalMetricValue `json:"items"`
}

// a metric value for external metric
type ExternalMetricValue struct {
    metav1.TypeMeta`json:",inline"`

    // the name of the metric
    MetricName string `json:"metricName"`

    // label set identifying the value within metric
    MetricLabels map[string]string `json:"metricLabels"`

    // indicates the time at which the metrics were produced
    Timestamp unversioned.Time `json:"timestamp"`

    // indicates the window ([Timestamp-Window, Timestamp]) from
    // which these metrics were calculated, when returning rate
    // metrics calculated from cumulative metrics (or zero for
    // non-calculated instantaneous metrics).
    WindowSeconds *int64 `json:"window,omitempty"`

    // the value of the metric
    Value resource.Quantity
}
```

And endpoints:

```
/apis/external.metrics.k8s.io/v1beta1/namespaces/<namespace_name>/<metric_name>?labelSelector=<selector>
```

All design decisions apply to external metrics API, with a few differences:
- it's up to adapters to decide namespace since external systems do not necessarily have namespace
- many external systems use `/` in their name but this is not allowed in Kubernetes (as metrics name),
  the proposal proposes `\|` as escape sequence
- access control can be performed using normal Kubernetes policies, but for external metrics, we can
  also add a new ExternalMetricsPolicy API object to control how external metrics are access controlled

*References*

- [external metrics API design doc](https://github.com/kubernetes/community/blob/59ad9e15d9290e34a3b02a5a88fb447dbbc7e18c/contributors/design-proposals/instrumentation/external-metrics-api.md)

## (medium) metrics server

- *Date: 01/14/2018*

[Metrics server](https://github.com/kubernetes-incubator/metrics-server) is an implementation of the
resource metrics API. It is a dependency for quite a few components in Kubernetes, thus marked as a
critical addon. Metrics server will replace Heapster in the future.

A few points:
- default metrics scrape duration is 1min
- all metrics will be stored in memory
- metrics server uses api aggregator in order to minic Kubernetes native API
- based on experience with Heapster, metrics server will be scaled vertically (horizontal scale is out of scope)

*References*

- [metrics server design doc](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/instrumentation/metrics-server.md)
- [metrics server repository](https://github.com/kubernetes-incubator/metrics-server)

## (medium) horizontal pod autoscaler v2 extension API

- *Date: 11/19/2018*

The goal of the proposal is to:
- allow autoscaling based on external metrics
- allow autoscaling based on per-pod target (instead of global target)

An external metrics source is added for the first goal. For the second goal, in addition to
`TargetValue`, Kubernetes added another field `TargetAverageValue`.

For example, following HorizontalPodAutoscaler autoscales ReplicationController based on external
metric `queue_messages_ready`, which is averaged over all pods:

```yaml
kind: HorizontalPodAutoscaler
apiVersion: autoscaling/v2beta2
spec:
  scaleTargetRef:
    kind: ReplicationController
    name: Worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
   - type: External
     external:
       metricName: queue_messages_ready
       metricSelector:
         matchLabels:
           queue: worker_tasks
       targetAverageValue: 30
```

HorizontalPodAutoscaler will query the following endpoint for metrics. The label selector implementation
depends on backend used. For example, in prometheus, time series is identified by both metrics name
(e.g. `http_requests`) and label (e.g. `GET`).

```
/apis/external.metrics.k8s.io/v1beta1/queue_messages_ready?labelSelector=queue=worker_tasks
```

*References*

- [hpa v2 extension design doc](https://github.com/kubernetes/community/blob/c4e87a2524c331f338912595daa50406bc9973c9/contributors/design-proposals/autoscaling/hpa-external-metrics.md)

## (small) horizontal pod autoscaler status conditions

- *Date: 09/15/2017*

The proposal proposes to add a new `Conditions` to HPA object, similar to Pod, Node, etc.

> Currently, the HPA status conveys the last scale time, current and desired replicas, and the
> last-retrieved values of the metrics used to autoscale.
>
> However, the status field conveys no information about whether or not the HPA controller encountered
> difficulties while attempting to fetch metrics, or to scale. While this information is generally
> conveyed via events, events are difficult to use to determine the current state of the HPA.

*Reference*

- [hpa status conditions design doc](https://github.com/kubernetes/community/blob/a4a1d2f561eac609403f0db7d31d764daaea3b00/contributors/design-proposals/autoscaling/hpa-status-conditions.md)

## (small) volume stats pvc reference

- *Date: 09/15/2017*

The proposal exposes volume stats with references to PVC, if any.

```
// VolumeStats contains data about Volume filesystem usage.
type VolumeStats struct {
	// Embedded FsStats
	FsStats
	// Name is the name given to the Volume
	// +optional
	Name string `json:"name,omitempty"`
+	// PVCRef is a reference to the measured PVC.
+	// +optional
+	PVCRef PVCReference `json:"pvcRef"`
}

+// PVCReference contains enough information to describe the referenced PVC.
+type PVCReference struct {
+	Name      string `json:"name"`
+	Namespace string `json:"namespace"`
+}
```

*References*

- [volume stats pvc ref design doc](https://github.com/kubernetes/community/blob/a4a1d2f561eac609403f0db7d31d764daaea3b00/contributors/design-proposals/instrumentation/volume_stats_pvc_ref.md)

## (discussion) performance monitoring

- *Data: 01/14/2018*

The doc aims to provide a place to gather information about past performance regression. It proposes:
- cluster-level metrics: like number of pods, number of master restart
- logging monitoring: monitoring log spam using log ratation rate
- REST call monitoring: like number of calls per verb, etc
- rate limit monitoring: number of inflight requests in API server
- network connection monitoring
- etcd monitoring
- resource consumption: cpu usage
- other saturation metrics

*References*

- [performance related monitoring](https://github.com/kubernetes/community/blob/5c72116259a131b03f4c6b5e6a7c5ffa289e556f/contributors/design-proposals/instrumentation/performance-related-monitoring.md)

## (deprecated) initial resources

- *Date: 09/07/2017*
- *Date: 04/04/2020, v1.18, deprecated*

It's usually hard for users to set Pod resource requirement at beginning, while having the
information is critial for scheduling decisions. The proposal aims to solve the problem.

> Initial Resources is a data-driven feature that based on historical data tries to estimate
> resource usage of a container without Resources specified and set them before the container
> is run.

Following is a list of key design points:
- The primary component of initial resource is an admission controller, invoked before LimitRanger.
- To avoid being killed by kubelet, initial resources will only set request (not limit).
- Prediction is based on docker image being run in the container (both the name and the tag matters).
- InitialResources will set Request for both cpu/mem as the 90th percentile, in the following order:
  - 7 days same image:tag, assuming there is at least 60 samples (1 hour)
  - 30 days same image:tag, assuming there is at least 60 samples (1 hour)
  - 30 days same image, assuming there is at least 1 sample

The initial resource feature is deprecated and superceded by vertical pod autoscaler.

*References*

- [initial resource design doc](https://github.com/kubernetes/community/blob/a4a1d2f561eac609403f0db7d31d764daaea3b00/contributors/design-proposals/autoscaling/initial-resources.md)

# Implementation

## how cluster monitoring works

- *Date: 02/19/2015*

Cluster monitoring is a cluster addon. During cluster bootstrap, a script named `master-start.sh`
is dynamically created (heredoc) that has the configuration installed (whether cluster monitoring
is enabled or not). After the startup scripts are pushed to master/minions, salt will exec
`kubectl create -f` to create cluster monitoring module, see `cluster/saltbase/salt/kube-addons`.

cAdvisor monitors and collects data of all containers on a specific node, as well as the node itself.
Heapster runs in a pod, it periodically collects data from kubelet, write to influxDB, and display
the stats in grafana. In summary, current OOS monitoring setup is Heapster + InfluxDB + Grafana.

Note that the core of GCM (google cloud monitoring) is actually equivalent to InfuxDB+Grafana: it
provides the backend to store data as well as visulization. In GCM world, Heapster is like a plugin.
E.g. a MongoDB plugin in GCM will monitor MongoDB status, such as number of connections, documents
request, etc, and write the metrics to GCM backendend. Heapster does the same thing, like a
Kubernetes plugin for GCM.
