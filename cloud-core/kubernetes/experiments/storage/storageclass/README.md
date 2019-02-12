## kubernetes storageclass

#### Run local cluster and optionally a nfs server

#### Create default class (optional)

Remove default local cluster storage class and create a new 'nfs-class'; note
the provisioner is a fake one. Note this step is optional: if both PV and PVC
have storage class attributes and there is available PV, then kubernetes will
directly bind the PV and PVC without using default class.

```
$ kubectl delete storageclasses standard
storageclass "standard" deleted

$ kubectl create -f class.yaml
storageclass "nfs-class" created
```

#### Create PV and PVC

Create PV and PVC then they will bound (If we don't give storage class attribute,
then we'll end up with pending pvc since kubernetes will try to provision with
default class).

```
$ kubectl create -f pvc.yaml
persistentvolumeclaim "myclaim" created

$ kubectl create -f pv.yaml
persistentvolume "nfs-pv" created

$ kubectl get pv
NAME      CAPACITY   ACCESSMODES   RECLAIMPOLICY   STATUS    CLAIM             STORAGECLASS   REASON    AGE
nfs-pv    50Gi       RWO           Recycle         Bound     default/myclaim   nfs-class                27m
```

https://stackoverflow.com/questions/44120612/kubernetes-pvc-not-binding-the-nfs-pv
