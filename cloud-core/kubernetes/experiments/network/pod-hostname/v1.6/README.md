## Kubernetes v1.6 pod hostname

#### Create pod with hostname/subdomain spec

```
kubectl create -f pod-with-hostname.yaml
```

Then exec into the pod:

```
$ kubectl exec pod-with-hostname -it sh
# hostname -f
pod-hostname.pod-subdomain.default.svc.cluster.local
# cat /etc/hosts
# Kubernetes-managed hosts file.
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
fe00::0 ip6-mcastprefix
fe00::1 ip6-allnodes
fe00::2 ip6-allrouters
172.17.0.3      pod-hostname.pod-subdomain.default.svc.cluster.local    pod-hostname
```

Note:
- Pod's `/etc/hosts` file is mounted from host, e.g. `/var/lib/kubelet/pods/f5fd585d-2f9d-11e7-bfdd-8825937fa049/etc-hosts`
- Multiple pods can have the same hostname.domain
- The `pod-hostname.pod-subdomain.default.svc.cluster.local` FQDN is only accessible from the pod itself

#### Create headless service

```
kubectl create -f headless-svc.yaml
```

This will make endpoint controller populates the service with Pod IPs, and make
DNS service create DNS A record for each pods:

```
$ kubectl run --image nginx:1.13 nginx
deployment "nginx" created

$ kubectl exec -it nginx-348975970-h8ll4 bash
/ # curl pod-hostname.pod-subdomain.default.svc.cluster.local:80
<!DOCTYPE html>
<html>
// truncated

$ kubectl get pods -o wide
NAME                    READY     STATUS    RESTARTS   AGE       IP           NODE
nginx-348975970-h8ll4   1/1       Running   0          54m       172.17.0.4   127.0.0.1
pod-with-hostname       1/1       Running   0          1h        172.17.0.3   127.0.0.1

$ kubectl get ep
NAME            ENDPOINTS           AGE
kubernetes      192.168.8.53:6443   1h
pod-subdomain   172.17.0.3:80       48m

$ kubectl get svc -o wide
NAME            CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE       SELECTOR
kubernetes      10.0.0.1     <none>        443/TCP   1h        <none>
pod-subdomain   None         <none>        80/TCP    48m       demo-hostname=true

$ nslookup pod-hostname.pod-subdomain.default.svc.cluster.local 10.0.0.10
Server:		10.0.0.10
Address:	10.0.0.10#53

Name:	pod-hostname.pod-subdomain.default.svc.cluster.local
Address: 172.17.0.3
```

Inspecting endpoints; note that the address has hostname, which is the trigger
for dns to insert A record for each pod.

```
$ kubectl get ep pod-subdomain -o yaml
apiVersion: v1
kind: Endpoints
metadata:
  creationTimestamp: 2017-05-23T13:12:11Z
  name: pod-subdomain
  namespace: default
  resourceVersion: "1713"
  selfLink: /api/v1/namespaces/default/endpoints/pod-subdomain
  uid: 6e869715-3fb9-11e7-9f56-8825937fa049
subsets:
- addresses:
  - hostname: pod-hostname
    ip: 172.17.0.7
    nodeName: 127.0.0.1
    targetRef:
      kind: Pod
      name: pod-with-hostname
      namespace: default
      resourceVersion: "1709"
      uid: 6d0e71b4-3fb9-11e7-9f56-8825937fa049
  ports:
  - port: 80
    protocol: TCP
```
