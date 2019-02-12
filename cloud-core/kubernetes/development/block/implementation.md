
#### Update APIs

###### PersistentVolume

<pre>
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-local-pv
  annotations:
   "volume.alpha.kubernetes.io/node-affinity": '{
     "requiredDuringSchedulingIgnoredDuringExecution": {
       "nodeSelectorTerms": [
         { "matchExpressions": [
           { "key": "kubernetes.io/hostname",
             "operator": "In",
             "values": ["my-node"]
           }
         ]}
        ]}
       }'
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /dev/sdx
    <b>fsType: ext4</b>
  <b>volumeType: block</b>
</pre>

- `spec.volumeType` tells type of volume, one of block and file.
- `spec.local.fsType` is valid only when volumeType is block. If pvc requests block,
  fsType is ignored; if pvc requests file, then local volume plugin will format it
  to fsType.

###### PersistentVolumeClaim

<pre>
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: local-raw-pvc
spec:
  storageClassName: local-storage
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 80Gi
  <b>volumeType: block</b>
</pre>

- `spec.volumeType` tells type of volume requested, one of block and file.
