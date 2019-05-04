## Kubernetes persistent volume dynamically provisioning (v1.6)

#### Create persistent volume claim

```
$ kubectl create -f pvc-storageclass.yaml --kubeconfig=$HOME/.kube/config-gce
$ kubectl get pvc --kubeconfig=$HOME/.kube/config-gce
NAME      STATUS    VOLUME    CAPACITY   ACCESSMODES   AGE
myclaim   Bound     pv0003    8Gi        RWO           9s
```

In GCE, default storageclass is gce persistent disk, so a gce persistent disk PV
will be created.

#### Create pod with pvc

```
kubectl create -f pod-with-pvc.yaml --kubeconfig=$HOME/.kube/config-gce
```
