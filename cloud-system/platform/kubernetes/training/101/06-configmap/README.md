## Kubernetes configmap

Create configmap from file, and consume it using env

```console
$ kubectl create configmap training-config --from-literal=size=50 --from-literal=difficulty=easy

$ kubectl get configmap training-config -o yaml

$ kubectl create -f configmap-env-pod.yaml
```

- Consume with volume

```console
$ kubectl create configmap game-config --from-file=game.properties

$ kubectl get configmap game-config -o yaml

$ kubectl create -f volume-pod.yaml
```
