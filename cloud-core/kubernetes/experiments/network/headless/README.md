## Kubernetes headless service

#### Create two pods

```
$ kubectl run --image nginx:1.13 --replicas 2 nginx
deployment "nginx" created

$ kubectl get pods --show-labels
NAME                     READY     STATUS    RESTARTS   AGE       LABELS
nginx-3853914729-263vm   1/1       Running   0          22s       pod-template-hash=3853914729,run=nginx
nginx-3853914729-nrkj0   1/1       Running   0          22s       pod-template-hash=3853914729,run=nginx
```

#### Create headless service

Headless service is a service that doesn't have service IP address. Kubernetes
will still create endpoints for headless service. Here, endpoints will be the
above two pods, and since the headless service selects them, two DNS A records
will be returned for the service.

```
$ kubectl create -f headless-svc.yaml
service "app-service" created

$ kubectl get ep
NAME          ENDPOINTS                     AGE
app-service   172.17.0.3:80,172.17.0.6:80   26s
kubernetes    192.168.8.53:6443             16m

$ nslookup app-service.default.svc.cluster.local 10.0.0.10
Server:         10.0.0.10
Address:        10.0.0.10#53

Name:   app-service.default.svc.cluster.local
Address: 172.17.0.3
Name:   app-service.default.svc.cluster.local
Address: 172.17.0.6
```

We can inspect the endpoints for more informaiton. Note that endpoint's address
doesn't have hostname.

```
$ kubectl get ep app-service -o yaml
apiVersion: v1
kind: Endpoints
metadata:
  creationTimestamp: 2017-05-23T13:08:14Z
  name: app-service
  namespace: default
  resourceVersion: "1436"
  selfLink: /api/v1/namespaces/default/endpoints/app-service
  uid: e111648d-3fb8-11e7-9f56-8825937fa049
subsets:
- addresses:
  - ip: 172.17.0.3
    nodeName: 127.0.0.1
    targetRef:
      kind: Pod
      name: nginx-3853914729-nrkj0
      namespace: default
      resourceVersion: "1388"
      uid: c9745614-3fb8-11e7-9f56-8825937fa049
  - ip: 172.17.0.6
    nodeName: 127.0.0.1
    targetRef:
      kind: Pod
      name: nginx-3853914729-263vm
      namespace: default
      resourceVersion: "1386"
      uid: c9744fb3-3fb8-11e7-9f56-8825937fa049
  ports:
  - port: 80
    protocol: TCP
```

#### Create headless service with port name

If creating headless service with port name, Kubernetes will use the service name
and port name to create SRV record.

```
kubectl create -f headless-svc-port.html

$ kubectl get svc
NAME               CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
app-service        None         <none>        80/TCP    17m
app-service-port   None         <none>        80/TCP    6m
kubernetes         10.96.0.1    <none>        443/TCP   56m
```

The exec into a utility pod to see the result:

```
/root@dnstuils:/# dig _http._tcp.app-service-port.default.svc.cluster.local

; <<>> DiG 9.9.5-3ubuntu0.2-Ubuntu <<>> _http._tcp.app-service-port.default.svc.cluster.local
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 20722
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 3, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;_http._tcp.app-service-port.default.svc.cluster.local. IN A

;; ANSWER SECTION:
_http._tcp.app-service-port.default.svc.cluster.local. 30 IN CNAME 3139376166613530.app-service-port.default.svc.cluster.local.
3237653666313939.app-service-port.default.svc.cluster.local. 30 IN A 172.17.0.4
3139376166613530.app-service-port.default.svc.cluster.local. 30 IN A 172.17.0.5

;; Query time: 0 msec
;; SERVER: 10.96.0.10#53(10.96.0.10)
;; WHEN: Mon Dec 04 03:32:00 UTC 2017
;; MSG SIZE  rcvd: 151
```

If we exec the same query on `app-service`, there won't be any result since Kubernetes
will not create SRV records for unnamed ports.
