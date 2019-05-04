## Persistent local volume

#### Create resources

```
kubectl create -f local-pv.yaml
kubectl create -f pvc.yaml
kubectl create -f pod.yaml
```

kubelet local volume plugin will do the following mount:

```
I0629 13:21:15.943322   17787 local.go:202] LocalVolume mount setup: PodDir(/var/lib/kubelet/pods/c61e4d1f-5c8a-11e7-8c56-8825937fa049/volumes/kubernetes.io~local-volume/example-local-pv) VolDir(/tmp/data) Mounted(false) Error(stat /var/lib/kubelet/pods/c61e4d1f-5c8a-11e7-8c56-8825937fa049/volumes/kubernetes.io~local-volume/example-local-pv: no such file or directory), ReadOnly(false)
I0629 13:21:15.943388   17787 local.go:222] attempting to mount /var/lib/kubelet/pods/c61e4d1f-5c8a-11e7-8c56-8825937fa049/volumes/kubernetes.io~local-volume/example-local-pv
I0629 13:21:15.943395   17787 mount_linux.go:118] Mounting cmd (mount) with arguments ([-o bind /tmp/data /var/lib/kubelet/pods/c61e4d1f-5c8a-11e7-8c56-8825937fa049/volumes/kubernetes.io~local-volume/example-local-pv])
```

i.e. local path is smiply bind-mounted under '/var/lib/kubelet'. The mount point is further bind mounted to container, e.g.

```
$ docker inspect a7
[
  ...
    "Mounts": [
      ...
      {
        "Type": "bind",
        "Source": "/var/lib/kubelet/pods/c61e4d1f-5c8a-11e7-8c56-8825937fa049/volumes/kubernetes.io~local-volume/example-local-pv",
        "Destination": "/data",
        "Mode": "",
        "RW": true,
        "Propagation": ""
      }
      ...
    ]
  ...
]
```
