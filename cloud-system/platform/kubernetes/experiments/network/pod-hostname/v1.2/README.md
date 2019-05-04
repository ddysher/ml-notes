### Kubernetes pod hostname (v1.2)

- Create pod with hostname/subdomain annotation (soon to be spec field)

```
kubectl create -f pod-with-hostname.yaml
```

Then exec into the pod:

```
$ kubectl exec pod-with-hostname -it sh
# hostname -f
pod-hostname.pod-subdomain.default.svc.cluster.local
```

- Create headless service

```
kubectl create -f headless-svc.yaml
```

This will populate the service with Pod IP, and a DNS A record:

```
$ kubectl exec heapster-v1.0.0-edum7 -it --namespace=kube-system sh
/ # curl pod-hostname.pod-subdomain.default.svc.cluster.local:8000
Hello World!
```
