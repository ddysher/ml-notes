## ResourceQuota scoping

Create namespace and quota:

```
$ kubectl create ns quotans
namespace "quotans" created

$ kubectl create -f quota.yaml
resourcequota "quota-best-effort" created
resourcequota "quota-terminating" created
resourcequota "quota-longrunning" created
resourcequota "quota" created
```

Now even though we have quota for cpu/memory request/limit, we can still create
besteffort pod due to quota scoping:


```
$ kubectl create -f pod.yaml
pod "nginx-besteffort" created

$ kubectl describe quota -n quotans
Name:       quota
Namespace:  quotans
Resource    Used  Hard
--------    ----  ----
pods        1     6


Name:       quota-best-effort
Namespace:  quotans
Scopes:     BestEffort
 * Matches all pods that do not have resource requirements set. These pods have a best effort quality of service.
Resource  Used  Hard
--------  ----  ----
pods      1     2


Name:       quota-longrunning
Namespace:  quotans
Scopes:     NotBestEffort, NotTerminating
 * Matches all pods that have at least one resource requirement set. These pods have a burstable or guaranteed quality of service.
 * Matches all pods that do not have an active deadline. These pods usually include long running pods whose container command is not e
xpected to terminate.
Resource       Used  Hard
--------       ----  ----
limits.cpu     0     4
limits.memory  0     4Gi
pods           0     2


Name:       quota-terminating
Namespace:  quotans
Scopes:     NotBestEffort, Terminating
 * Matches all pods that have at least one resource requirement set. These pods have a burstable or guaranteed quality of service.
 * Matches all pods that have an active deadline. These pods have a limited lifespan on a node before being actively terminated by the
 system.
Resource       Used  Hard
--------       ----  ----
limits.cpu     0     2
limits.memory  0     1Gi
pods           0     2
```
