## Volume Stats

#### Volume

Create Pod with emptyDir:

```
$ kubectl create -f pod-with-emptydir.yaml
pod "pod-with-emptydir" created

$ kubectl exec -it pod-with-emptydir bash
root@pod-with-emptydir:/# dd if=/dev/zero of=/data/index.html bs=512 count=131072
131072+0 records in
131072+0 records out
67108864 bytes (67 MB, 64 MiB) copied, 0.203999 s, 329 MB/s
```

Read metrics from https://localhost:10250/stats/summary.

#### Persistent volume

Create PV, PVC and Pod:

```
$ mkdir /tmp/data
$ kubectl create -f pv-hostpath.yaml
persistentvolume "pv-hostpath" created

$ kubectl create -f pvc.yaml
persistentvolumeclaim "myclaim" created

$ kubectl create -f pod-with-pvc.yaml
pod "mypod" created
```

Now write some data to the volume:

```
$ kubectl exec -it mypod bash
root@mypod:/# dd if=/dev/zero of=/var/www/html/index.html bs=512 count=131072
131072+0 records in
131072+0 records out
67108864 bytes (67 MB, 64 MiB) copied, 0.199466 s, 336 MB/s

$ ls -lh /tmp/data
total 64M
-rw-r--r-- 1 root root 64M Jun 24 15:08 index.html
```
