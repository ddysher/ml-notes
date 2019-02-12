## Kubernetes HPA v2 (v1.9 beta)

Experiment follows
* [end-to-end tutorial](https://github.com/stefanprodan/k8s-prom-hpa/tree/55a53721acbf748a94c5873be4385bb8df976c97)

References
* [k8s prometheus adaptor](https://github.com/DirectXMan12/k8s-prometheus-adapter/blob/df48f2aa63529da8f33cfeee7b8f58452f506aeb/docs/walkthrough.md)
* [api aggregation auth](https://github.com/kubernetes-incubator/apiserver-builder/blob/cee53b80d654afe23943b2d7ca9611682ca3d3db/docs/concepts/auth.md)

Below is only a list of some notes; the end-to-end tutorial is very detailed.

### Running on linux with local cluster

metrics server will use node IP to get metrics information; thus it is important to bring up local
cluster with real node IP, not 127.0.0.1; otherwise metrics server will use 127.0.0.1 to query metrics
from kubelet, but since it is running in a Pod, 127.0.0.1 is its own loopback address so the query
will fai. Assuming node IP is 192.168.8.53, we bring up the cluster using:

```
HOSTNAME_OVERRIDE=192.168.8.53 KUBELET_HOST=0.0.0.0 ALLOW_PRIVILEGED=Y ALLOW_SECURITY_CONTEXT=Y ./hack/local-up-cluster.sh -O
```

Another caveat is that on linux, certs generation requires `base64 -w 0`; the tutorial only works on
Mac. PR sent :)

### Components

- metrics-server: this is a slimmed-down version of heapster, which queries kubelet for metrics and expose it via api aggregation.
- k8s-prometheus-adaptor: this adaptor is also an addon server using api aggregation, it transform query from kubernetes api to prometheus.

### Auth

The end-to-end tutorial doesn't use auth, that is, for both metrics-server and the adaptor server,
TLS verification is skipped. Based on the auth document, in production, we want to generate certs
for our aggregated api server, and provide the certs ca to API `apiregistration.k8s.io/v1beta1`,
kind: `APIService.spec.caBundle`.
