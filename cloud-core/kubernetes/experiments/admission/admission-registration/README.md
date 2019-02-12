## kubernetes extensible admission controllers (v1.7 alpha)

### Initializer

#### Run local cluster with "initializer" enabled

```
RUNTIME_CONFIG="admissionregistration.k8s.io/v1alpha1" ./hack/local-up-cluster.sh
```

#### Deploy InitializerConfiguration resource

```
$ kubectl create -f initializerconfig.yaml
```

#### Create a pod

```
$ kubectl create -f pod.yaml
```

Note that apiserver will hold response until all initializers are removed; thus
`kubectl` will hang since we don't have an external admission controller called
`podimage.example.com`, it will wait forever. Use `ctrl+C` to quit.

#### Query uninitialized pods

By default, only initialized pods will be returned via API and cmd. To query
uninitialized pods, we need to append a query parameter:

```
$ curl http://localhost:8080/api/v1/namespaces/default/pods\?includeUninitialized=true
```

### External webhook

https://github.com/caesarxuchao/example-webhook-admission-controller/
