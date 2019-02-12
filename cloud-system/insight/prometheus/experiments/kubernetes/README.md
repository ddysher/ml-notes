<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Prometheus with Kubernetes](#prometheus-with-kubernetes)
  - [Run](#run)
  - [Services](#services)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Prometheus with Kubernetes

## Run

Under current directory, run all components with:

```
kubectl create -f .
```

This will create:
- cluster role in kube-system
- node_exporter daemonset
- prometheus deployment, service and config
- grafana deployment and service

## Services

- For node exporter, go to http://127.0.0.1:9100
- For prometheus, go to http://127.0.0.1:32032
- For grafana, go to http://127.0.0.1:32064
