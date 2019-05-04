Question X

You need to make sure data are persisted no matter when.

1. Create a file on a node at `/tmp/index.html` with content `hello`.

2. Create a persistent volume using hostpath and allocate 2Gi for it. The persistent volume has
   access mode `ReadWriteOnce` and StorageClass name `hostpath`.

3. Create a Persistent volume claim that requests a volume of at least 1Gi that with access mode
   `ReadWriteOnce` with storage class `hostpath`

4. Create an nginx pod with image nginx:1.13 and using the claim as data source
