# Development

Edit file 'deployment/kubernetes/provisioner-daemonset.yaml': change image to `local-volume-provisioner:dev`,
and remove image pull policy.

```
$ make container IMAGE=local-volume-provisioner VERSION=dev
$ kubectl create -f deployment/kubernetes/admin_account.yaml
$ kubectl create -f deployment/kubernetes/provisioner-daemonset.yaml
```

To update change:

```
$ make container IMAGE=local-volume-provisioner VERSION=dev
$ kubectl delete pods local-volume-provisioner-nmxjp
```
# Alpha workaround

In 1.7 alpha release, there won't be complete scheduler code to integrate local volume with scheduler.
It will still operate on the old way where PV/PVC binding occurs at PV controller, indendent from Pod
scheduling. For local volume, this means that once the binding completes, pod requesting a PVC is
essentially assigned to the node where PV is created on. This can result in wrong or suboptimal
schedule decision. In 1.7 alpha release, an external controller is needed to work around the problem.

## Controller workflow

A single external controller is used, which is responsible to look at pods that are has local volume
request and are pending for scheduling for a long time.

Caches:
- watch all pods pending scheduling
- secondary cache for pv/pvc

Actions:
- Add/Update pod event
  * pod with no local volume request: ignore
  * pending pod with local volume request: enqueue to timed cache (to be processed later)
  * other status pod with local volume request: remove if exists in timed cache (e.g. user manually assigns to a node)
- Delete pod event: remove if pod exists in the timed cache
- Timed-cache timeout
  * For extra cautious, query API server; if positive, unbind PV/PVC (TODO: how to interact with pv controller)

# Notes

```
for vol in vol1 vol2 vol3; do
    sudo mkdir /mnt/fast-disks/$vol
    sudo mount -t tmpfs $vol /mnt/fastdisks/$vol
done
```

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv
spec:
  accessModes:
  - ReadWriteOnce
  capacity:
    storage: 8Gi
  local:
    path: /mnt/fast-disks/volume1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - 127.0.0.1
```
