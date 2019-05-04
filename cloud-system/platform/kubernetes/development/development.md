> Development Tips

# Testing

## unittest

```
# unit test a special package
go test -v k8s.io/kubernetes/pkg/kubelet/kuberuntime
```

## e2e test

Run e2e test locally

```
make WHAT='test/e2e/e2e.test'
make ginkgo
export KUBERNETES_PROVIDER=local
go run hack/e2e.go -- -v --test --test_args="--ginkgo.focus=Feature:LocalPersistentVolumes --provider=local"
go run hack/e2e.go -- -v --test --test_args="--ginkgo.focus=Port\sforwarding --provider=local"
```
