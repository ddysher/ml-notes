## Kubernetes local storage (v1.10 beta)

#### Run local cluster

```
ALLOW_PRIVILEGED=Y ./hack/local-up-cluster.sh -O
```

#### Manually create local PV

```
$ kubectl create -f local-pv.yaml
```

#### Local storage provisioner

https://github.com/kubernetes-incubator/external-storage/tree/local-volume-provisioner-v2.1.0/local-volume
