<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature & Design](#feature--design)
  - [rescheduling & rescheduler, or descheduler](#rescheduling--rescheduler-or-descheduler)
  - [rescheduler for critical pods](#rescheduler-for-critical-pods)
  - [pod priority](#pod-priority)
  - [pod preemption](#pod-preemption)
  - [pod priority quota](#pod-priority-quota)
  - [scheduler extender](#scheduler-extender)
  - [multi-scheduler](#multi-scheduler)
  - [scheduler framework, aka, scheduler v2](#scheduler-framework-aka-scheduler-v2)
  - [taint node by conditions](#taint-node-by-conditions)
  - [schedule daemonset pod by default scheduler](#schedule-daemonset-pod-by-default-scheduler)
  - [node affinity](#node-affinity)
  - [pod affinity/anti-affinity](#pod-affinityanti-affinity)
  - [taint, toleration and dedicated nodes](#taint-toleration-and-dedicated-nodes)
  - [scheduler equivalence class](#scheduler-equivalence-class)
  - [scheduler policy via configmap](#scheduler-policy-via-configmap)
  - [per-pod-configurable eviction behavior](#per-pod-configurable-eviction-behavior)
  - [scheduler binding](#scheduler-binding)
- [PRs](#prs)
  - [scheduling with volume count](#scheduling-with-volume-count)
  - [scheduler performance improvement for affinity/anti-affinity](#scheduler-performance-improvement-for-affinityanti-affinity)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes scheduling.

- [SIG-Scheduling Community](https://github.com/kubernetes/community/tree/master/sig-scheduling)

# Feature & Design

## rescheduling & rescheduler, or descheduler

*Date: 02/28/2018, v1.9*

**[Rescheduling proposal](https://github.com/kubernetes/community/blob/b8d4a1b389bd105d23ca496b1c67febe1e2efdf2/contributors/design-proposals/scheduling/rescheduling.md)**

The proposal is kind of an umbrella proposal which introduces some key mechanisms and components in
kubernetes scheduling area: priority, preemption, disruption budgets, the `/evict` subresource and
the rescheduler.

**[Rescheduler proposal](https://github.com/kubernetes/community/blob/b8d4a1b389bd105d23ca496b1c67febe1e2efdf2/contributors/design-proposals/scheduling/rescheduler.md)**

Rescheduler proposal is a scratch proposal highlights some possibilities around the design of rescheduler
(supplement of the rescheduling proposal) . The goal of rescheduler, as mentioned in the proposal, is
to improve some kind of objective function, and the primary use cases of the rescheduler are:
- Move Pods around to get a PENDING Pod to schedule
- Redistribute Pods onto new nodes added by a cluster auto-scaler when there are no PENDING Pods
- Move Pods around when CPU starvation is detected on a node

The proposal identifies a baseline rescheduler that
- only kicks in when there is Pending pods for some period of time
- is not a scheduler (depends on regular scheduler to schedule pods)

With this baseline rescheduler, a bunch of variations and improvements are described in the proposal.
The proposal is not updated for quite a while, but with the introduction of priority & preemption, I
suspect it is no longer true to say rescheduler only kicks in when there is Pending pods, since users
are supposed to use priority and pods can stay pending because of low priority.

**[Descheduler project](https://github.com/kubernetes-incubator/descheduler)**

Descheduler, based on its policy, finds pods that can be moved and evicts them. Please note, in
current implementation, descheduler does not schedule replacement of evicted pods but relies on the
default scheduler for that.

As of Kubernetes 1.9, rescheduler only cares about critical pods and will proactively reschedule
pods to other nodes; while descheduler only checks policies and evit pods from targeted nodes.

## rescheduler for critical pods

*Date: 07/20/2017, v1.7*

Rescheduler for critical pods is a component to re-schedule pending pods to other nodes, or shuffle
existing running pods to improve server utilizations. As of kubernetes 1.7, this is not a general
component; it is primarily used to make sure critical addon pods keep running. There is another
rescheduler called `descheduler` which works differently; it proactively rescheduless all pods in
the cluster. To benefit from rescheduler for critical pods, there are three requirements:
- pods must run in `kube-system` namespace (configurable)
- have the `scheduler.alpha.kubernetes.io/critical-pod` annotation set to empty string
- have the PodSpec's tolerations field set to `[{"key":"CriticalAddonsOnly", "operator":"Exists"}]`

Internally, rescheduler lists all unschedulable pods, and finds pods with the above annotation. For
all such unschedulable critical pods, it finds suitable nodes for them. Before assigning the pod to
selected nodes, rescheduler will taints the node with `CriticalAddonsOnly` to make room for the
critical pods. The taint will be removed once the add-on is successfully scheduled. The above
algothrim requires both annotation and taints to present for rescheduler to work.

*Update on 06/14/2018, v1.10, deprecated*

Rescheduler is marked deprecated in favor of priority/preemption feature in default scheduler.
Rescheduler will be completely deprecated once scheduling logic in daemonset controller is removed
and its pods are scheduled via default scheduler to leverage preemption feature; until then, we
still need rescheduler to shuffle pods for daemonset controller.

*References*

- [proposal](https://github.com/kubernetes/community/blob/b8d4a1b389bd105d23ca496b1c67febe1e2efdf2/contributors/design-proposals/scheduling/rescheduling-for-critical-pods.md)
- https://github.com/kubernetes/contrib/tree/master/rescheduler
- https://kubernetes.io/docs/tasks/administer-cluster/guaranteed-scheduling-critical-addon-pods/

## pod priority

*Date: 05/23/2017, v1.6, design*

At time of writing, pod priority is still in proposal phase; the general idea is to associate each
pod with a priority. The priority will be used in both pod scheduling and preemption. Two fields
will be added to pod spec:

```go
// PodSpec is a description of a pod
type PodSpec struct {
  ...
  // If specified, indicates the pod's priority. "system" is a special keyword
  // which indicates the highest priority. Any other name must be defined by
  // creating a PriorityClass object with that name.
  // If not specified, the pod priority will be zero.
  // +optional
  PriorityClassName string
  // The priority value which is resolved by the Admission Controller from
  // PriorityClassName. The higher the value, the higher the priority.
  // It must not be specified by user.
  Priority *int32
}
```

And a new scheduling API will be added to scheduling api group:

```
// PriorityClass defines the mapping from a priority class name to the priority
// integer value. The value can be any valid integer.
type PriorityClass struct {
  metav1.TypeMeta
  // +optional
  metav1.ObjectMeta

  // The value of this priority class. This is the actual priority that pods
  // receive when they have the name of this class in their pod spec.
  Value int32
}

// PriorityClassList is a collection of priority classes.
type PriorityClassList struct {
  metav1.TypeMeta
  // +optional
  metav1.ListMeta

  // Items is the list of PriorityClasses.
  Items []PriorityClass
}
```

A few notes:
- Pod references a PriorityClaas through pod.Spec.PriorityClassName, and this is resolved during
  apiserver admission control (a new admission controller). If no PriorityClass is specified, it
  will default to zero in the first version; in later version, a default priority class will be
  created with annotation, just like default storage class.
- PriorityClass is not allowed to be updated, but it's possible to just delete it and create a new
  one with the same name. Kubernetes doesn't check for this, but it is discouraged. Deletion is
  allowed despite the fact that there may be existing pods that have specified such priority class
  names in their pod spec.
- At last, there's quite a few interactions between priority and QoS classes. Kubernetes has three
  QoS classes which are derived from request and limit of pods. Priority is introduced as an
  independent concept; meaning that any QoS class may have any valid priority. When a node is out
  of resources and pods needs to be preempted, we give priority a higher weight over QoS classes. In
  other words, we preempt the lowest priority pod and break ties with some other metrics, such as,
  QoS class, usage above request, etc. This is not finalized yet.
- By default, only one default priority class can exist. But in case of multiple ones exist (due to
  race condition, etc), kubernetes will return the one with lowest priority value (smallest number).

*Update on 10/27/2017, v1.8, alpha*

The feature reaches alpha in kubernetes 1.8, ref [updated proposal](https://github.com/kubernetes/community/blob/a616ab2966ce4caaf5e9ff3f71117e5be5d9d5b4/contributors/design-proposals/scheduling/pod-priority-api.md).

*Update on 03/10/2018, v1.10, alpha*

The feature is still alpha in kubernetes 1.10, ref [tracking issue](https://github.com/kubernetes/kubernetes/issues/57471).

*Update on 06/13/2018, v1.11, beta*

The feature reaches beta in kubernetes 1.11.

*References*
- https://github.com/kubernetes/community/pull/604

## pod preemption

*Date: 06/23/2018, v1.11, beta*

Pod preemption is the process where kubernetes scheduler tries to preempt lower priority pods to
make room for higher priority pods (the feature comes after priority API design). Note that preemption
is orthogonal from kubelet eviction, where kubelet kills a pod on a node because that particular node
is running out of resources. The only senario pod preemption happens is when higher priority pods
cannot be scheduled due to unmet requirements, including resource requirement, affinity/anti-affinity
rules, etc.

Scheduler is choosen to implement the preemption logic (instead of another controller or kubelet),
because we want to have a central place to implement the scheduling logic and also reduce the
possibility of race condition (race condition can also happen if we have multiple scheduler, but
it's a different issue).

Preemption order: scheduler preempts based on priority first, then break ties based on QoS, etc. In
addition, scheduler will choose to evit pods on a node where the number and/or priority of victims
(evicted pods) is smallest. After a node is choosen, scheduler considers the lowest priority pods
for preemption first.
- Among pods with equal priority the pods are ordered by their QoS class: Best Effort, Burstable, Guaranteed.
- Scheduler respects pods' disruption budget when considering them for preemption.
- Scheduler will try to minimize the number of preempted pods.
- Scheduler does not have the knowledge of resource usage of pods.

Eviction works independently with preemption. For example, from scheduler's point of view, BestEffort
pods are less likely to be evicted since it has 0 resource request, preempting them will not provide
more resource for pending high priority pods (let's only consider resource here, ignoring other factors
like affinity). Consider the scenario where we have a Burstable pod and a BestEffort pod running on
a node. Scheduler will preempt the Burstable pod for reason mentioned above; however, if resource
usage on the node is quite high, then the BestEffort pod will be evicted by kubelet.

Starvation problem. Right now, there is only a FIFO queue for pending pods in scheduler. If a pod
can't be scheduled, it will be put back to the end of the FIFO queue. However, using this approach
can starve the high priority pod; that is, after we put the pod to end of queue, the room made from
evicted pod can be taken up by other pending pods in the queue. To solve the problem, the scheduling
algorithm is changed to use a priority queue (heap) and a list of unschedulable pods. In addition,
nodes that have preempted pods for a high priority pod are said to be nominated by the high priority
pod, to avoid other pods from scheduling on it; other parts of the scheduling logic will respect the
nomination. *(Side Note, in golang, the scheduler is also a FIFO queue, lacking the notion of priority).*

Scheduler preemption will support PDB for beta, but respecting PDB is not guaranteed. Preemption
will try to avoid violating PDB, but if it doesn't find any lower priority pod to preempt without
violating PDB, it goes ahead and preempts victims despite violating PDB. This is to guarantee that
higher priority pods will always get precedence over lower priority pods in obtaining cluster
resources.

Inter-pod affinity on lower priority pods. The above scheduler algorithm will evict lower priority
pods to make room for high priority pods. However, if a high priority pod has dependency on low
priority pods, scheduler logic can be quite complex, to avoid evicting dependant low priority pods.
In addition, such a dependency is probably not desired in most realistic scenarios, thus the feature
is not implemented right now.

Cross node preemption? When a pod P is not schedulable on a node N even after removal of all lower
priority pods from node N, there may be other pods on other nodes that are not allowing it to
schedule, e.g. rack/zone anti-affinity, local resources, etc. Scheduler has to do an exhaustive
search to find the pods to evict, which can be very expensive, thus the feature is not implemented
right now.

*References*
- [design doc](https://github.com/kubernetes/community/blob/d251c97aff20fe94fea9761a2ce9b922e6b68239/contributors/design-proposals/scheduling/pod-preemption.md)

## pod priority quota

*Date: 06/23/2018, v1.11, alpha*

Apart from priority API design above, a new design, priority resource quota is added (as part of the
ResourceQuota API). Since we already have priority field in Pod spec, Pods can now be classified
into different priority classes.

We would like to be able to create quota for various priority classes in order to manage cluster
resources better and limit abuse scenarios. The link above has detailed design and user story; in
short, the existing `scope` field in ResourceQuota API will be extended to consider pod priority.
The resource quota scope is used to filter objects matching the quota, so naturally, we add the
priority info into quota scope so it will match pods of specific priority, etc.

*References*
- [design doc](https://github.com/kubernetes/community/blob/99e4e741f8c488e427e6b8398b0cf55c6c8ad306/contributors/design-proposals/scheduling/pod-priority-resourcequota.md)

## scheduler extender

*Date: 08/03/2018, v1.11*

When scheduling a pod, the extender allows an external process to filter, prioritize nodes, as well
as preempt pods on nodes. Three separate http/https calls are issued to the extender:
- one for `filter`
- one for `prioritize`
- one for `preempt`

Additionally, the extender can choose to bind the pod to apiserver by implementing the `bind` action.
Note the design doc is a bit outdated, it doesn't mention the `preempt` action.

*References*
- [design doc](https://github.com/kubernetes/community/blob/184c105667bd340fdb8a3dfaabe9a7a1d0346988/contributors/design-proposals/scheduling/scheduler_extender.md)

## multi-scheduler

*Date: 04/03/2017, v1.6*

Kubernetes ships with a default scheduler; if the default scheduler does not suit your needs you can
implement your own scheduler. Not just that, you can even run multiple schedulers simultaneously
alongside the default scheduler and instruct Kubernetes what scheduler to use for each of your pods.
Custom schedulers must conform to kubernetes scheduler API, i.e. the scheduler must have a scheduler
name, and respect `pod.spec.schedulerName`.

A couple of design considerations in multi-scheduler:
- Different schedulers are essentially separated processes. When all schedulers try to schedule their
  pods onto the nodes, there might be conflicts. Current solution is to let Kubelet to do the conflict
  check and if the conflict happens, effected pods would be put back to scheduler and waiting to be
  scheduled again.
- All schedulers must use predicate functions that are at least as strict as the ones that Kubelet
  applies when deciding whether to accept a pod, otherwise Kubelet and scheduler may get into an
  infinite loop where Kubelet keeps rejecting a pod and scheduler keeps re-scheduling it back the
  same node. To make it easier for people who write new schedulers to obey this rule, we will create
  a library containing the predicates Kubelet uses.
- Scheduler must not claim Pods that it is not responsible for.

Note there are a couple of other approaches to extend scheduler:
- (This proposal) Write your own scheduler and run it along with Kubernetes native scheduler.
- (Scheduler extender) Use the http callout approach
- Recompile the scheduler with a new policy
- Restart the scheduler with a new scheduler policy config file
- Or maybe in future dynamically link a new policy into the running scheduler

*References*
- [design doc](https://github.com/kubernetes/community/blob/0f7cc84c83867f6dd5cb241e7e2a69687ca7d796/contributors/design-proposals/multiple-schedulers.md)
- https://kubernetes.io/docs/tutorials/clusters/multiple-schedulers/

## scheduler framework, aka, scheduler v2

*Date: 08/03/2018, v1.11, design*

The proposal lists a bunch of limitations in current scheduler:
- there's limited extension points (only post filter and post scoring), which means it's harder to
  extend the scheduler and all changes must be compiled in default scheduler
- scheduler extender is slow with http & json
- there's no feedback from scheduler to extender about scheduling failure
- scheduler extender cannot share cache with default scheduler

A new scheduler framework is proposed to solve the problems; at its core is a bunch of extension
points, which can be in-process using golang plugin or out-of-process using http & json. The
extension points are:
- scheduling queue sort
- pre-filter: Only Pod is passed to the plugins, used to check certain required conditions.
- filter: The plugins filter out Nodes that cannot run the Pod.
- post-filter: The Pod and the set of nodes that can run the Pod are passed to these plugins.
- scoring: The plugins are utilized to rank nodes that have passed the filtering stage.
- post-scroing: The Pod and the chosen node are passed to these plugins.
- [reserve]: NOT a plugin, but a phase in scheduler framework to reserve the chosen Node for the Pod.
- admit: The plugins run in a separate go routine to return admit result - admin, reject and wait.
- reject: Plugins registered here are called if the reservation of the Pod is cancelled to undo any changes made in admit phase.
- pre-bind: These plugins run before the actual binding of the Pod to a Node happens.
- bind: These plugins run when binding the Pod; once a true is returned the remaining plugins are skipped.
- post-bind: The Post Bind plugins can be useful for housekeeping after a pod is scheduled.

*References*
- https://github.com/kubernetes/community/pull/2281

## taint node by conditions

*Date: 07/28/2017, v1.7*

Currently, node conditions are patched via kubelet and node controller. The information is furthur
used by other components, e.g. scheduler filters out nodes with condition `NetworkUnavailable=True`.
However, this is not optimal as user might want to schedule pod to that node, e.g. for troubleshotting
issues. The proposal aims to solve the issue via tainting node using node condition, users can then
use tolerations to improve scheduling capability.

- [design doc](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/scheduling/taint-node-by-condition.md)
- https://github.com/kubernetes/community/pull/819

## schedule daemonset pod by default scheduler

*Date: 03/23/2018, v1.9, design*

As of 1.9, Kubernetes daemonset controller contains scheduling logic; it uses scheduler logic to
determine node feasibility (e.g. PodFitHosts), and directly set `pod.spec.hostName`, which bypasses
default scheduler. The reason for this origial design is that:
- run on every node is a special scheduling case and scheduler is rather simple at that point
- it is common to run daemonset even when node is not ready or scheduler is not running; coding the
  scheduling logic into daemonset greatly simplifies things

There was discussion to move scheduling logic from daemonset into scheduler, but was then rejected
because of two problems:
- scheduler can be swapped out; how do we make sure replacement scheduler work as expected for daemonset
- how to solve the problem where critical pods must run on nodes even if nodes are not ready

The issue was closed, but was then later brought up again, because as mentioned in the proposal, this
design (scheduling logic in daemonset) has introduced a lot of problems, mostly due to increasingly
complicated scheduler primitives. The solutions to the above problems:
- there is a lot of potential ways for cluster admin to break things: broken replacement scheduler
  is just one of them. The plan is probably to provide scheduler conformance test to make sure
  replacement scheduler works as expected
- to make sure critical pods can land on unready nodes, unready nodes will be tainted with certain
  taints; and daemonset controller is responsible to add toleration to pods
- sig-scheduling is working on priority/preemption feature in default scheduler, daemonset controller
  can leverage this feature to make sure critical pods can run on desired nodes; otherwise, deamonset
  controller has to add preemption logic itself

Implementation-wise, daemonset controller will use node affinity feature to schedule pods. For large
cluster, it takes quite a few minutes; but Kubernetes chooses to stay with that, and will optimize
it later.

*Update on 10/04/2018, v1.12.0*

DaemonSet pods, which used to be scheduled by the DaemonSet controller, will be scheduled by the
default scheduler in 1.12. This change allows DaemonSet pods to enjoy all the scheduling features of
the default scheduler.

*References*
- [design doc](https://github.com/kubernetes/community/blob/01a70cd13341130a0f0206e264e5a32a011ae371/contributors/design-proposals/scheduling/schedule-DS-pod-by-scheduler.md)
- https://github.com/kubernetes/kubernetes/issues/42002
- https://docs.google.com/document/d/1v7hsusMaeImQrOagktQb40ePbK6Jxp1hzgFB9OZa_ew/edit

## node affinity

*Date: 05/11/2017, v1.6*

Compared with pod affinity feature, node affinity is relatively easy. It has three variants:
- RequiredDuringSchedulingRequiredDuringExecution
- RequiredDuringSchedulingIgnoredDuringExecution
 - PreferredDuringSchedulingIgnoredDuringExecution

Each has its own meaning based on scheduling time and execution time. Once the constraints are
defined, we can use NodeSelectorRequirement to select nodes, i.e. `<Key Operator Values>`. For more
details, see experiments/scheduling.

*References*
- [design doc](https://github.com/kubernetes/community/blob/release-1.6/contributors/design-proposals/nodeaffinity.md)
- https://kubernetes.io/docs/concepts/configuration/assign-pod-node/

## pod affinity/anti-affinity

*Date: 04/03/2017, v1.6*

One of the core ideas of pod affinity/anti-affinity is `topologyKey`: it's just a fancy term for a
node label, which represents topological domain, i.e. same node, same rack, same zone, same power
domain, etc. For example, a topology key can be `topologyKey: failure-domain.beta.kubernetes.io/zone`,
and this will target nodes with label `failure-domain.beta.kubernetes.io/zone: $VALUE`, where `$VALUE`
is nodes' failure-domain. Scheduler will use the value to make schedule decision; e.g. to schedule
pods across failure-domain, scheduler will choose pods with different `$VALUE`. Following is a
concrete example:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-pod-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: security
            operator: In
            values:
            - S1
        topologyKey: failure-domain.beta.kubernetes.io/zone
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: security
            operator: In
            values:
            - S2
        topologyKey: kubernetes.io/hostname
  containers:
  - name: with-pod-affinity
    image: gcr.io/google_containers/pause:2.0
```

The above yaml has two pod affinity constraints.
- The first is podAffinity, which means we can schedule the pod on a node only if the node has a
  label with key: `failure-domain.beta.kubernetes.io/zone`, and among all nodes with the same label
  (key/value pair), at least one pod has label `security=S1`.
- The second topologyKey is `failure-domain.beta.kubernetes.io/hostname` , which means the pod can
  only run on a node if the node has a pod running with label `security=S1`, as opposed to a range
  of nodes in the same zone. For more details, see experiments/scheduling.

There are a couple of takeaways from the design proposal:
- RequiredDuringScheduling anti-affinity is symmetric. That is, if pod P has anti-affinity rule saying
  "do not run me on nodes that are running pod Q", then it is not sufficient to check anti-affinity
  rule when scheduling P - it is also necessary to check the rule when scheduling Q to make sure it
  is not scheduled on node running P.
- RequiredDuringScheduling affinity is not symmetric. That is, if pod P has affinity rule saying "run
  me on nodes that are running pod Q", then it is not required to schedule Q on nodes running P as
  well; however, kubernetes scheduler will prefer nodes running P if possible.
- PreferredDuringScheduling is symmetric.
- There is a corner case that if we want to spread pods of a service using affinity, then the first
  pod is unable to be scheduled since there is no pod matching the affinity in the cluster. Current
  solution is to have the scheduler use a rule that if the `RequiredDuringScheduling` affinity
  requirement matches a pod's own labels, and there are no other such pods anywhere, then disregard
  the requirement (there is race condition if when running multiple schedulers).
- For anti-affinity, a pod with too broad rule will potentially prevent other pods from running in
  the cluster. Current solution is to limit anti-affinity rule to only use node as topology key
  (using adminssion controller). A more standard approach is to use quota, and instead of charging
  requested quota, scheduler will also charge for `opportunity cost`. For example, if a pod has
  anti-affinity rules against all other pods on a node, then it will be charged for all resources
  of the node it is running. This is only mentioned in the proposal, not yet implemented.
- Co-existing with daemons. A cluster administrator may wish to allow pods that express anti-affinity
  against all pods, to nonetheless co-exist with system daemon pods, such as those run by DaemonSet.
  This is planned to implement inside scheduler to exclude a certain namespace when considering
  affinity rules (not implemented however). An alternative is to add 'toleration' kind of API, but
  this will complicate things.
- If `RequiredDuringSchedulingRequiredDuringExecution` is set, kubernetes must decide which pod to
  kill and for how long it needs to wait. For the first question, kubernetes kill the pod with
  affinity rule; for the second question, whichever component does the killing will decide the time.

*References*
- [design doc](https://github.com/kubernetes/community/blob/release-1.6/contributors/design-proposals/podaffinity.md)

## taint, toleration and dedicated nodes

*Date: 06/22/2018, v1.10, ga*

A taint is a new type that is part of the NodeSpec; when present, it prevents pods from scheduling
onto the node unless the pod tolerates the taint (tolerations are listed in the PodSpec).

Future work:
- At present, the Kubernetes security model allows any user to add and remove any taints and
  tolerations (Note, the proposal is old, right now we can use RBAC to prevent user from modifying
  node object).
- Another security vulnerability arises if nodes are added to the cluster before receiving their
  taint. Thus we need to ensure that a new node does not become "Ready" until it has been configured
  with its taints.

*References*
- [design doc](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/design-proposals/scheduling/taint-toleration-dedicated.md)

## scheduler equivalence class

*Date: 06/23/2018, v1.10, alpha*

Pods in Kubernetes cluster usually have identical requirements and constraints, e.g. Deployment with
a number of replicas. So rather than determining feasibility for every pending pod on every node, we
only do predicates one pod per equivalence class - a group of tasks with identical requirements, and
reuse the predicate results for other equivalent pods. Equivalence class is a proven feature in borg.

The key design points here are:
- Use controller reference (owner reference) to define equivalence class, i.e. pods with the same
  controller reference are treated as equivalence class.
- Since cluster state change frequently, it would be infeasible to cache the result based solely on
  node; instead, the proposal uses a three layer cache: `nodename -> predicates -> equivalencehash`.
  To find a cached result, scheduler will give name of the node, what kind of predicate to evaluate
  (e.g. affinity rules) and what equivalence class the pod belongs to.

The feature is still alpha in Kubernetes v1.10, since bugs in the feature will have large impact and
upstream doesn't have much confidence right now (even though the feature was added two years ago).
It is targed to move to beta in v1.12.

*Update on 10/05/2018, v1.12, alpha*

Due to performance reason, the three level cache has been changed to two level cache, ref [PR](https://github.com/kubernetes/kubernetes/pull/65714).
Note the caching schema does not change, Kubernetes still uses `nodename -> predicate -> equivalencecache`,
but instead of using a single large cache to cache the results, it uses cache per node, e.g. looking
up cache result changes from:
```go
value, ok = c.cache[nodeName][predicateKey][equivalenceHash]
```

to:
```go
value, ok = n.cache[predicateKey][equivalenceHash]
```

where `c.cache` is a single cache, whereas `n.cache` is per node cache. The change minimizes lock
usage and uses r/w lock instead of mutex lock to improve performance.

*References*
- [design doc](https://github.com/kubernetes/community/blob/d3879c1610516ca26f2d6c5e1cd3f4d392fb35ec/contributors/design-proposals/scheduling/scheduler-equivalence-class.md)

## scheduler policy via configmap

*Date: 06/13/2018, v1.10, beta*

The feature allows kubernetes scheduler to pick up its config from configmap. The proposal choose to
use configmap (instead of reading config from local config  file), because this makes it easy to run
self-hosted scheduler, since in hosted solution, it's not easy for pod to access local disk. The
design chooses to change scheduler code to watch configmap. An alternative approach mentioned in the
design doc is to use a sidecar to pick up the configmap.

*References*
- https://docs.google.com/document/d/19AKH6V6ejOeIvyGtIPNvRMR4Yi_X8U3Q1zz2fgTNhvM/edit
- https://github.com/kubernetes/features/issues/374

## per-pod-configurable eviction behavior

*Date: 04/03/2017, v1.6, alpha*

Kubernetes 1.6 has alpha support for representing node problems as taints (currently only "node
unreachable" and "node not ready", corresponding to the NodeCondition "Ready" being "Unknown" or
"False" respectively) . When the `TaintBasedEvictions` alpha feature is enabled. You can do this
by including `TaintBasedEvictions=true` in `--feature-gates`, e.g.
```
--feature-gates=FooBar=true,TaintBasedEvictions=true
```

The taints are automatically added by the NodeController and the normal logic for evicting pods from
nodes based on the Ready NodeCondition is disabled. For example, an application with a lot of local
state might want to stay bound to node for a long time in the event of network partition, in the
hope that the partition will recover and thus the pod eviction can be avoided. The toleration the
pod would use in that case would look like:

```yaml
tolerations:
- key: "node.alpha.kubernetes.io/unreachable"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 6000
```

Note that Kubernetes automatically adds a toleration for `node.alpha.kubernetes.io/notReady` with
tolerationSeconds=300 unless the pod configuration provided by the user already has a toleration for
`node.alpha.kubernetes.io/notReady`. Likewise it adds a toleration for `node.alpha.kubernetes.io/unreachable`
with tolerationSeconds=300 unless the pod configuration provided by the user already has a toleration
for `node.alpha.kubernetes.io/unreachable`.

These automatically-added tolerations ensure that the default pod behavior of remaining bound for
5 minutes after one of these problems is detected is maintained. The two default tolerations are
added by the `DefaultTolerationSeconds` admission controller.

*References*
- https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/#taint-based-evictions

## scheduler binding

*Date: 07/01/2018, v1.11*

As of v1.11, scheduler selects all pods whose status is not Succeeded or PodFailed:

```go
// 'pkg/scheduler/factory/factory.go'

// NewPodInformer creates a shared index informer that returns only non-terminal pods.
func NewPodInformer(client clientset.Interface, resyncPeriod time.Duration) coreinformers.PodInformer {
  selector := fields.ParseSelectorOrDie(
    "status.phase!=" + string(v1.PodSucceeded) +
      ",status.phase!=" + string(v1.PodFailed))
  lw := cache.NewListWatchFromClient(client.CoreV1().RESTClient(), string(v1.ResourcePods), metav1.NamespaceAll, selector)
  return &podInformer{
    informer: cache.NewSharedIndexInformer(lw, &v1.Pod{}, resyncPeriod, cache.Indexers{cache.NamespaceIndex: cache.MetaNamespaceIndexFunc}),
  }
}
```

Note before v1.11, scheduler only watches pods it is responsible for, but this is not correct, see
[issue](https://github.com/kubernetes/kubernetes/issues/63002). To simply put, scheduler must watch
all the pods of the cluster, including those scheduled by other schedulers in order to update its
cache of the state of the cluster.

For all informed pods, scheduler only schedules those with empty `pod.Spec.NodeName` and
`pod.spec.SchedulerName` set to its name. Once scheduler finds a node via `predicate & priority`
function, it will create a `Binding` objects (v1.Binding or pod/binding; the former one is deprecated
in favor of pod subresource). In pod registry, apiserver will extract pod and binding object, and set
pod node name based on binding object, see `pkg/registry/core/pod/storage`.

# PRs

## [scheduling with volume count](https://github.com/kubernetes/kubernetes/pull/60525)

*Date: 04/02/2018, v1.10*

The feature description is "Balanced resource allocation priority to include volume count on nodes".
Right now, only cpu, memory utilization are considered in `balanced_resource_allocation` priority,
the feature also counts in volume count, to better utilize disk and network (for network storage)
bandwidth.

## [scheduler performance improvement for affinity/anti-affinity](https://github.com/kubernetes/kubernetes/pull/62211)

Affinity/anti-affinity predicate was checking all pods of the cluster for each node in the cluster
to determine feasibility of affinity/anti-affinity terms of the pod being scheduled. This optimization
first finds all the pods in a cluster that match the affinity/anti-affinity terms of the pod being
scheduled once and stores the metadata (the `affinity/anti-affinity terms` here means labelSelector
and namespaces fields in `PodAffinityTerm` defined as part of pod API; scheduler cache this information
for later usage). Scheduler predicate then only checks the topology of the matching pods for each
node in the cluster.
