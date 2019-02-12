## kubernetes static persistent volume (v1.2)

#### Provision storage and create persistent volume in kubernetes

```
kubectl create -f pv-hostpath.yaml
```

Note we are using hostpath here for testing; usually, we'll use cloud disks or
distributed storage. Static persistent volume is created by kubernetes admin,
and is almost immediately available (without acutally check the status of the
underline volume).

#### Create persistent volume claim

```
kubectl create -f pvc.yaml
```

Here kubernetes will match 'pv-hostpath' for us. Note here, we don't use any
storage class related features, so kubernetes will find a best match using
capacity. This means if we have 'pv-hostpath' and 'pv-gce', we can't instruct
kubernetes to use 'pv-gce' or 'pv-hostpath'.

In later release, we can use label selector and storage class. Note to experiment
this, we must disable default storage class; otherwise pvc won't bind pv-hostpath
since we are not specifying a class so kubernetes will try to dynamicall provision
one using default class for the pvc instead of binding to existing pv-hostpath.

#### Create pod using the claim

```
kubectl create -f pod-with-pvc.yaml
```
