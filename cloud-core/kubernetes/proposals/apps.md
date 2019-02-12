<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [20180101 - ttl after finished](#20180101---ttl-after-finished)
  - [20180514 - sidecar container](#20180514---sidecar-container)
  - [20180925 - optional service environment variables](#20180925---optional-service-environment-variables)
  - [20190318 - pod disruption budget](#20190318---pod-disruption-budget)
- [Feature & Design](#feature--design)
  - [(large) workload designs](#large-workload-designs)
  - [(medium) controller revision](#medium-controller-revision)
  - [(medium) statefulset update](#medium-statefulset-update)
  - [(small) daemonset update](#small-daemonset-update)
  - [(small) statefulset pod management policy](#small-statefulset-pod-management-policy)
  - [(small) selector generation](#small-selector-generation)
  - [(small) pod preset](#small-pod-preset)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes apps.

- [SIG-Apps KEPs](https://github.com/kubernetes/enhancements/blob/master/keps/sig-apps)
- [SIG-Apps Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/apps)
- [SIG-Apps Community](https://github.com/kubernetes/community/tree/master/sig-apps)

# KEPs

## 20180101 - ttl after finished

- *Date: 08/25/2019, v1.15, alpha*

The KEP proposes a mechanism for users to delete resources automatically after their TTL. At this
moment, only Job resource supports this feature, with Pod (RestartPolicy!=Always) and Custom Resources
to be supported in the future.

At the API level, a new `TTLSecondsAfterFinished` field will be added to `PodSpec` and `JobSpec` for
users to set the TTL (The KEP mentions `PodSpec`, but in alpha, the field only appears in `JobSpec`).

A couple notes:
- TTL will take effect even if the resource has owner reference.
- TTL won't block deletion from garbage collector.

Implementation-wise, a new `ttlafterfinished` controller is running as part of controller manager.

*References*

- [ttl after finished KEP link](https://github.com/kubernetes/enhancements/blob/310c6ce25124e701a8e47f0221f3afd47084a505/keps/sig-apps/0026-ttl-after-finish.md)

## 20180514 - sidecar container

- *Date: 08/24/2019, v1.15, design*

The sidecar container KEP proposes a new class of container to solve the problem of container
lifycycle dependency issue. In Kubernetes, we usually want the "sidecar container" to start before
normal container, and exit after normal container. This is to facilitate application startup and
shutdown.

The KEP adds a new `LifecycleType` field to `Pod.Spec.Containers[].Lifecycle.Type`, with two
options: `default` and `sidecar`. The `sidecar` type container is just normal container in almost
all aspects, except lifecycle related operations.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: myapp
spec:
  containers:
  - name: myapp
    image: myapp
    command: ['do something']
  - name: sidecar
    image: sidecar-image
    lifecycle:
      type: Sidecar
    command: ["do something to help my app"]
```

The new Pod lifecycle becomes:
- Init containers start
- Init containers finish
- Sidecars start
- Sidecars become ready
- Containers start
- (Shutdown)
- Containers sent SIGTERM
- Once all Containers have exited: Sidecars sent SIGTERM

In addition, if all normal containers exit (voluntarily, not by SIGTERM) and are in their terminal
states, i.e. Succeeded or Failed, then Kubelet will send SIGTERM to all sidecar containers. Note
this happens only for Pod with RestartPolicy!=Always; for Pod with RestartPolicy==Always, Kubelet
will behave as usual, i.e. restart normal containers.

All other fields in `Pod.Spec.Containers[].Lifecycle` works as before. One thing to note is that
PreStop Hooks will be sent to sidecar containers before normal containers are terminated.

*References*

- [sidecar container KEP link](https://github.com/kubernetes/enhancements/blob/aba897e14b2663c2a479c1c60654a57887e236d1/keps/sig-apps/sidecarcontainers.md)
- https://github.com/kubernetes/enhancements/issues/753

## 20180925 - optional service environment variables

- *Date: 08/25/2019, v1.15*

The KEP provides an option for Pod to disable environment variables for services in the same
namespace via `EnableServiceLinks` field in Pod spec.

For example, Pod env changes from

```
$ kubectl exec -it -n kube-system nginx-6f57bf6bc7-h7k8x bash
root@nginx-6f57bf6bc7-h7k8x:/# env
KUBE_DNS_SERVICE_PORT=53
KUBE_DNS_PORT_53_TCP_PROTO=tcp
HOSTNAME=nginx-6f57bf6bc7-h7k8x
NJS_VERSION=1.13.12.0.2.0-1~stretch
KUBE_DNS_PORT_53_UDP=udp://10.96.0.10:53
KUBE_DNS_PORT_9153_TCP=tcp://10.96.0.10:9153
NGINX_VERSION=1.13.12-1~stretch
METRICS_SERVER_SERVICE_HOST=10.100.137.53
KUBE_DNS_PORT_53_UDP_PROTO=udp
KUBERNETES_PORT_443_TCP_PROTO=tcp
KUBERNETES_PORT_443_TCP_ADDR=10.96.0.1
METRICS_SERVER_PORT_443_TCP_PROTO=tcp
KUBE_DNS_PORT_9153_TCP_PORT=9153
KUBE_DNS_PORT_53_UDP_ADDR=10.96.0.10
KUBERNETES_PORT=tcp://10.96.0.1:443
PWD=/
HOME=/root
KUBE_DNS_PORT_53_TCP_ADDR=10.96.0.10
KUBE_DNS_PORT=udp://10.96.0.10:53
KUBERNETES_SERVICE_PORT_HTTPS=443
KUBERNETES_PORT_443_TCP_PORT=443
METRICS_SERVER_PORT_443_TCP=tcp://10.100.137.53:443
METRICS_SERVER_PORT=tcp://10.100.137.53:443
METRICS_SERVER_PORT_443_TCP_ADDR=10.100.137.53
KUBE_DNS_SERVICE_PORT_METRICS=9153
...
```

to

```
$ kubectl exec -it -n kube-system nginx-864d944c4f-22pf9 bash
root@nginx-864d944c4f-22pf9:/# env
HOSTNAME=nginx-864d944c4f-22pf9
NJS_VERSION=1.13.12.0.2.0-1~stretch
NGINX_VERSION=1.13.12-1~stretch
KUBERNETES_PORT_443_TCP_PROTO=tcp
KUBERNETES_PORT_443_TCP_ADDR=10.96.0.1
KUBERNETES_PORT=tcp://10.96.0.1:443
PWD=/
HOME=/root
KUBERNETES_SERVICE_PORT_HTTPS=443
KUBERNETES_PORT_443_TCP_PORT=443
KUBERNETES_PORT_443_TCP=tcp://10.96.0.1:443
TERM=xterm
SHLVL=1
KUBERNETES_SERVICE_PORT=443
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
KUBERNETES_SERVICE_HOST=10.96.0.1
_=/usr/bin/env
```

This is necessary because:
- it can avoid accidental conflicts with user defined env
- mimigate performance impact for a namespace with thousands of services (slow pod startup)
- docker removes service links for a long time; this is to make Kubernetes compatible with certain
  docker images which explicitly fail at startup time if certain service links exist

*References*

- [optional service environment variables KEP link](https://github.com/kubernetes/enhancements/blob/310c6ce25124e701a8e47f0221f3afd47084a505/keps/sig-apps/0028-20180925-optional-service-environment-variables.md)

## 20190318 - pod disruption budget

- *Date: 05/02/2017, v1.6, design*
- *Date: 06/22/2019, v1.15, beta*

PodDisruptionBudget (pdb) allows user to specify rules about safety constraints on pods. A controller
called `disruption` is running as part of controller manager. The controller reads all `pdb`, as well
as workloads (rs, rc, deployment, etc); then update pdb.status accordingly. The controller itself
won't do any safety constraint check. Later, when user (or service account) tries to evict a pod via
pod' eviction subresource, e.g. via
```
http://127.0.0.1:8080/api/v1/namespaces/default/pods/nginx-348975970-17kbf/eviction
```

the request will go to `kubernetes/pkg/registry/core/pod/storage/eviction.go`, where api server reads
out pdbs and make sure pod safety contraints are satisfied; and if not, reject the request. Two top
level API objects defined here (`PodDisruptionBudget` and `Eviction`) both belong to `policy/v1beta1`
API group.

*References*

- [poddisruptionbudget graduation to stable KEP link](https://github.com/kubernetes/enhancements/blob/1bad2ecb356323429a6ac050f106af4e1e803297/keps/sig-apps/20190318-PodDisruptionBudget-graduation-to-stable.md)
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-disruption-budget/
- https://github.com/kubernetes/enhancements/pull/904

# Feature & Design

## (large) workload designs

Workload design include
- deployment
- daemonset
- statefulset
- job
- cronjob

**cronjob**

CronJob provides time-based Jobs, i.e.
- once at a specified point in time,
- repeatedly at a specified point in time.

CronJob doens't manage Pods directly; instead, it uses Job to manage Pods. Job naming uses hashed-date
suffix approach. The concept of CronJob is simple, but the discussion of fault tolerance worth reading:
- Starting Jobs in the face of controller failures
  - at least job controller HA (leader election) setup is required
- Ensuring jobs are run at most once
  - at cronjob level, it is possible to fail the semantic in race conditin
  - at pod level, job controller doesn't provide the semantic (we need somethine like StatefulJob)
  - at container level, Kubelet is not written to ensure at-most-one-container-start per pod.

**statefulset**

The StatefulSet is responsible for creating and maintaining a set of identities and ensuring that
there is one pod and zero or more supporting resources for each identity. There should never be more
than one pod or unique supporting resource per identity at any one time.

Guarantees from statefulset:
- Unique identity assignment, i.e. {name}-{0 ~ replicas-1}
- Parameterizing pod templates and supporting resources, e.g. every pod has its own PVC
- Accessing pods by stable network identity, i.e. every pod contains a DNS record in the cluster
- Controller will prevent duplicate identities, provide ordered startup and shutdown, etc

Statefulset has two update strategy: `RollingUpdate` and `OnDelete`. The first will delete and the
create a new pod for the last indexed pod, once succeeds, proceeds the the next one, until all pods
are updated. A `partition` field controls phased roll out. The second will only update pod when user
updates `.spec.template` field.

*References*

- [deployment design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/deployment.md)
- [daemonset design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/daemon.md)
- [statefulset design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/stateful-apps.md)
- [job design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/job.md)
- [cronjob design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/cronjob.md)
- [statefulset update design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/statefulset-update.md)
- [daemonset update design proposal](https://github.com/kubernetes/community/blob/753c86763083d7cbd13a7c8f7b0091c235255b1b/contributors/design-proposals/apps/daemonset-update.md)

## (medium) controller revision

To facilitate update and rollback of workload controllers (i.e. Deployment, StatefulSet, DaemonSet),
a mechanism is proposed to allow controllers (in-tree and out-tree) to manage a bounded history of
revisions to the declared target state of their generated objects. The generated objects include
Pod, PVC, etc. ControllerRevision is primarily intended for internal use by controllers.

The mechanism includes a new `ControllerRevision` API object, shown below:

```go
type ControllerRevision struct {
	metav1.TypeMeta
	metav1.ObjectMeta

	// Data is the Object representing the state.
	Data runtime.Object

	// Revision indicates the revision of the state represented by Data.
	Revision int64
}
```

where `runtime.Object` is an interface and the struct commonly used here is `runtime.RawExtension`.

Apart from the new object, a set of controller implementation 'guidelines' are provided in the
design doc, including:
- General Flow
- Version Snapshot Creation
- Revision Number Selection
- History Reconstruction
- History Maintenance
- Version Tracking
- Version Equivalence
- Target Object State Reconciliation
- Kubernetes Upgrades

Note as of Kubernetes v1.15, statefulset and daemonset will use controller revision, but not
deployment, which still uses multiple replicaset to managee multiple versions.

```
$ kubectl get sts --all-namespaces
NAMESPACE   NAME   READY   AGE
default     web    2/2     43m

$ kubectl get daemonsets --all-namespaces
NAMESPACE     NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
kube-system   kube-proxy   1         1         1       1            1           <none>          62d

$ kubectl get deployments --all-namespaces
NAMESPACE     NAME      READY   UP-TO-DATE   AVAILABLE   AGE
default       nginx     1/1     1            1           52m
kube-system   coredns   2/2     2            2           62d

$ kubectl get controllerrevisions --all-namespaces
NAMESPACE     NAME                    CONTROLLER                  REVISION   AGE
default       web-57864df6bb          statefulset.apps/web        1          42m
default       web-7d56f4d666          statefulset.apps/web        2          42m
kube-system   kube-proxy-7999c6dd97   daemonset.apps/kube-proxy   1          62d
```

*References*

- [controller revision design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/controller_history.md)

## (medium) statefulset update

- *Date: 09/07/2017, v1.7, beta*

As of Kubernetes 1.6, only `.Spec.Replicas` and `.Spec.Template.Containers` are mutable fields:
- updating `.Spec.Replicas` will scale the number of Pods in the statefulset
- updating `.Spec.Template.Containers` will update Pods only when those Pods are manually deleted

The implementation of this proposal will add the capability to perform ordered, automated,
sequential updates to StatefulSet. StatefulSet controller uses the `ControllerRevision` API for
version tracking, update detection, and rollback detection.

The apps/v1 API:

```go
// StatefulSetUpdateStrategy indicates the strategy that the StatefulSet
// controller will use to perform updates. It includes any additional parameters
// necessary to perform the update for the indicated strategy.
type StatefulSetUpdateStrategy struct {
    // Type indicates the type of the StatefulSetUpdateStrategy.
    // Default is RollingUpdate.
    // +optional
    Type StatefulSetUpdateStrategyType `json:"type,omitempty" protobuf:"bytes,1,opt,name=type,casttype=StatefulSetStrategyType"`
    // RollingUpdate is used to communicate parameters when Type is RollingUpdateStatefulSetStrategyType.
    // +optional
    RollingUpdate *RollingUpdateStatefulSetStrategy `json:"rollingUpdate,omitempty" protobuf:"bytes,2,opt,name=rollingUpdate"`
}

// StatefulSetUpdateStrategyType is a string enumeration type that enumerates
// all possible update strategies for the StatefulSet controller.
type StatefulSetUpdateStrategyType string

const (
    // RollingUpdateStatefulSetStrategyType indicates that update will be
    // applied to all Pods in the StatefulSet with respect to the StatefulSet
    // ordering constraints. When a scale operation is performed with this
    // strategy, new Pods will be created from the specification version indicated
    // by the StatefulSet's updateRevision.
    RollingUpdateStatefulSetStrategyType StatefulSetUpdateStrategyType = "RollingUpdate"
    // OnDeleteStatefulSetStrategyType triggers the legacy behavior. Version
    // tracking and ordered rolling restarts are disabled. Pods are recreated
    // from the StatefulSetSpec when they are manually deleted. When a scale
    // operation is performed with this strategy,specification version indicated
    // by the StatefulSet's currentRevision.
    OnDeleteStatefulSetStrategyType StatefulSetUpdateStrategyType = "OnDelete"
)

// RollingUpdateStatefulSetStrategy is used to communicate parameter for RollingUpdateStatefulSetStrategyType.
type RollingUpdateStatefulSetStrategy struct {
    // Partition indicates the ordinal at which the StatefulSet should be
    // partitioned.
    // Default value is 0.
    // +optional
    Partition *int32 `json:"partition,omitempty" protobuf:"varint,1,opt,name=partition"`
}
```

Note about the `partition` strategy for `RollingUpdate`:

> If a partition is specified, all Pods with an ordinal that is greater than or equal to the
> partition will be updated when the StatefulSet's `.spec.template` is updated. All Pods with an
> ordinal that is less than the partition will not be updated, and, even if they are deleted, they
> will be recreated at the previous version. If a StatefulSet's `...partition` is greater than its
> `.spec.replicas`, updates to its `.spec.template` will not be propagated to its Pods. In most
> cases you will not need to use a partition, but they are useful if you want to stage an update,
> roll out a canary, or perform a phased roll out.

*References*

- [statefulset update design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/apps/statefulset-update.md)

## (small) daemonset update

- *Date: 09/07/2017, v1.7, beta*

Before Kubernetes 1.5, users can update a DaemonSet but the changes will not be propagated to its
managing pods, until those pods are killed. The behavior is not consistent with other workload APIs,
thus the proposal proposes to add a "RollingUpdate" strategy which allows DaemonSet to update those
pods, similar to how Deployment works.

Implementation-wise, DaemonSet controller will leverage the `ControllerRevision` API for DaemonSet
revision introspection and rollback. The `ControllerRevision` is also called `history` in the
proposal.

The apps/v1 API:

```go
// DaemonSetUpdateStrategy is a struct used to control the update strategy for a DaemonSet.
type DaemonSetUpdateStrategy struct {
    // Type of daemon set update. Can be "RollingUpdate" or "OnDelete". Default is RollingUpdate.
    // +optional
    Type DaemonSetUpdateStrategyType `json:"type,omitempty" protobuf:"bytes,1,opt,name=type"`

    // Rolling update config params. Present only if type = "RollingUpdate".
    //---
    // TODO: Update this to follow our convention for oneOf, whatever we decide it
    // to be. Same as Deployment `strategy.rollingUpdate`.
    // See https://github.com/kubernetes/kubernetes/issues/35345
    // +optional
    RollingUpdate *RollingUpdateDaemonSet `json:"rollingUpdate,omitempty" protobuf:"bytes,2,opt,name=rollingUpdate"`
}

type DaemonSetUpdateStrategyType string

const (
    // Replace the old daemons by new ones using rolling update i.e replace them on each node one after the other.
    RollingUpdateDaemonSetStrategyType DaemonSetUpdateStrategyType = "RollingUpdate"

    // Replace the old daemons only when it's killed
    OnDeleteDaemonSetStrategyType DaemonSetUpdateStrategyType = "OnDelete"
)

// Spec to control the desired behavior of daemon set rolling update.
type RollingUpdateDaemonSet struct {
    // The maximum number of DaemonSet pods that can be unavailable during the
    // update. Value can be an absolute number (ex: 5) or a percentage of total
    // number of DaemonSet pods at the start of the update (ex: 10%). Absolute
    // number is calculated from percentage by rounding up.
    // This cannot be 0.
    // Default value is 1.
    // Example: when this is set to 30%, at most 30% of the total number of nodes
    // that should be running the daemon pod (i.e. status.desiredNumberScheduled)
    // can have their pods stopped for an update at any given
    // time. The update starts by stopping at most 30% of those DaemonSet pods
    // and then brings up new DaemonSet pods in their place. Once the new pods
    // are available, it then proceeds onto other DaemonSet pods, thus ensuring
    // that at least 70% of original number of DaemonSet pods are available at
    // all times during the update.
    // +optional
    MaxUnavailable *intstr.IntOrString `json:"maxUnavailable,omitempty" protobuf:"bytes,1,opt,name=maxUnavailable"`
}
```

*References*

- [daemonset update design proposal](https://github.com/kubernetes/community/blob/753c86763083d7cbd13a7c8f7b0091c235255b1b/contributors/design-proposals/apps/daemonset-update.md)

## (small) statefulset pod management policy

- *Date: 09/07/2017*

In Kubernetes 1.7 and later, StatefulSet allows you to relax its ordering guarantees while
preserving its uniqueness and identity guarantees via its `.spec.podManagementPolicy` field.
Note the policy only applies when creating/terminating, or scaling statefulset: it does not
apply to updates.

```go
// PodManagementPolicyType defines the policy for creating pods under a stateful set.
type PodManagementPolicyType string

const (
    // OrderedReadyPodManagement will create pods in strictly increasing order on
    // scale up and strictly decreasing order on scale down, progressing only when
    // the previous pod is ready or terminated. At most one pod will be changed
    // at any time.
    OrderedReadyPodManagement PodManagementPolicyType = "OrderedReady"
    // ParallelPodManagement will create and delete pods as soon as the stateful set
    // replica count is changed, and will not wait for pods to be ready or complete
    // termination.
    ParallelPodManagement PodManagementPolicyType = "Parallel"
)
```

## (small) selector generation

- *Date: 09/07/2017*

Selector generation means automatically generate labels for Job (and later for other workloads), to
avoid users accidentally create a job which has an overlapping selector.

A new field `job.spec.manualSelector` is added:

```go
    // manualSelector controls generation of pod labels and pod selectors.
    // Leave `manualSelector` unset unless you are certain what you are doing.
    // When false or unset, the system pick labels unique to this job
    // and appends those labels to the pod template.  When true,
    // the user is responsible for picking unique labels and specifying
    // the selector.  Failure to pick a unique label may cause this
    // and other jobs to not function correctly.  However, You may see
    // `manualSelector=true` in jobs that were created with the old `extensions/v1beta1`
    // API.
    // +optional
    ManualSelector *bool
```

*References*

- [selector generation design doc](https://github.com/kubernetes/community/blob/a4a1d2f561eac609403f0db7d31d764daaea3b00/contributors/design-proposals/apps/selector-generation.md)

## (small) pod preset

- *Date: 06/11/2017, v1.6, alpha*
- *Date: 04/04/2020, v1.18, alpha*

PodPreset is used to inject information to a set of pods (selected via selectors). The primary use
case is for service catalog, where when a service from service broker is provisioned, admins (or
service catalog controller) can create resources like secret for application to use. These services
can be inject into pod at admission time. A PodPreset admission controller is responsible to inject
these settings. For each pod, the admission controller loops through all PodPresets and inject settings
for all matching ones.

*Update on 06/23/2019, v1.15*

With the introduction of dynamic admission control, projects like service catalog, istio do not use
PodPreset for injecting settings. PodPreset is still alpha in Kubernetes v1.15.

*References*

- [podpreset design doc](https://github.com/kubernetes/community/blob/630c2f78b86a327f989684b4a7bd9ee06bb431dc/contributors/design-proposals/pod-preset.md)
