## kubernetes inline volume

#### Create a pod using inline volume

```
kubectl create -f pod-inline-volume.yaml
```

This will create a pod with using a pre-provisioned volume. Note we are using
gce persistent disk here, but it is essentially the same as hostpath and emptydir.
