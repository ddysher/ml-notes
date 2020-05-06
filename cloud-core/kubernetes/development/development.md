<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Environment](#environment)
  - [minikube](#minikube)
- [Testing](#testing)
  - [unittest](#unittest)
  - [e2e test](#e2e-test)
- [Minikube](#minikube)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> Development Tips

# Environment

## minikube

```
$ minikube start --memory 4096 --driver virtualbox --image-mirror-country cn image-repository registry.cn-hangzhou.aliyuncs.com/google_containers
```

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

# Minikube

minikube start --extra-config=apiserver.enable-admission-plugins="PodSecurityPolicy"
