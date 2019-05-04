## Kubernetes Pod

#### Shortcut

Simple pod:

```
$ kubectl create -f 1-simple.yaml

$ kubectl get pods

$ kubectl describe pods nginx

$ kubectl get pods nginx -o yaml

$ kubectl get pods -o wide

$ minkube ssh
# curl 172.17.0.3
```

Multi-container pods:

```console
$ kubectl create -f 2-multi-container.yaml

# Two containers but same IP address, and always same machine
$ kubectl get pods -o wide
```

Shared volume:

```console
$ kubectl create -f 3-share-volume.yaml

$ kubectl exec -it share-volume -c fluent sh
/ # ls /fluentd/log/
```

Pod resources:

```console
$ kubectl create -f 4-pod-resource.yaml

# explain QoS (mention pod priority API)
# explain unit (128974848, 129e6, 129M, 123Mi)
# explain admission controller (initial resource)
```

#### Simple pod

Now if we list containers from docker, we'll see two containers:

```console
$ docker ps | grep nginx
ca1ba27a28d        nginx                                                  "nginx -g 'daemon ..."   2 minutes ago       Up 2 minutes                            k8s_nginx_nginx_default_8977e326-40ff-11e7-93d1-8825937fa049_0
a82557d9cbf        gcr.io/google_containers/pause-amd64:3.0               "/pause"                 2 minutes ago       Up 2 minutes                            k8s_POD_nginx_default_8977e326-40ff-11e7-93d1-8825937fa049_0
```

The first container is the actual container that we run; the second container
is a so-called 'pause' container that kubernetes uses as an infra container,
i.e. all containers in the pod wil share the namespaces with this infra container,
we can check this by running `docker inspect`:

```console
$ docker inspect 6ca1ba27a28d
[
  {
    "HostConfig": {
      "NetworkMode": "container:5a82557d9cbf6a6448595b9c0b6a7e6b5752c7c368e2b701d75f80f11af47062",
      "IpcMode": "container:5a82557d9cbf6a6448595b9c0b6a7e6b5752c7c368e2b701d75f80f11af47062",
      "PidMode": "container:5a82557d9cbf6a6448595b9c0b6a7e6b5752c7c368e2b701d75f80f11af47062",
      "UTSMode": "",
      "UsernsMode": "",
  },
  ...
]
```

Using `kubectl get pods nginx -o yaml` will return a lot of pod information.
To check what each field means, use `kubectl explain`; for example,
