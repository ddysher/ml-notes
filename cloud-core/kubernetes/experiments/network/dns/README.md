## Inspect kubernetes dns (pre v1.0)

- Build and push images under images/ folder.

- Create pod 'k8s-dns-pod1', 'k8s-dns-pod1' will proivde a service 'k8s-dns-pod2' needs.:
  ```
  $ kubectl.sh create -f k8s-dns-pod1.json
  ```

- Create service 'k8s-dns-service1', targed at 'k8s-dns-pod1':
  ```
  $ kubectl.sh create -f k8s-dns-service1.json
  ```

- Create pod 'k8s-dns-pod2':
  ```
  $ kubectl.sh create -f k8s-dns-pod2.json
  ```
- Inspect 'k8s-dns-pod2' logs (not working now).
