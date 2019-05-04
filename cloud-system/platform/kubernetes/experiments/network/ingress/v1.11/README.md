## Kubernetes ingress (v1.11)

### Installation

Run a local Kubernetes cluster:

```
./hack/local-up-cluster.sh
```

Now create ingress controller and related resources:

```
kubectl create -f install/mandatory.yaml
kubectl create -f install/service-nodeport.yaml
```

The `mandatory.yaml` file contains ingress controller, service account, rbac rules,
services, etc. The argument `--publish-service=$(POD_NAMESPACE)/ingress-nginx`
means nginx controller will mirror the address of this service's endpoints to the
load-balancer status of all Ingress objects it satisfies. The `service-nodeport.yaml`
file contains this service.

However, in our local cluster, the ingress loadbalancer IP address is empty; this
is due to the fact that we are running the nginx-ingress service as node port. The
source code that determines the IP address to report is [here](https://github.com/kubernetes/ingress-nginx/blob/03ef9e0b49dcaf9fac47353128ebb908b2bee0d8/internal/ingress/status/status.go).
From the code we can see that for local cluster, we still can not have ingress
loadbalancer IP address set using `--report-node-internal-ip-address` since
the node.status is empty in local cluster.

Resources after installing ingress:

```
$ kubectl get all --all-namespaces
NAMESPACE       NAME                                           READY     STATUS    RESTARTS   AGE
ingress-nginx   pod/default-http-backend-846b65fb5f-jnc2x      1/1       Running   0          27m
ingress-nginx   pod/nginx-ingress-controller-d658896cd-82p9w   1/1       Running   0          27m
kube-system     pod/kube-dns-7b479ccbc6-n8zhh                  3/3       Running   0          41m

NAMESPACE       NAME                           TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                      AGE
default         service/kubernetes             ClusterIP   10.0.0.1     <none>        443/TCP                      41m
ingress-nginx   service/default-http-backend   ClusterIP   10.0.0.204   <none>        80/TCP                       27m
ingress-nginx   service/ingress-nginx          NodePort    10.0.0.224   <none>        80:31080/TCP,443:31443/TCP   26m
kube-system     service/kube-dns               ClusterIP   10.0.0.10    <none>        53/UDP,53/TCP                41m

NAMESPACE       NAME                                       DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
ingress-nginx   deployment.apps/default-http-backend       1         1         1            1           27m
ingress-nginx   deployment.apps/nginx-ingress-controller   1         1         1            1           27m
kube-system     deployment.apps/kube-dns                   1         1         1            1           41m

NAMESPACE       NAME                                                 DESIRED   CURRENT   READY     AGE
ingress-nginx   replicaset.apps/default-http-backend-846b65fb5f      1         1         1         27m
ingress-nginx   replicaset.apps/nginx-ingress-controller-d658896cd   1         1         1         27m
kube-system     replicaset.apps/kube-dns-7b479ccbc6                  1         1         1         41m
```

Processes inside ingress controller pod:

```
$ kubectl exec -it -n ingress-nginx nginx-ingress-controller-d658896cd-82p9w bash
www-data@nginx-ingress-controller-d658896cd-82p9w:/etc/nginx$ ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
www-data     1  0.0  0.0   4052   672 ?        Ss   06:04   0:00 /usr/bin/dumb-i
www-data     9  0.6  0.1  46132 29632 ?        Ssl  06:04   0:09 /nginx-ingress-
www-data    34  0.0  0.2 130808 35952 ?        S    06:04   0:00 nginx: master p
www-data  1141  0.0  0.2 393084 40728 ?        Sl   06:26   0:00 nginx: worker p
www-data  1142  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1143  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1144  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1145  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1146  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1147  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1156  0.0  0.2 393084 38008 ?        Sl   06:26   0:00 nginx: worker p
www-data  1405  0.0  0.0  18200  3280 pts/0    Ss   06:30   0:00 bash
www-data  1413  0.0  0.0  36640  2880 pts/0    R+   06:30   0:00 ps aux
www-data@nginx-ingress-controller-d658896cd-82p9w:/etc/nginx$ exit
```

If we run multiple replica of nginx controller pods, all of them will start nginx
processes, but only one of them will become the leader. If we run multiple class
of nginx controller deployment, we must use annocation `kubernetes.io/ingress.class: "nginx"`.

### Create ingress

Create ingress and example backend (from [here](https://github.com/kubernetes/contrib/tree/c4fa60f66f7430389c47c47675e2ce3d9ff9668a/ingress/echoheaders)).

```
kubectl create -f basic/
```

This will run an echo server in Kubernetes cluster; the server doesn't have any
public accessible endpoint (in-cluster service). Another ingress resource is created
to direct traffic from `http://basic.example.com` to the echo server.

To access the echoserver application, we need to add loopback address `127.0.0.1 basic.example.com`
or node IP `192.168.3.34 basic.example.com` to `/etc/hosts`. Now we can access
the app with:

```
curl basic.example.com:31080/
```

Here `31080` is the node port of nginx-ingress service. In real environment, we
can create public loadbalancer instead of using node port. For more information,
see [static IP example](https://github.com/kubernetes/ingress-nginx/tree/03ef9e0b49dcaf9fac47353128ebb908b2bee0d8/docs/examples/static-ip).

For now, when we access the above address, we are essentially hitting an nginx
listening on the address, which will then forward the requests to backend pods.

Note ingress resource must have the same namespace as its proxied services; but
an ingress controller can handle resources of multiple namespaces; for example,
we can create the above resources in another namespace:

```
$ kubectl delete -f basic/
service "echoheaders" deleted
deployment.apps "echoheaders" deleted
ingress.extensions "nginx-basic" deleted

$ kubectl create ns ingress-demo
namespace/ingress-demo created

$ kubectl create -f basic/ --namespace ingress-demo
service/echoheaders created
deployment.apps/echoheaders created
ingress.extensions/nginx-basic created

$ curl basic.example.com:31080/
```

Clean up the above resources:

```
kubectl delete -f basic/
kubectl delete -f basic/ -n ingress-demo
```

### Ingress rewrite

Rewrite is simple, it change our original request path to the one that matches
the actual path served by our backend server. We can create rewrite related
resources with:

```
kubectl create -f rewrite/
```

After services are up and running, we'll be able to access it:

```
$ curl rewrite.example.com:31080
default backend - 404%

$ curl rewrite.example.com:31080/something
server output blabla
```

Clean up the above resources:

```
kubectl delete -f rewrite/
```

### Ingress session sticky

Session sticky uses cookie to maintain stable connections with clients. As shown
in `sticky/ingress.yaml` file, we need to provide three annotations to configure
nginx.

Create resources:

```
$ kubectl create -f sticky/

$ kubectl get pods
NAME                           READY     STATUS    RESTARTS   AGE
echoheaders-5c84db8d7b-8xb9t   1/1       Running   0          15m
echoheaders-5c84db8d7b-w8vk9   1/1       Running   0          15m
echoheaders-5c84db8d7b-ztnwd   1/1       Running   0          15m

```

If we access the application without using any cookie, we'll see the requests are
round robined:

```
$ curl stickyingress.example.com:31080/
Hostname: echoheaders-5c84db8d7b-w8vk9

$ curl stickyingress.example.com:31080/
Hostname: echoheaders-5c84db8d7b-ztnwd

$ curl stickyingress.example.com:31080/
Hostname: echoheaders-5c84db8d7b-8xb9t
```

Now we start using session cookie, we'll see that all requests are forward to a
specific nginx instance:

```
$ curl -I stickyingress.example.com:31080/
HTTP/1.1 200 OK
Server: nginx/1.13.12
Date: Sun, 29 Jul 2018 08:18:10 GMT
Content-Type: text/plain
Connection: keep-alive
Vary: Accept-Encoding
Set-Cookie: route=1d53af47531f761b2c12ac1d830f3181a9c16f67; Path=/; HttpOnly

$ curl --cookie "route=1d53af47531f761b2c12ac1d830f3181a9c16f67" stickyingress.example.com:31080/
Hostname: echoheaders-5c84db8d7b-8xb9t

$ curl --cookie "route=1d53af47531f761b2c12ac1d830f3181a9c16f67" stickyingress.example.com:31080/
Hostname: echoheaders-5c84db8d7b-8xb9t

$ curl --cookie "route=1d53af47531f761b2c12ac1d830f3181a9c16f67" stickyingress.example.com:31080/
Hostname: echoheaders-5c84db8d7b-8xb9t
```

### Ingress TLS

Create TLS certificates:

```
$ openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=tls.example.com/O=tls.example.com"
Generating a 2048 bit RSA private key
................+++
................+++
writing new private key to 'tls.key'
-----

$ kubectl create secret tls tls-secret --key tls.key --cert tls.crt
secret "tls-secret" created
```

Now create resources:

```
$ kubectl create -f ./tls
```

Note we need to use another port to access TLS (make sure `tls.example.com` is specified in `/etc/hosts` ):

```
$ curl -k https://tls.example.com:31443
```

### Ingress Auth

#### Basic Auth & External Auth

Following examples are well-documented:

- [HTTP Basic Auth](https://github.com/kubernetes/ingress-nginx/tree/03ef9e0b49dcaf9fac47353128ebb908b2bee0d8/docs/examples/auth/basic)
- [External Auth](https://github.com/kubernetes/ingress-nginx/tree/03ef9e0b49dcaf9fac47353128ebb908b2bee0d8/docs/examples/auth/external-auth)

#### Client Certificate

For client certificate, we need to:
1. create a self-owned CA
2. use the CA to sign a client certificate (used to verify client identity)
3. create tls pair to host our server (can be independent of the above CA & client certs)

First create CA and certificates (from [prerequisites](https://github.com/kubernetes/ingress-nginx/blob/03ef9e0b49dcaf9fac47353128ebb908b2bee0d8/docs/examples/PREREQUISITES.md)).

```
$ openssl genrsa -out ca.key 2048
$ openssl req -x509 -new -nodes -key ca.key -days 10000 -out ca.crt -subj "/CN=example-ca"
```

This will generate two files: A private key (ca.key) and a public key (ca.crt).
This CA is valid for 10000 days. The ca.crt can be used later in the step of
creation of CA authentication secret. Then, a user generates his very own private
key (that he needs to keep secret) and a CSR (Certificate Signing Request) that
will be sent to the CA to sign and generate a certificate.

```
$ openssl genrsa -out client.key 2048
$ openssl req -new -key client.key -out client.csr -subj "/CN=client" -config openssl.cnf
```

As the CA receives the generated `client.csr` file, it signs it and generates
a `client.crt` certificate:

```
$ openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -extensions v3_req -extfile openssl.cnf
```

For now, we've created CA and client, we can then create tls chain (CA) secret,
which will be loaded to nginx to verity client certificate:

```
$ ls
ca.crt  ca.key  ca.srl  client.crt  client.csr  client.key  openssl.cnf

$ kubectl create secret generic auth-tls-chain --from-file=ca.crt
```

As in Ingress TLS, we need to create tls certificates, which will be loaded to
nginx to host our server (cert.example.com):

```
$ openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=cert.example.com/O=cert.example.com"

$ kubectl create secret tls tls-secret --key tls.key --cert tls.crt
secret "tls-secret" created
```

With all these secrets created, we can create resources:

```
$ kubectl create -f ./auth/cert
```

Then access the application:

```
$ curl -k https://cert.example.com:31443
<html>
<head><title>302 Found</title></head>
<body bgcolor="white">
<center><h1>302 Found</h1></center>
<hr><center>nginx/1.13.12</center>
</body>
</html>

$ curl -k --cert client.crt --key client.key https://cert.example.com:31443
Hostname: echoheaders-5c84db8d7b-795gn
```
