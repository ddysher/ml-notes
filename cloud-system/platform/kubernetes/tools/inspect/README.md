## Inspect various kubernetes internal representation.

- Start kubernetes cluster.
- Build and push images under images/ folder, follow instructions in Dockerfile.
- Create pod:
  ```
  $ kubectl create -f k8s-inspect-pod.yaml
  ```
- ssh into the minion pod is running, and check the logs 'docker logs ${id}'
- Delete pod:
  ```
  $ kubectl get pods k8s-inspect-pod
  ```
