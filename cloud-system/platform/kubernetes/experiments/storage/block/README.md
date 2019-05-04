## Kubernetes Block Volume (v1.11 alpha)

Create resources, make sure '/dev/loop0' is unused:


```
$ dd if=/dev/zero of=/tmp/store0 bs=128 count=1048576
$ sudo losetup /dev/loop0 /tmp/store0

$ kubectl create -f pv.yaml
$ kubectl create -f pvc.yaml
$ kubectl create -f pod.yaml
```
