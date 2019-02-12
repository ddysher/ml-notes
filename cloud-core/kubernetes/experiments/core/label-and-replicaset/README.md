## Kubernetes v1.2 label

#### Create two pods first

- `kubectl create -f pod-with-label-1.yaml pod-with-label-2.yaml`

#### Then experiment with different rc and replicaset

- `kubectl create -f rc-with-label-1.yaml`
- `kubectl create -f rc-with-label-2.yaml`
- `kubectl create -f replicaset-1.yaml`
- etc

#### Command line

Make sure two pods are running:

- `kubectl get pods -l environment=prod,tier=backend `
- `kubectl get pods -l 'environment in (prod),tier in (backend)'`
