## Kubernetes local storage isolation (v1.10 beta)

### Run local cluster with shared partition

Run local cluster with shared partition, i.e. /var/lib/kubelet and /var/lib/docker
are both mounted under '/'.

```
ALLOW_PRIVILEGED=Y ALLOW_SECURITY_CONTEXT=Y ./hack/local-up-cluster.sh -O
```

### Run pod with normal ephemeral storage

For the following pod, writing data in any directory larger that 64Mi will cause
the pod to be evicted by kubelet.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-normal-ephemeral
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    resources:
      requests:
        cpu: 100m
        ephemeral-storage: 64Mi
      limits:
        cpu: 100m
        ephemeral-storage: 64Mi
```

```shell
$ kubectl create -f pod-with-normal-ephemeral.yaml

$ kubectl exec -it pod-normal-ephemeral bash
root@pod-normal-ephemeral:/# ls
bin   data  etc   lib	 lib64	 media	opt   root  sbin  sys  usr
boot  dev   home  lib32  libx32  mnt	proc  run   srv   tmp  var
root@pod-normal-ephemeral:/# dd if=/dev/zero of=output.dat bs=100M count=1
```

After several seconds, the pod will be evicted:

```shell
$ kubectl get pods pod-normal-ephemeral
NAME                   READY     STATUS    RESTARTS   AGE
pod-normal-ephemeral   0/1       Evicted   0          1m
```

If there are multiple containers in the pod, and anyone of them exceeds limit,
the pod will be evicted. For example, if we write data larger than 64Mi to nginx
container, the pod will be evicted.

```
apiVersion: v1
kind: Pod
metadata:
  name: pod-multi-ephemeral
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    resources:
      requests:
        cpu: 100m
        ephemeral-storage: 64Mi
      limits:
        cpu: 100m
        ephemeral-storage: 64Mi
  - name: mysql
    image: mysql:5.7
    resources:
      requests:
        cpu: 100m
        ephemeral-storage: 128Mi
      limits:
        cpu: 100m
        ephemeral-storage: 128Mi
    env:
    - name: MYSQL_ROOT_PASSWORD
      value: "rootpasswd"
```

### Run pod using logs

This pod will be evicted since it has too many logs:

```
apiVersion: v1
kind: Pod
metadata:
  name: pod-logs
spec:
  containers:
  - name: debian
    image: debian:jessie
    command:
    - /bin/sh
    - -c
    - yes "Some text" | head -n 8000000 && sleep 100
    resources:
      requests:
        cpu: 100m
        ephemeral-storage: 64Mi
      limits:
        cpu: 100m
        ephemeral-storage: 64Mi
```

```shell
$ kubectl create -f pod-with-logs.yaml

$ kubectl get pods pod-logs
NAME       READY     STATUS    RESTARTS   AGE
pod-logs   0/1       Evicted   0          1m
```

### Run pod using emptyDir (as well as setting ephemeral-storage)

For the following pod, even if emptyDir size limit is 128Mi, pod will be evicted
if it writes data to '/data' directory larger than 64Mi: ephemeral storage decides
the overall size limit:

```
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-emptydir
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    resources:
      requests:
        cpu: 100m
        ephemeral-storage: 64Mi
      limits:
        cpu: 100m
        ephemeral-storage: 64Mi
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir:
      sizeLimit: 128Mi
```

### Run pod with memory based emptyDir

Running a pod with memory based emptyDir, the size of the volume is still half of
available memory in the system (linux default), not sizeLimit in volume spec:

```
$ kubectl create -f pod-memory-tmpfs.yaml
pod "pod-memory-tmpfs" created

$ kubectl exec -it pod-memory-tmpfs bash
root@pod-memory-tmpfs:/# df -h /scratch
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           7.8G     0  7.7G   0% /scratch
```

However, kubelet will still monitors volume usage and evit pod in case pod exceeds
volume limit:

```
$ kubectl exec -it pod-memory-tmpfs bash
root@pod-memory-tmpfs:/# dd if=/dev/zero of=/scratch/output.dat bs=100M count=1
1+0 records in
1+0 records out
104857600 bytes (105 MB, 100 MiB) copied, 0.0474816 s, 2.2 GB/s
root@pod-memory-tmpfs:/# df -h /scratch
Filesystem      Size  Used Avail Use% Mounted on
tmpfs           7.8G  100M  7.7G   2% /scratch

$ kubectl get pods
NAME               READY     STATUS    RESTARTS   AGE
pod-memory-tmpfs   0/1       Evicted   0          1m
```

### Run local cluster with separate partition

Clean up the above cluster and run local cluster with separate partition:

```
# 512MiB root partition
sudo dd if=/dev/zero of=/tmp/store1 bs=512 count=1048576
sudo losetup /dev/loop0 /tmp/store1
sudo mkfs.ext4 /dev/loop0
sudo mkdir -p /var/lib/kubelet
sudo mount -t ext4 /dev/loop0 /var/lib/kubelet

ALLOW_PRIVILEGED=Y ALLOW_SECURITY_CONTEXT=Y ./hack/local-up-cluster.sh -O
```

### Run pod with large ephemeral storage

Pod won't start with large ephemeral storage.

```yaml
1apiVersion: v1
kind: Pod
metadata:
  name: pod-large-ephemeral
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    resources:
      requests:
        cpu: 100m
        ephemeral-storage: 4096Gi
```


```shell
$ kubectl create -f pod-with-large-ephemeral.yaml

$ kubectl get pods
NAME                  READY     STATUS    RESTARTS   AGE
pod-large-ephemeral   0/1       Pending   0          33s
```

### Run pod with large emptyDir

Pod won't start with large emptydir.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-large-stratch-emptydir
spec:
  containers:
  - name: nginx
    image: nginx:1.13
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir:
      sizeLimit: 4096Gi
```

### Repeat the above experiments

If we repeat the above experiments, we'll see that pod writing large logs and pod
use-up emptydir volume will be evicted; however, if we create a pod with just
ephemeral-storage set (e.g. 128Mi), and write data larger than the size, pod will
keep running. This is because since we have different partitions for root and runtime
now, kubelet will not calculate container writable layer anymore.

Here is how kubelet eviction manager calculates fs stats for Pod:
- fsStatsLogs means container logs
- fsStatsLocalVolumeSource means local emptydir
- fsStatsRoot means container root fs (not kubelet root path)

```golang
if *m.dedicatedImageFs {
	fsStatsSet = []fsStatsType{fsStatsLogs, fsStatsLocalVolumeSource}
} else {
	fsStatsSet = []fsStatsType{fsStatsRoot, fsStatsLogs, fsStatsLocalVolumeSource}
}
```

Here is how kubelet eviction manager calculates fs stats for Container:
- fsStatsLogs means container logs
- fsStatsRoot means container root fs (not kubelet root path)

```
containerUsed := diskUsage(containerStat.Logs)
if !*m.dedicatedImageFs {
	containerUsed.Add(*diskUsage(containerStat.Rootfs))
}
```
