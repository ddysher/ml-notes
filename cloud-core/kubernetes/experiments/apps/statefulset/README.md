## Kubernetes StatefulSet v1.11

### Update Strategy

https://velotio.com/blog/2018/5/30/exploring-upgrade-strategies-for-statefulset-deployments-in-kubernetes


```sh
kubectl patch statefulset cassandra --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value":"gcr.io/google-samples/cassandra:v13"}]'
```
