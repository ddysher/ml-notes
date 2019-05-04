```go
type NodeStatus struct {
    // NodePhase is the current lifecycle phase of the Node, one of "Pending", "Running" and "Terminated".
    Phase     NodePhase
    Conditions []NodeCondition
}

type NodePhase string

type NodeConditionKind string

const (
  NodeReachable   NodeConditionKind = "Reachable"
  NodeLive        NodeConditionKind = "Live"
  NodeReady       NodeConditionKind = "Ready"
  NodeSchedulable NodeConditionKind = "Schedulable"
  NodeRunnable    NodeConditionKind = "Runnable"
)

type NodeCondition struct {
  Kind NodeConditionKind
  Status string // possible values: true, false, unknown
  LastTransitionTime util.Time
  Reason string
  Message string
}
```

Question:
1. At any given time, do we want to keep all of the five condition information of the a Node? For example, if a Node is just launched, then Reachable=False, Live=True, Ready=False, Schedulable=False, Runnable=False, instead of just Live=True. I think it's better to have all five states. If so, then it's easier to change Conditions field to type map[string]NodeCondition.

2. Currently, we only have a little information regarding the status of a Node. I'v opened an issue about creating a varz package. Before we made an agreement on how to export more information, we 'll just start with a subset of the conditions: Reachable/Unreachable (connection succeed or not), and Ready/NotReady (status ok or not).

3. Difference between Reachable vs Live vs Ready vs Schedulable vs Runnable? The boundary seems blurred, we need to carefully define these state.

4. You said "The running phase may be populated based on condition, but the terminated phase should not be." I dont know why terminated phase shouldn't be populated by condition. Isn't terminated state also decided by the condition of Node?

Only Reachable / Live

ICMP ping for reachable

forgiveness override (waiting longer for task to start on other minion)

Condition (current status, always 'Running').

git tag


<!-- Hints -->
1. Use pkg/master/pod_cache.go for hint.
2. pkg/master/ip_cache.go should go away once we push status.
3. If nothing changes, do not push!
4. Clear HostIP if node goes down (not just update condition).


1. We have to push node status every time we did a probe, because last probe time will always change.

Hard to get it right, reconcile kubelet and node controller
If we really have kubelt publish nodestatus, with self-hosting, we can do that in a pod with different container

Need the status patch one to land in first

spec


node controller doesn't have the knowledge to decicde (no usage info)
