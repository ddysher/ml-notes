## Kubernetes configmap (v1.2)

#### Create

- Create a configmap from file

`kubectl create configmap game-config --from-file=kubectl`
`kubectl describe configmaps game-config`
`kubectl get configmaps game-config -o yaml`

- Create a configmap from literal

`kubectl create configmap special-config --from-literal=special.how=very --from-literal=special.type=charm`
`kubectl get configmaps special-config -o yaml`

#### Consume

- Consume with environment variable

`kubectl create -f configmap-env-pod.yaml`

- Consume with volume

`kubectl create -f configmap-volume-pod.yaml`

#### Redis Example

- Run redis

`kubectl create configmap example-redis-config --from-file=redis/redis-config`
`kubectl create -f redis/redis-pod.yaml`
`kubectl exec -it redis bash`

- Change config

`kubectl edit configmaps example-redis-config`
`kubectl exec -it redis bash`
