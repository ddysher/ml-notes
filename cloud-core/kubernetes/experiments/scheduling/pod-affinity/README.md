## Kubernetes pod affinity (v1.6, beta)

#### Run two nodes

```sh
$ kubectl get nodes --show-labels
NAME            STATUS    AGE       VERSION                             LABELS
127.0.0.1       Ready     3h        v1.7.0-alpha.2.838+fe9361ffe38eac   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=127.0.0.1
192.168.33.33   Ready     3h        v1.7.0-alpha.2.838+fe9361ffe38eac   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=192.168.33.33
```

#### Run a pod with pod affinity

This pod has pod affinity can't be satisfied via current nodes due to:
  - no suitable topologyKey
  - no affinity pods

```sh
$ kubectl create -f pod-affinity-1.yaml
pod "with-pod-affinity-1" created

$ kubectl describe pods with-pod-affinity-1
Name:           with-pod-affinity-1
Namespace:      default
...
Events:
  FirstSeen     LastSeen        Count   From                    SubObjectPath   Type            Reason                  Message
  ---------     --------        -----   ----                    -------------   --------        ------                  -------
  25s           10s             6       default-scheduler                       Warning         FailedScheduling        No nodes are available that match all of the following predicates:: MatchInterPodAffinity (2).
```

#### Run another pod with pod affinity

This pod has pod affinity can't be satisfied via current nodes due to
  - no affinity pods

```sh
$ kubectl create -f pod-affinity-2.yaml
pod "with-pod-affinity-2" created

$ kubectl describe pods with-pod-affinity-2
Name:           with-pod-affinity-2
Namespace:      default
xxx
Events:
  FirstSeen     LastSeen        Count   From                    SubObjectPath   Type            Reason                  Message
  ---------     --------        -----   ----                    -------------   --------        ------                  -------
  3s            3s              2       default-scheduler                       Warning         FailedScheduling        No nodes are available that match all of the following predicates:: MatchInterPodAffinity (2).
```

#### Run pod with pod affinity that can be satisfied

We first create a pod `pod-with-label`, which has label "environment=prod". In
the affinity section, we say topologyKey is "kubernetes.io/hostname", which means
kubernetes will schedule out affinity pod to a node where `pod-with-label` is
running.

```sh
$ kubectl create -f pod.yaml
pod "pod-with-label" created

$ kubectl create -f pod-affinity-3.yaml
pod "with-pod-affinity-3" created

$ kubectl get pods -o wide
NAME                  READY     STATUS    RESTARTS   AGE       IP           NODE
pod-with-label        1/1       Running   0          55s       172.17.0.2   192.168.33.33
with-pod-affinity-1   0/1       Pending   0          14h       <none>
with-pod-affinity-2   0/1       Pending   0          3m        <none>
with-pod-affinity-3   1/1       Running   0          2s        172.17.0.3   192.168.33.33
```

#### Run pod with different topologyKey

Continuing the above example, we can label each node with a zone label, thus
kubernetes can schedule pod to any nodes with the label (since we alreay have
`pod-with-label` running in the zone. It doesn't matter if the exact node has
the pod running). As can be seen below, `with-pod-affinity-4` runs on node
127.0.0.1 even though `pod-with-label` runs on node 192.168.33.33.

```sh
$ kubectl label nodes 127.0.0.1 failure-domain.beta.kubernetes.io/zone=cn_east
node "127.0.0.1" labeled

$ kubectl label nodes 192.168.33.33 failure-domain.beta.kubernetes.io/zone=cn_east
node "192.168.33.33" labeled

$ kubectl get nodes --show-labels
NAME            STATUS    AGE       VERSION                             LABELS
127.0.0.1       Ready     18h       v1.7.0-alpha.2.838+fe9361ffe38eac   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,failure-domain.beta.kubernetes.io/zone=cn_east,kubernetes.io/hostname=127.0.0.1
192.168.33.33   Ready     18h       v1.7.0-alpha.2.838+fe9361ffe38eac   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,failure-domain.beta.kubernetes.io/zone=cn_east,kubernetes.io/hostname=192.168.33.33

$ kubectl create -f pod-affinity-4.yaml
pod "with-pod-affinity-4" created

$ kubectl get pods -o wide
NAME                  READY     STATUS    RESTARTS   AGE       IP           NODE
pod-with-label        1/1       Running   0          17m       172.17.0.2   192.168.33.33
with-pod-affinity-1   0/1       Pending   0          14h       <none>
with-pod-affinity-2   0/1       Pending   0          20m       <none>
with-pod-affinity-3   1/1       Running   0          16m       172.17.0.3   192.168.33.33
with-pod-affinity-4   1/1       Running   0          5s        172.17.0.3   127.0.0.1
```

#### Anti-affinity works similar to affinity
