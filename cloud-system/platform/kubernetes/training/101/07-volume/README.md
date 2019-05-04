## Kubernetes volume

```console
$ kubectl create -f 1-volume-inline-pod.yaml
```

```console
$ kubectl create -f 2-pv-hostpath.yaml

$ kubectl create -f 2-pvc.yaml

$ kubectl create -f 2-pvc-pod.yaml

$ kubectl describe pods mypod

$ kubectl delete pods mypod
```
