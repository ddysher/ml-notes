#### Test existing 'storage' resource quota

```sh
$ kubectl create -f quota.yaml
$ kubectl create -f pvc1.yaml
$ kubectl create -f pvc2.yaml
Error from server (Forbidden): error when creating "pvc2.yaml": persistentvolumeclaims "myclaim2" is forbidden: exceeded quota: storage-resource, requested: requests.storage=8Gi, used: requests.storage=8Gi, limited: requests.storage=10Gi
```
