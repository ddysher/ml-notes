<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 04/07/2017, k8s 1.6, project release v2.0.0*

At time of writing, [external storage](https://github.com/kubernetes-incubator/external-storage) is
an incubator project. The project is fairly simple, it houses community-maintained external provisioners
plus a helper library for building them. For example, to use in-tree glusterfs provisioner, one can
just use:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: slow
provisioner: kubernetes.io/glusterfs
parameters:
  resturl: "http://127.0.0.1:8081"
  clusterid: "630372ccdc720a92c681fb928f27b53f"
  restuser: "admin"
  secretNamespace: "default"
  secretName: "heketi-secret"
  gidMin: "40000"
  gidMax: "50000"
  volumetype: "replicate:3"
```

However, if this in-tree class doesn't meet your requirement, you can create your own opinioned
provisioner. For example:

```yaml
apiVersion: storage.k8s.io/v1beta1
kind: StorageClass
metadata:
  name: glusterblock
provisioner: gluster.org/glusterblock
parameters:
  resturl: "http://127.0.0.1:8081"
  restuser: "admin"
  secretnamespace: "default"
  secretname: "heketi-secret"
  opmode: "executable"
  execpath: "/tmp/iscsicreate"
  hacount: "3"
```

To use external storage, we need to first create this storageclass to kubernetes; since there is no
claim using this class, it won't take any effect. Then we need to deploy a custom controller, which
watches for claims, and if any claim's storage class name equals the class we just created, a PV
will be created.

```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: claim1
  annotations:
    volume.beta.kubernetes.io/storage-class: "glusterblock"
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
```

The `external-storage` project aims to simplify this process. It defines an interface for developers
to implement external provisioner, to free them from implementing controller logic like retry, watch,
etc. It is *important* to note that out-of-tree provisioner is scoped to the volume supported in
kubernetes API. For example, you can create an out-of-tree provisioner for glusterfs, but not xxxfs,
because xxxfs API object is not defined in kubernetes. However, this doesn't mean that other storage
backend can never be supported - Kubernetes supports a wide range of protocols, custom storage backend
should be implemented using these protocols, e.g. NFS, iSCSI, etc.
