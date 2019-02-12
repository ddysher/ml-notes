## Kubernetes multi-ports service and endpoints (v1.10)

For every service, Kubernetes will create corresponding endpoints (if necessary).

#### Build container image

The image runs a python script serving two ports:

```
$ docker build -t multi-port:v1 .
```

#### Create Deployment

The deployment creates two pods, each listens on two socket ports:

```
$ kubectl create -f deployment.yaml
```

#### Create Service

The service exposes the previous deployment on two ports:

```
$ kubectl create -f service.yaml
```

Once the service is created, an endpoint will be automatically created via endpoint controller:

```
$ kubectl get pods -o wide
NAME                          READY     STATUS    RESTARTS   AGE       IP           NODE
multi-port-556946fc4f-j8crc   1/1       Running   0          11m       172.17.0.6   127.0.0.1
multi-port-556946fc4f-w2grh   1/1       Running   0          11m       172.17.0.5   127.0.0.1

$ kubectl get endpoints
NAME         ENDPOINTS                                                     AGE
kubernetes   192.168.3.34:6443                                             1h
multi-port   172.17.0.5:9876,172.17.0.6:9876,172.17.0.5:6789 + 1 more...   9s

$ kubectl describe endpoints multi-port
Name:         multi-port
Namespace:    default
Labels:       <none>
Annotations:  <none>
Subsets:
  Addresses:          172.17.0.5,172.17.0.6
  NotReadyAddresses:  <none>
  Ports:
    Name   Port  Protocol
    ----   ----  --------
    port2  9876  TCP
    port1  6789  TCP

Events:  <none>
```

#### Inspect iptables rules

The rules show that two rules, one per port, are appended to KUBE-SERVICES chain,
and at the last part, we see there are a total of four endpoints:

```
$ kubectl get service
NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)             AGE
kubernetes   ClusterIP   10.0.0.1     <none>        443/TCP             1h
multi-port   ClusterIP   10.0.0.180   <none>        6789/TCP,9876/TCP   1m

$ sudo iptables-save | grep 10.0.0.180
-A KUBE-SERVICES -d 10.0.0.180/32 -p tcp -m comment --comment "default/multi-port:port2 cluster IP" -m tcp --dport 9876 -j KUBE-SVC-7UM5QEJTMSFR5G7G
-A KUBE-SERVICES -d 10.0.0.180/32 -p tcp -m comment --comment "default/multi-port:port1 cluster IP" -m tcp --dport 6789 -j KUBE-SVC-AM4O52FQW27WOSP3

$ sudo iptables-save | grep KUBE-SVC-7UM5QEJTMSFR5G7G
:KUBE-SVC-7UM5QEJTMSFR5G7G - [0:0]
-A KUBE-SERVICES -d 10.0.0.180/32 -p tcp -m comment --comment "default/multi-port:port2 cluster IP" -m tcp --dport 9876 -j KUBE-SVC-7UM5QEJTMSFR5G7G
-A KUBE-SVC-7UM5QEJTMSFR5G7G -m comment --comment "default/multi-port:port2" -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-AOXBPDLZIRNUJBNU
-A KUBE-SVC-7UM5QEJTMSFR5G7G -m comment --comment "default/multi-port:port2" -j KUBE-SEP-4A4UPXXZY5YNOEMS

$ sudo iptables-save | grep KUBE-SVC-AM4O52FQW27WOSP3
:KUBE-SVC-AM4O52FQW27WOSP3 - [0:0]
-A KUBE-SERVICES -d 10.0.0.180/32 -p tcp -m comment --comment "default/multi-port:port1 cluster IP" -m tcp --dport 6789 -j KUBE-SVC-AM4O52FQW27WOSP3
-A KUBE-SVC-AM4O52FQW27WOSP3 -m comment --comment "default/multi-port:port1" -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-FHZWYI3JQ4ZIYTI6
-A KUBE-SVC-AM4O52FQW27WOSP3 -m comment --comment "default/multi-port:port1" -j KUBE-SEP-EAQZZX7TDJOG7UUH

$ sudo iptables-save | grep KUBE-SEP- | grep "multi-port" | grep "to-destination"
-A KUBE-SEP-4A4UPXXZY5YNOEMS -p tcp -m comment --comment "default/multi-port:port2" -m tcp -j DNAT --to-destination 172.17.0.6:9876
-A KUBE-SEP-AOXBPDLZIRNUJBNU -p tcp -m comment --comment "default/multi-port:port2" -m tcp -j DNAT --to-destination 172.17.0.5:9876
-A KUBE-SEP-EAQZZX7TDJOG7UUH -p tcp -m comment --comment "default/multi-port:port1" -m tcp -j DNAT --to-destination 172.17.0.6:6789
-A KUBE-SEP-FHZWYI3JQ4ZIYTI6 -p tcp -m comment --comment "default/multi-port:port1" -m tcp -j DNAT --to-destination 172.17.0.5:6789
```
