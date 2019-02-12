## ResourceQuota admission control configuration

Run cluster:

```
cp config.yaml /tmp/config.yaml

# under kubernetes repository:
ADMISSION_CONTROL_CONFIG_FILE=/tmp/config.yaml FEATURE_GATES=AllAlpha=true ALLOW_PRIVILEGED=true ./hack/local-up-cluster.sh -O
```

The configuration file will be passed to apiserver flag. LimitedResource in the
configuration file matches a resource whose consumption is limited by default.
To consume the resource, there must exist an associated quota that limits its
consumption. Here, the configuration says pods that uses 'system-cluster-critical'
priority class must have quota.

Create pods will be rejected:

```
$ kubectl create -f pod.yaml
Error from server: error when creating "pod.yaml": insufficient quota to match these scopes: [{PriorityClass In [system-cluster-critical]}]

$ kubectl create -f pod.yaml -n kube-system
Error from server: error when creating "pod.yaml": insufficient quota to match these scopes: [{PriorityClass In [system-cluster-critical]}]
```

If we create a quota in 'kube-system' namespace, then we'll be able to create pods
in 'kube-system' but still not other namespaces:


```
$ kubectl create -f quota.yaml -n kube-system
resourcequota/critical-priority-quota created

$ kubectl create -f pod.yaml
Error from server: error when creating "pod.yaml": insufficient quota to match these scopes: [{PriorityClass In [system-cluster-critical]}]

$ kubectl create -f pod.yaml -n kube-system
pod/nginx-critical created
```
