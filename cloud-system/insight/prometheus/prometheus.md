<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Concepts](#concepts)
  - [Metric Types](#metric-types)
- [Components](#components)
  - [Prometheus Server](#prometheus-server)
  - [PushGateway](#pushgateway)
  - [Exporter](#exporter)
- [Kubernetes Monitoring with Prometheus](#kubernetes-monitoring-with-prometheus)
  - [Methodology](#methodology)
  - [Node CPU Metrics](#node-cpu-metrics)
  - [Node Memory Metrics](#node-memory-metrics)
  - [Node Disk Metrics](#node-disk-metrics)
  - [Node Network Metrics](#node-network-metrics)
  - [Container CPU Metrics](#container-cpu-metrics)
  - [Container Memory Metrics](#container-memory-metrics)
  - [Container Disk Metrics](#container-disk-metrics)
  - [Container Network Metrics](#container-network-metrics)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[Prometheus](https://prometheus.io/docs/introduction/overview/) is an open-source software project
written in Go that is used to record real-time metrics in a time series database built using a HTTP
pull model, with flexible queries and real-time alerting.

*Update on 03/10/2018, v2.2*

- https://prometheus.io/blog/2017/11/08/announcing-prometheus-2-0/
- https://coreos.com/blog/prometheus-2.0-released

*References*

- https://prometheus.io/docs/introduction/overview/
- https://prometheus.io/docs/operating/configuration/
- https://movio.co/blog/prometheus-service-discovery-kubernetes/

# Concepts

## Metric Types

Prometheus provides four core metric types, namely:
- Counter
- Gauge
- Histogram
- Summary

A counter is a cumulative metric that represents a **single monotonically increasing** counter whose
value can only increase or be reset to zero on restart. For example, you can use a counter to
represent the number of requests served, tasks completed, or errors. Do not use a counter to expose
a value that can decrease. For example, do not use a counter for the number of currently running
processes; instead use a gauge.

A gauge is a metric that represents a single numerical value that can arbitrarily go up and down.
Gauges are typically used for measured values like temperatures or current memory usage, but also
"counts" that can go up and down, like the number of concurrent requests.

A histogram samples observations (usually things like request durations or response sizes) and
counts them in configurable buckets. For a histogram metric `<basename>`, prometheus provides a
couple of time series, i.e.
- bucket: `basename_bucket{le="<upper inclusive bound>"}` (`le` means "less and equal")
- total: `<basename>_sum`
- count: `<basename>_count` (identical to `<basename>_bucket{le="+Inf"}` above)

Similar to a histogram, a summary samples observations (usually things like request durations and
response sizes). While it also provides a total count of observations and a sum of all observed
values, it calculates configurable quantiles over a sliding time window.
- bucket: `<basename>{quantile="<φ>"}`
- total: `<basename>_sum`
- count: `<basename>_count`

**Note about histogram and summary.** There are two rules of thumb for choosing metric type between
the two:
- If you need to aggregate, choose histograms.
- Otherwise, choose a histogram if you have an idea of the range and distribution of values that
  will be observed. Choose a summary if you need an accurate quantile, no matter what the range
  and distribution of the values is.

In most cases, histogram will suffice. For example, if we want to know the number of requests that
are served within 300ms within last 5min, we can do:

```
sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m])) by (job)
 /
sum(rate(http_request_duration_seconds_count[5m])) by (job)
```

If we want to know the time where 95% requests are served. To do that, you can either configure a
summary with a 0.95-quantile and (for example) a 5-minute decay time, or you configure a histogram
with a few buckets around the 300ms, and uses `histogram_quantile` function.

# Components

## Prometheus Server

**TargetManager (retrieval)**

TargetManager is responsible to scrape metrics from all configured targets: it runs a goroutine
per target.

**RuleManager**

There are two kinds of rules: recording rule and alerting rule.
- Recording rules allow you to precompute frequently needed or computationally expensive expressions
  and save their result as a new set of time series.
- Alerting rules allow you to define alert conditions based on Prometheus expression language
  expressions and to send notifications about firing alerts to an external service.

All rules (recording and alerting) are evaluated at a regular interval. If the evaluated rule is
alerting rule and is not pending, then rule manager will try to send the rules. RuleManager runs
a goroutine per rule group (a group of related rules).

**Notifier**

Notifier is responsible to send alerts to AlertManager. Notifier runs in a goroutine and exposes a
`Send` method to its caller (called via RuleManager whenever an alert is triggered via a rule).

**PromQL**

PromQL is a package (not a running gorouting) that handles query, parsing of prometheus rules. The
main datastructure is `Engine` and an interface `Queryable`. Frontend, or generally, prometheus API,
uses the interface methods to query time series. Local storage implements the interface, while
remote storage doesn't; this means to query metrics in remote storage such as influxdb, you need to
contact influxdb directly.

**Storage (Remote)**

For remote storage, there is a StorageQueueManager which manages a queue of samples to be sent to
the remote storage (openTSDB, influxdb, graphite). There is a goroutine per shard (sharding is based
on metric's fingerprint) that queues the samples, and flush to underline storage when samples are
full or flush interval is reached.

**Storage (Local)**

Prometheus has a sophisticated local storage subsystem. For indexes, it uses LevelDB. For the bulk
sample data, it has its own custom storage layer, which organizes sample data in chunks of constant
size (1024 bytes payload). These chunks are then stored on disk in one file per time series.

**Service Discovery**

Prometheus supports different service discovery mechanism, e.g. gce, azure, kubernetes, etc. If we
define a service discovery section in prometheus config file, prometheus server (target manager)
will run goroutines to utilize service discovery features.

For example, if we define `kubernetes_sd_configs` in our config file, prometheus will create
goroutines to list & watch kubernetes api server based on configured roles (node, pods, etc). For
different roles, prometheus will automatically apply meta labels: these meta labels are well
documented in prometheus website. For example, pod listed from kubernetes will have a bunch of meta
labels, one of them is `__meta_kubernetes_pod_ip`, which is attached to the pod target using
`pod.Status.PodIP`, see file `discovery/kubernetes/pod.go`. The meta labels are provided to users
to relabel them for their own use. These labels will be discarded during scape.

```yaml
# Example scrape config for probing services via the Blackbox Exporter.
#
# The relabeling allows the actual service scrape endpoint to be configured
# via the following annotations:
#
# * `prometheus.io/probe`: Only probe services that have a value of `true`
- job_name: 'kubernetes-services'

  metrics_path: /probe
  params:
    module: [http_2xx]

  kubernetes_sd_configs:
  - api_servers:
    - 'https://kubernetes.default.svc'
    in_cluster: true
    role: service

  relabel_configs:
  - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_probe]
    action: keep
    regex: true
  - source_labels: [__address__]
    target_label: __param_target
  - target_label: __address__
    replacement: blackbox
  - source_labels: [__param_target]
    target_label: instance
  - action: labelmap
    regex: __meta_kubernetes_service_label_(.+)
  - source_labels: [__meta_kubernetes_service_namespace]
    target_label: kubernetes_namespace
  - source_labels: [__meta_kubernetes_service_name]
    target_label: kubernetes_name
```

Relabel is quite important in service discovery. For the example config above, we have label
`__meta_kubernetes_service_annotation_prometheus_io_probe` (all annotations will be added to meta
labels), the action for this label is `keep` and regex is `true`, which means only targets (service)
with this label (annotation), and whose value is `true` will be kept; all other targets will be
dropped. For the label `__meta_kubernetes_service_namespace`, the action is empty so prometheus
will use default action `replace`; target label is `kubernetes_namespace` so this relabel config
adds a label `kubernetes_namespace` to all services and its value equals that of `__meta_kubernetes_service_namespace`.

## PushGateway

PushGateway is simple. It exposes API endpoints to external services to push metrics. The metrics
are buffered in memory and can optionally be flushed to disk.

## Exporter

There are a number of libraries and servers which help in exporting existing metrics from third-party
systems as Prometheus metrics. E.g. node exporter collects machine informations and exposes a
`host:port/metrics` endpoint for prometheus to scrape metrics.

# Kubernetes Monitoring with Prometheus

## Methodology

Following is a list of common methodologies. The `USE Method` targets at **Resources** like CPUs,
disks, etc, while the `RED Method` targets at **Application Softwares**.

The `Four Golden Rules` from Google SRE:
- Latency: The time it takes to service a request
- Traffic: A measure of how much demand is being placed on your system
- Errors: The rate of requests that fail
- Saturation: How "full" your service is

The `USE Method`:
- Resource: all physical server functional components (CPUs, disks, busses, ...)
- Utilization: the average time that the resource was busy servicing work
- Saturation: the degree to which the resource has extra work which it can't service, often queued
- Errors: the count of error events

The `RED Method`:
- Rate: The number of requests per second
- Errors: The number of those requests that are failing
- Duration: The amount of time those requests take

In the following, we'll look at resources [USE methods](http://www.brendangregg.com/USEmethod/use-linux.html).

*References*

- https://blog.freshtracks.io/a-deep-dive-into-kubernetes-metrics-b190cc97f0f6
- https://blog.freshtracks.io/a-deep-dive-into-kubernetes-metrics-66936addedae
- https://blog.freshtracks.io/a-deep-dive-into-kubernetes-metrics-part-2-c869581e9f29
- https://blog.freshtracks.io/a-deep-dive-into-kubernetes-metrics-part-3-container-resource-metrics-361c5ee46e66

## Node CPU Metrics

**CPU Utilization**

One PromQL for cpu utilization can be (from node_exporter v0.17.0):

```
sum(rate(node_cpu_seconds_total{mode!="idle",mode!="iowait",mode!~"^(?:guest.*)$"}[5m])) BY (instance)

Element                             Value
{instance="192.168.11.204:9100"}    0.21745833333334505
```

The end result is time spent on "non-idle, non-iowait, non-guest" for all CPUs, measured per second
during 5min, and per node (instance).

**CPU Saturation**

The number used for CPU Saturation can be `node_load1`, `node_load5` and `node_load15`. Loosely, the
[load average](https://scoutapm.com/blog/understanding-load-averages) is the number of processes
running plus the those waiting to run across 1min, 5min and 15min. To properly calculate load, we
also need number of CPUs, thus the PromQL can be:

```
sum(node_load1) by (node) / count(node_cpu{mode="system"}) by (node) * 100

Element                                                         Value
node_load15{instance="192.168.11.204:9100",job="node_exporter"} 0.18
```

The end result is load average amortized across cores. Generally, a number less than 0.75 is ideal,
and 1 can be interpreted as "fix it now", and a number larger than 1 can be problematic (though it
can be ok if the load is a spike, i.e. the number is high only for a small period, as indicated by
`node_load1`).

**CPU Error**

Prometheus node_exporter doesn't provide CPU error metrics.

## Node Memory Metrics

**Memory Utilization**

Memory utilization can be computed using MemAvailable:

```
1 - sum(node_memory_MemAvailable_bytes) by (node)  / sum(node_memory_MemTotal_bytes) by (node)

Element Value
{}      0.18149520192227075
```

MemAvailable is only available in newer kernel (after 3.14). In older kernel, this can be roughly
computed using [free, cache, and buffers](https://www.linuxatemyram.com/):

```
sum(node_memory_MemFree_bytes + node_memory_Cached_bytes + node_memory_Buffers_bytes)
```

**Memory Saturation**

Memory saturation is a complex, one measurement can be number of paging a node is doing. Note this
is incomplete metrics, since paging is quite normal in Linux. Another metrics can be OOM activities.
In general, the more paging & OOM activities, the more memory is saturated.

```
node_vmstat_pgpgin
node_vmstat_pgpgout
```

**Memory Error**

Prometheus will expose memory errors for certain hardwares:

```
node_edac_correctable_errors_total
node_edac_uncorrectable_errors_total
node_edac_csrow_correctable_errors_total
node_edac_csrow_uncorrectable_errors_total
```

## Node Disk Metrics

Disk metrics can be divided into:
- capacity
- throughput

For capacity utilization & saturation, we can use

```
sum(node_filesystem_free_bytes{mountpoint="/"}) by (node, mountpoint) / sum(node_filesystem_size_bytes{mountpoint="/"}) by (node, mountpoint)
```

For throughput utilization & saturation, it's generally harder to determine, but we can still use
following metrics:

```
node_disk_io_now
node_disk_io_time_ms
node_disk_io_weighted
```

## Node Network Metrics

**Network Utilization**

Depending on use case, network utilization can be defined as rate of receive or transmit. Below, we
define network utilization as sum of recieve and transmit:

```
sum(rate(node_network_receive_bytes_total[5m])) by (node) + sum(rate(node_network_transmit_bytes_total[5m])) by (node)
```

**Network Saturation**

It's hard to determine network saturation without accessing underline devices, but we can peak into
saturation via looking at dropped packets:

```
sum(rate(node_network_receive_drop_total[5m])) by (node) + sum(rate(node_network_transmit_drop_total[5m])) by (node)
```

**Network Error**

Network error is reported as:

```
node_network_receive_errs
node_network_transmit_errs
```

## Container CPU Metrics

**CPU Utilization**

Promethus with kubernetes exposes the following metrics:
- container_cpu_user_seconds_total: the total amount of "user" time (i.e. time spent not in the kernel)
- container_cpu_system_seconds_total: the total amount of "system" time (i.e. time spent in the kernel)
- container_cpu_usage_seconds_total: the sum of the above

Following query will give us the number of cores that are being used by each container.

```
sum(rate(container_cpu_usage_seconds_total[5m])) by (container_name)

Element                                     Value
{container_name="prometheus-node-exporter"} 0.001173670138983051
...
```

**CPU Saturation**

The metric `container_cpu_cfs_throttled_seconds_total` records the total amount of time container
was throttled. In Kubernetes, this happens when resource limit is set, which translate to cgroups
`cpu.cfs_period_us` and `cpu.cfs_quota_us`.

In an experiment, `prometheus-node-exporter` container was set to `10m` limit, the metric value is:

```
sum(rate(container_cpu_cfs_throttled_seconds_total[5m])) by (container_name)

Element                                     Value
{container_name="prometheus-node-exporter"} 0.49217656050847447
```

When setting limit to `50m`, the metric value is:

```
{container_name="prometheus-node-exporter"}	0.10220450339999998
```

When setting limit to `100m`, the metric value is:

```
{container_name="prometheus-node-exporter"}	0.04043697797627118
```

**CPU Error**

Much like the node_exporter, cAdvisor does not expose CPU errors.

## Container Memory Metrics

**Memory Utilization**

For memory utilization, the metric to use is `container_memory_working_set_bytes`, which is what the
OOMKiller is looking for. The metric `container_memory_usage_bytes` includes cache (e.g. file cache)
which is not accurate:

```
sum(container_memory_working_set_bytes{name!~"POD"}) by (name)
```

"POD" is parent cgroup which tracks stats for all the containers in the pod.

**Memory Saturation**

Saturation can be defined as the amount of available memory from the limit:

```
sum(container_memory_working_set_bytes) by (container_name) / sum(container_spec_memory_limit_bytes) by (container_name)
```

For `inf`, it means container with no limit set.

**Memory Error**

Memory errors are not exposed.

## Container Disk Metrics

Similar to Node level metrics.

## Container Network Metrics

Similar to Node level metrics.
