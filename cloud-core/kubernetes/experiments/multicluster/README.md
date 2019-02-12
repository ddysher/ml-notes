## Kubernetes multicluster on Minikube (v1.8 beta)

#### Bootstrap two Minikube

Note, minikube version is 0.23, kubernetes cluster version is 1.8.0

```
$ minikube start --profile minikube
$ minikube start --profile minikube2
```

We should have two contexts:

```
$ kubectl config get-contexts
CURRENT   NAME        CLUSTER     AUTHINFO    NAMESPACE
          minikube    minikube    minikube
*         minikube2   minikube2   minikube2
```

#### Run CoreDNS on "host cluster"

Host cluster is used to run federation control plane. It needs a DNS provider to
resolve federated service DNS. The following command will run a CoreDNS instance
in host cluster.

```
minikube -p minikube addons enable coredns
```

kubefed init myfed --host-cluster-context=minikube --dns-provider="coredns" --dns-zone-name="cluster.local" --api-server-service-type=NodePort --api-server-advertise-address=$(minikube ip -p minikube) --apiserver-enable-basic-auth=true --apiserver-enable-token-auth=true --apiserver-arg-overrides="
--anonymous-auth=true,--v=4" --dns-provider-config="./coredns-provider.conf"
