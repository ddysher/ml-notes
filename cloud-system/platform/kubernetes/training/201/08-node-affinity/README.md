## Kubernetes node affinity (As of k8s 1.6, feature beta)

#### Run two nodes

```sh
NAME            STATUS    AGE       VERSION                             LABELS
127.0.0.1       Ready     9m        v1.7.0-alpha.2.838+fe9361ffe38eac   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=127.0.0.1
192.168.33.33   Ready     8m        v1.7.0-alpha.2.838+fe9361ffe38eac   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=192.168.33.33
```

#### Run a pod with node affinity

This pod has node affinity can't be satisfied via current nodes:

```sh
$ kubectl create -f pod-with-node-affinity-1.yaml
pod "with-node-affinity-1" created

$ kubectl get pods
NAME                   READY     STATUS    RESTARTS   AGE
with-node-affinity-1   0/1       Pending   0          2s

$ kubectl describe pods with-node-affinity-1
Name:           with-node-affinity-1
Namespace:      default
...
Events:
  FirstSeen     LastSeen        Count   From                    SubObjectPath   Type            Reason                  Message
  ---------     --------        -----   ----                    -------------   --------        ------                  -------
  15s           0s              6       default-scheduler                       Warning         FailedScheduling        No nodes are available that match all of the following predicates:: MatchNodeSelector (2).
```

#### Run another pod with node affinity

This pod will be able to schedule to 127.0.0.1:

```sh
$ kubectl create -f pod-with-node-affinity-2.yaml
pod "with-node-affinity-2" created

$ kubectl get pods -o wide
NAME                   READY     STATUS    RESTARTS   AGE       IP           NODE
with-node-affinity-1   0/1       Pending   0          16m       <none>
with-node-affinity-2   1/1       Running   0          14s       172.17.0.3   127.0.0.1
```

#### Run pod with preferred affinity

This pod will be able to schedule to one node, even if affinity doesn't match:

```sh
$ kubectl create -f pod-with-node-affinity-3.yaml
pod "with-node-affinity-3" created

$ kubectl get pods -o wide
NAME                   READY     STATUS    RESTARTS   AGE       IP           NODE
with-node-affinity-1   0/1       Pending   0          11m       <none>
with-node-affinity-2   1/1       Running   0          13m       172.17.0.3   127.0.0.1
with-node-affinity-3   1/1       Running   0          8m        172.17.0.2   192.168.33.33
```

#### Run pod with multiple preferred affinity

This pod will be scheduled to preference with higher score:

```sh
$ kubectl create -f pod-with-node-affinity-4.yaml
pod "with-node-affinity-4" created

$ kubectl get pods -o wide
NAME                   READY     STATUS    RESTARTS   AGE       IP           NODE
with-node-affinity-1   0/1       Pending   0          14m       <none>
with-node-affinity-2   1/1       Running   0          15m       172.17.0.3   127.0.0.1
with-node-affinity-3   1/1       Running   0          10m       172.17.0.2   192.168.33.33
with-node-affinity-4   1/1       Running   0          2s        172.17.0.3   192.168.33.33
```
