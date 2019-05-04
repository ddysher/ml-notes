## kubernetes deployment

Simple deployment:

```console
kubectl create -f 1-simple.yaml --save-config

kubectl get deployment

kubectl get pods

# How to find pods?
```

Update deployment:

```console
kubectl edit deployment simple-deployment

kubectl apply -f 1-simple-updated.yaml
```

Rollout history:

```console
kubectl rollout history deployment/simple-deployment

kubectl rollout history deployment/simple-deployment --revision=1

kubectl rollout undo deployment/simple-deployment --to-revision=1

# Run two `--to-revision` very quickly, will the second wait?
```

Standardalone replicaset

```console
$ kubectl create -f 2-replicaset.yaml
```

kubectl shortcut

```console
kubectl run my-nginx --image=nginx:1.13 --replicas=2 --port=80 --record
```
