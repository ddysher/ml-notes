## kubernetes mount propagation

#### Run cluster

```console
$ ALLOW_PRIVILEGED=Y ./hack/local-up-cluster.sh -O
```

#### Propagation

Create hostpath pod with 'HostToContainer' propagation:

```console
kubectl create -f pod.yaml
```

Verify host to container mount propagation:

```
$ dd if=/dev/zero of=/tmp/store0 bs=512 count=1048576
1048576+0 records in
1048576+0 records out
536870912 bytes (537 MB, 512 MiB) copied, 1.65947 s, 324 MB/s

$ sudo losetup -f
/dev/loop0

$ sudo losetup /dev/loop0 /tmp/store0

$ sudo mkfs.ext4 /dev/loop0
mke2fs 1.42.13 (17-May-2015)
Discarding device blocks: done
Creating filesystem with 131072 4k blocks and 32768 inodes
Filesystem UUID: 52ecaa2b-a3e0-4598-b237-5bd2e3c4425b
Superblock backups stored on blocks:
        32768, 98304

Allocating group tables: done
Writing inode tables: done
Creating journal (4096 blocks): done
Writing superblocks and filesystem accounting information: done

$ kubectl exec -it pod-propagation bash
root@pod-propagation:/# ls /data/storage/
kube-apiserver.log
kube-controller-manager.log
kube-proxy.log
kube-proxy.yaml
kube-scheduler.log
kube-serviceaccount.key
kubelet.log
root@pod-propagation:/# exit

$ mkdir /tmp/abc

$ sudo mount -t ext4 /dev/loop0 /tmp/abc

$ kubectl exec -it pod-propagation bash
root@pod-propagation:/# ls /data/storage/
abc
kube-apiserver.log
kube-controller-manager.log
kube-proxy.log
kube-proxy.yaml
kube-scheduler.log
kube-serviceaccount.key
kubelet.log
root@pod-propagation:/# ls /data/storage/abc
lost+found
```

Create emptydir pod:

```console
kubectl create -f pod.yaml
```

If `/var/lib/kubelet` is not a shared mount, then we'll see error: "Path /var/lib/kubelet/pods/b213bccf-5733-11e7-81ff-8825937fa049/volumes/kubernetes.io~empty-dir/storage is mounted on /var/lib/kubelet but it is not a shared mount".
