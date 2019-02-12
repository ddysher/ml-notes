## Kubernetes local PV fsgroup check

https://github.com/kubernetes/kubernetes/issues/45053

The PV/PVC controller will not bind PVC's that request a storageclass with a topologyKey specified.

I0505 13:51:33.059749    1215 local_volume.go:205] LocalVolume mount setup: PodDir(/var/lib/kubelet/pods/e4727568-3156-11e7-893b-8825937fa049/volumes/kubernetes.io~local-volume/local-pv-1) VolDir(/tmp/local-pv) Mounted(false) Error(stat /var/lib/kubelet/pods/e4727568-3156-11e7-893b-8825937fa049/volumes/kubernetes.io~local-volume/local-pv-1: no such file or directory), ReadOnly(false)

#### Create a local PV and PVC

```
kubectl create -f local-pv.yaml

kubectl create -f local-pvc.yaml

$ kubectl get pv
NAME         CAPACITY   ACCESSMODES   RECLAIMPOLICY   STATUS    CLAIM             STORAGECLASS   REASON    AGE
local-pv-1   10Gi       RWO           Delete          Bound     default/myclaim   local-fast               3h

$ kubectl get pvc
NAME      STATUS    VOLUME       CAPACITY   ACCESSMODES   STORAGECLASS   AGE
myclaim   Bound     local-pv-1   10Gi       RWO           local-fast     3h
```

Note PVC will bind to a specific PV here (dev stage), later it will be bound only
at schedule time.

#### Create two Pods, fsgroup conflict

```
$ kubectl create pod.yaml

$ stat /tmp/local-pv
  File: '/tmp/local-pv'
  Size: 4096            Blocks: 8          IO Block: 4096   directory
Device: 804h/2052d      Inode: 4982500     Links: 2
Access: (2775/drwxrwsr-x)  Uid: ( 1000/  deyuan)   Gid: ( 1001/ chirico)
Access: 2017-05-05 15:02:02.105212124 +0800
Modify: 2017-05-05 13:38:08.092757088 +0800
Change: 2017-05-05 13:51:33.063618162 +0800
 Birth: -
```

/tmp/local-pv is bound to `/var/lib/kubelet/pods/e4727568-3156-11e7-893b-8825937fa049/volumes/kubernetes.io~local-volume/`

```
$ kubectl create pod-different-fsgroup.yaml

$ stat /tmp/local-pv
  File: '/tmp/local-pv'
  Size: 4096            Blocks: 8          IO Block: 4096   directory
Device: 804h/2052d      Inode: 4982500     Links: 2
Access: (2775/drwxrwsr-x)  Uid: ( 1000/  deyuan)   Gid: ( 1002/quotagrp)
Access: 2017-05-05 17:27:33.963397665 +0800
Modify: 2017-05-05 13:38:08.092757088 +0800
Change: 2017-05-05 17:27:33.963397665 +0800
 Birth: -
```
