## kubernetes service

Simple service:

```console
$ kubectl create -f 1-simple.yaml

$ kubectl get pods -o wide

$ kubectl get svc ngxin-svc

$ kubectl get endpoints nginx-svc

$ kubectl create -f inspector.yaml

$ kubectl exec -it inspector sh
/ # wget -q -O - nginx-svc:8080
/ # cat /etc/resolv.conf
```

Multiple pods:

```console
$ kubectl create -f 2-multiple.yaml

$ kubectl get pods -o wide

$ kubectl get svc ngxin-svc-multiple

$ kubectl get endpoints nginx-svc

$ kubectl exec -it inspector sh
/ # wget -q -O - nginx-svc-multiple:8080

# open three terminals and watch for logs

$ minikube ssh
/ # sudo iptables-save
```

NodePort:

```console
$ kubectl create 3-nodeport.yaml

$ curl $(minikube ip):32111
```
