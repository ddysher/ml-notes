## Kubernetes CSI (v1.10, beta)

Run local cluster:

```console
$ ALLOW_PRIVILEGED=Y ./hack/local-up-cluster.sh -O
```

Create storageclass, serviceaccount, rbac and all in one pod (hostpath csi):

```console
$ kubectl create -f csi-setup.yaml
```

Now create PVC:

```console
$ kubectl create -f pvc.yaml
```
