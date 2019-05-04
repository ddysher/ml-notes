<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature & Design](#feature--design)
  - [scalability improvements in kubernetes v1.2](#scalability-improvements-in-kubernetes-v12)
  - [scalability improvements in kubernetes v1.3](#scalability-improvements-in-kubernetes-v13)
  - [scalability improvements in kubernetes v1.6](#scalability-improvements-in-kubernetes-v16)
  - [kubernetes scalability SLO (v1.2)](#kubernetes-scalability-slo-v12)
  - [kubernetes scalability SLO (v1.6)](#kubernetes-scalability-slo-v16)
  - [scalability testing and kubemark](#scalability-testing-and-kubemark)
- [Others](#others)
  - [kubernetes scalability path (v1.1 -> v1.6)](#kubernetes-scalability-path-v11---v16)
  - [references](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes resource management
- [SIG-Scalability Community](https://github.com/kubernetes/community/tree/master/sig-scalability)

# Feature & Design

## scalability improvements in kubernetes v1.2

Below is a digest from kubernetes blog post:
- Created a "read cache" at the API server level
- Introduce a "Pod Lifecycle Event Generator" (PLEG) in the Kubelet
- Improved scheduler throughput
- A more efficient JSON parser

## scalability improvements in kubernetes v1.3

Below is a digest from kubernetes blog post:

> Protocol Buffer-based serialization format to the API as an alternative JSON. All Kubernetes control
> plane components now use it for their communication. (We didn't change the format in which we store
> cluster state in etcd to Protocol Buffers yet, as we're still working on the upgrade mechanism. But
> we're very close to having this ready, and we expect to switch the storage format to Protocol Buffers
> in Kubernete 1.4. Our experiments show that this should reduce pod startup end-to-end latency by
> another 30%.)

Another big feature is 'kubemark', which is used to simulate a large cluster.

## scalability improvements in kubernetes v1.6

Below is a digest from kubernetes blog post:
- etcd v3 (watch was the main bottleneck in etcd v2)
- Switching storage data format to protobuf
- Others
  - optimizing the scheduler (which resulted in 5-10x higher scheduling throughput)
  - switching all controllers to a new recommended design using shared informers, which reduced resource consumption of controller-manager
  - optimizing individual operations in the API server (conversions, deep-copies, patch)
  - reducing memory allocation in the API server (which significantly impacts the latency of API calls)

## kubernetes scalability SLO (v1.2)

We benchmark Kubernetes scalability against the following Service Level Objectives (SLOs):
- API responsiveness1: 99% of all API calls return in less than 1s
  - in kubernetes 1.3, test will use multiple namespaces
- Pod startup time: 99% of pods and their containers (with pre-pulled images) start within 5s

We say Kubernetes scales to a certain number of nodes only if both of these SLOs are met.

## kubernetes scalability SLO (v1.6)

We are aware of the limited scope of these SLOs. There are many aspects of the system that they do
not exercise. For example, we do not measure how soon a new pod that is part of a service will be
reachable through the service IP address after the pod is started.

The top scalability-related priority for upcoming Kubernetes releases is to enhance our definition
of what it means to support X-node clusters by:
- refining currently existing SLOs
- adding more SLOs (that will cover various areas of Kubernetes, including networking)

## scalability testing and kubemark

*Date: 06/23/2018, v1.10*

The initial design doc for scalability testing and kubemark is here:
- [scalability-testing](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/design-proposals/scalability/scalability-testing.md)
- [kubemark](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/design-proposals/scalability/kubemark.md)

The a repository with kubemark metrics benchmark design is proposed:
- https://github.com/kubernetes/perf-tests
- [benchmark design](https://github.com/kubernetes/perf-tests/blob/b0fa5be3e838f03edffa290513be5c1d95a9a383/benchmark/docs/design.md)

Here is scripts & code to bring up a kubemark cluster, along with user guide:
- [kubemark guide](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/devel/kubemark-guide.md)
- https://github.com/kubernetes/kubernetes/tree/53cc12b9bdc78bc0a4ce50ea53311bdc6b3c96cb/test/kubemark
- https://github.com/kubernetes/kubernetes/tree/53cc12b9bdc78bc0a4ce50ea53311bdc6b3c96cb/cmd/kubemark

A few notes:
- Two options are mentioned in kubemark design doc: option 1 is to run multiple node components on a
  single node, and each listens on different ports; option 2 is to run kubemark on top of kubernetes:
  the core idea is to use Pod to simulate Nodes, leveraging kubernetes networking mode (IP per Pod),
  i.e. use pod IP as node IP
- The benchmark design doc identify metrics to judge how similar it is between the results of kubemark
  and real cluster
- kubemark is a separate binary under 'kubernetes/cmd/kubemark' with launch option in kubelet morph
  mode or kubeproxy morph mode; the binary first mocks out operations with side effect (e.g. mock out
  iptables interface) and then run real kubelet/kubeproxy code

# Others

## kubernetes scalability path (v1.1 -> v1.6)

Below is a list of supported nodes and pods per node metrics in each Kubernetes version:
- v1.1: 500 nodes, 30 pods per node
- v1.2: 1000 nodes, 100 pods per node
- v1.3: 2000 nodes, 60000 pod cluster
- v1.6: 5000 nodes, 150000 pod cluster

## references

- http://blog.kubernetes.io/2016/03/1000-nodes-and-beyond-updates-to-Kubernetes-performance-and-scalability-in-12.html
- http://blog.kubernetes.io/2016/07/kubernetes-updates-to-performance-and-scalability-in-1.3.html
- http://blog.kubernetes.io/2017/03/scalability-updates-in-kubernetes-1.6.html
