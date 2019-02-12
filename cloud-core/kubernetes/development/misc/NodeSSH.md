kubectl to ssh node

While it's possible for k8s admin/users to ssh into nodes from cloudprovider, it is nicer to provide a ssh subcommnd within kubectl. This helps us provide a consistent view of kubernetes cluster.  So instead of
```
gcloud compute ssh instance --zone=us-central1-b
```
or
```
ssh -i blabla user@ip
```
Client can just do:
```
kubectl ssh node NodeName
```
where NodeName is the canonical node resource name in kubernetes, e.g. from `kubectl get node`.

One option is to provide is pod id, so
```
kubectl ssh node NodeName -p PodID
```
will ssh to the host where PodID is running.
