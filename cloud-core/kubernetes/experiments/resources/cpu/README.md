## Kubernetes cpu manager (v1.10, beta)

Run local cluster with kubelet static cpu policy:

```
KUBELET_FLAGS="--system-reserved=cpu=500m --kube-reserved=cpu=500m --cpu-manager-policy=static" ALLOW_PRIVILEGED=Y ./hack/local-up-cluster.sh -O
```

If we create a guaranteed pod with integer cpu request, we'll see that container
in the pod is allocated fixed cpus and all other containers use different cpus:

```
/sys/fs/cgroup/cpuset/kubepods/{exclusive-pod-id}/{container-id}/cpuset.cpus = 4
/sys/fs/cgroup/cpuset/kubepods/burstable/{normal-pod-id}/{container-id}/cpuset.cpus = 0-3,5-7
```
