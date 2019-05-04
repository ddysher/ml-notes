# Traffic Shaping

Make sure cni plugins are available, download from cni release, e.g. [v0.7.1](https://github.com/containernetworking/plugins/releases/download/v0.7.1/cni-plugins-amd64-v0.7.1.tgz).
Also, `tc` command must be installed.

Run local cluster with `kubenet` plugin (v1.12 adds support for `cni` plugin as well):

```
NET_PLUGIN=kubenet ./hack/local-up-cluster.sh -O
```

Create `pod.yaml` then we should be able to limit pod traffic.
