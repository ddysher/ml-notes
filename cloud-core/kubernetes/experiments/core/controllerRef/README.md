## Kubernetes v1.6 controllerRef

#### Create a pod

```sh
kubectl create -f pod.yaml
```

#### Create a rs which selects the pod (1 replica)

```sh
kubectl create -f rs-1.yaml
```

#### Create another rs which selects the same pod (2 replica)

```sh
kubectl create -f rs-2.yaml
```

Now instead of fighting for pods, there will actually be 3 different pods.
