## kubernetes local storage isolation (v1.7 alpha)

Local storage isolation is alpha in v1.7, it is graduated to beta in v1.10. There
is significant change since then, see below for updates.

#### Local storage configuration

A matrix of `/var/lib/kubelet` and `/var/lib/docker` being a mountpoint or not.

Case 1: both are mountpoint

```
# Configuration
sda      250G    /
sdb1     1G      /var/lib/docker
sdb2     2G      /var/lib/kubelet

# Reported information
Name:                           node-1
Capacity:
 storage.kubernetes.io/overlay: 999320Ki
 storage.kubernetes.io/scratch: 1998672Ki
```

Case 2: only `/var/lib/docker` is a mountpoint

```
# Configuration
sda      250G    /
sdb1     1G      /var/lib/docker

# Reported information
Name:                   127.0.0.1
Capacity:
 storage.kubernetes.io/overlay: 999320Ki
 storage.kubernetes.io/scratch: 232172536Ki
```

Case 3: only `/var/lib/kubelet` is a mountpoint

```
# Configuration
sda      250G    /
sdb2     2G      /var/lib/kubelet

# Reported information
Name:                           node-1
Capacity:
 storage.kubernetes.io/overlay: 232172536Ki
 storage.kubernetes.io/scratch: 1998672Ki
```

Case 4: both are not mountpoint

```
# Configuration
sda      250G    /

# Reported information
Name:                           node-1
Capacity:
 storage.kubernetes.io/scratch: 232172536Ki
Allocatable:
 storage.kubernetes.io/scratch: 232172536Ki
```

#### Run local cluster with alpha feature gate enabled

For the practice, we make "/var/lib/kubelet" a mount point with small size using
loop device (512MB).

```sh
$ FEATURE_GATES=LocalStorageCapacityIsolation=true ./hack/local-up-cluster.sh
$ kubectl describe nodes 127.0.0.1
Name:                   127.0.0.1
Addresses:
  InternalIP:   127.0.0.1
  Hostname:     127.0.0.1
Capacity:
 cpu:                           4
 memory:                        32834456Ki
 pods:                          110
 storage.kubernetes.io/overlay: 232172536Ki
 storage.kubernetes.io/scratch: 499656Ki
```

This shows our scratch storage is around 487MB, and overlay storage is around 223GB (from /).

#### Run pod with overlay limit

Part of local storage isolation is adding overlay limit support.

```sh
$ kubectl create -f pod-with-overlay-limit.yaml
pod "pod-with-overlay-limit" created

$ kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
pod-with-overlay-limit   1/1       Running   0          7s

$ kubectl exec -it pod-with-overlay-limit bash
root@pod-with-overlay-limit:/# dd if=/dev/zero of=/data bs=512 count=1024000
1024000+0 records in
1024000+0 records out
524288000 bytes (524 MB, 500 MiB) copied, 1.00464 s, 522 MB/s
root@pod-with-overlay-limit:/# exit

$ kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
pod-with-overlay-limit   1/1       Running   0          44s

# After a while, pod gets evicted.
$ kubectl get pods
NAME                     READY     STATUS    RESTARTS   AGE
pod-with-overlay-limit   0/1       Evicted   0          1m
```

#### Run pod with emptydir limit

Similar to overlay, pod with emptydir limit will also got evicted when using
excessive storage:

```
$ kubectl create -f pod-with-emptydir-limit.yaml
pod "pod-with-emptydir-limit" created

$ kubectl get pods
NAME                      READY     STATUS    RESTARTS   AGE
pod-with-emptydir-limit   1/1       Running   0          2s

$ kubectl exec -it pod-with-emptydir-limit bash
00ot@pod-with-emptydir-limit:/# dd if=/dev/zero of=/data/file bs=512 count=102400
1024000+0 records in
1024000+0 records out
524288000 bytes (524 MB, 500 MiB) copied, 1.60744 s, 326 MB/s
root@pod-with-emptydir-limit:/# exit

$ kubectl get pods
NAME                      READY     STATUS    RESTARTS   AGE
pod-with-emptydir-limit   1/1       Running   0          1m

$ kubectl get pods
NAME                      READY     STATUS    RESTARTS   AGE
pod-with-emptydir-limit   0/1       Evicted   0          2m
```

#### Run pod with too large overlay request

Run pod with too large overlay request will result pod keep pending:

```
$ kubectl create -f pod-large-overlay.yaml
pod "pod-large-storage" created

$ kubectl get pods
NAME                READY     STATUS    RESTARTS   AGE
pod-large-storage   0/1       Pending   0          2s

$ kubectl describe pods pod-large-storage
Name:           pod-large-storage
Namespace:      default
Node:           <none>
Labels:         <none>
Annotations:    <none>
Status:         Pending
IP:
Containers:
  nginx:
    Image:      nginx:1.13
    Port:       <none>
    Requests:
      cpu:                              100m
      storage.kubernetes.io/overlay:    4Ti
    Environment:                        <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from default-token-nbkj7 (ro)
Conditions:
  Type          Status
  PodScheduled  False
Volumes:
  default-token-nbkj7:
    Type:       Secret (a volume populated by a Secret)
    SecretName: default-token-nbkj7
    Optional:   false
QoS Class:      Burstable
Node-Selectors: <none>
Tolerations:    node.alpha.kubernetes.io/notReady=:Exists:NoExecute for 300s
                node.alpha.kubernetes.io/unreachable=:Exists:NoExecute for 300s
Events:
  FirstSeen     LastSeen        Count   From                    SubObjectPath   Type            Reason                  Message
  ---------     --------        -----   ----                    -------------   --------        ------                  -------
  6s            5s              3       default-scheduler                       Warning         FailedScheduling        no nodes available to schedule pods
  3s            3s              2       default-scheduler                       Warning         FailedScheduling        No nodes are available that match all of the following predicates:: Insufficient storage.kubernetes.io/scratch (1).
```

#### Run pod with too large scratch request

Run pod with too large scratch request is ok, since 'storage.kubernetes.io/scratch'
is not used for scheduling, see "pod-large-scratch-resource.yaml".

The scratch space exposed from node is used for emptydir size while scheduling, so
"pod-large-scratch-emptydir.yaml" will be pending.
