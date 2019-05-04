## Kubernetes priority and preemption (v1.11, beta)

#### High priority pod preempts low priority pod

Run local cluster:

```
ENABLE_POD_PRIORITY_PREEMPTION=true ALLOW_PRIVILEGED=true ./hack/local-up-cluster.sh -O
```

Create two priority classes:

```
kubectl create -f low-class.yaml
kubectl create -f high-class.yaml
```

Now create a low priority pod:

```
kubectl create -f low-pod.yaml
```

The low priority pod has anti-affinity to pods without 'env:test' label; however,
it will still be preempted by high priority pod:

```
kubectl create -f high-pod.yaml
```

Note 'low-pod' has anti-affinity rules applied to 'default' and 'abc' namespaces;
if we create 'high-pod' in 'abc' namespace, 'low-pod' will still be preempted, i.e.
preemption crosses namespaces.

#### Priority class quota (alpha)

Clean up the above environment and run local cluster:

```
FEATURE_GATES=AllAlpha=true ALLOW_PRIVILEGED=true ./hack/local-up-cluster.sh -O
```

Create two priority classes:

```
kubectl create -f low-class.yaml
kubectl create -f high-class.yaml
```

Create a quota for high priority class pods:

```
kubectl create -f quota.yaml
```

Now create high priority pod and normal pod, observe the output:

```
kubectl create -f high-pod.yaml
kubectl create -f normal-pod.yaml
```

Only high priority pods are counted against quota.
