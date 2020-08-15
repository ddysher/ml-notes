<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [opennebula](#opennebula)
- [choerodon](#choerodon)
- [rainbond](#rainbond)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# opennebula

*Date: 06/19/2020, v5.12*

[OpenNebula](https://opennebula.io/) is an open-source management platform to build IaaS private,
public and hybrid clouds. It also support running container images, as well as orchestrating services
across multiple VMs (OneFlow).

OpenNebula appears early than OpenStack, with similar scope.

*References*

- https://docs.opennebula.io/5.12/
- https://docs.opennebula.io/minione/index.html

# choerodon

*Date: 05/04/2020, v0.18.0*

[Choerodon](https://github.com/choerodon/choerodon) is a multi-cloud `integrated` platform written
in Java. It is built on top of Kubernetes, Istio, Knative, Gitlab and Spring Cloud.

The main difference between other PaaS system is the "DevOps Experience". In Choerodon, DevOps
includes "Collaboration (like Jira)", "Development (like Jira + GitHub)", "Test (a lot reports)"
and "Operation (a lot reports)".

Choerodon is a microservice architecture and includes quite a few components, e.g.
- choerodon-framework, a microservice framework based on spring cloud
- api-gateway: gateway service based on netflix zuul
- file-service, a file service based on minio
- notify-service, a notification service
- gitlab-service
- test-manager-service
- devops-service
- etc.

Reference: [chorodon screenshot](https://github.com/choerodon/choerodon/blob/0.18.0/SCREENSHOT.md)

# rainbond

*Date: 05/04/2020, v5.2.0*

[Rainbond](https://github.com/goodrain/rainbond) is a container platform based on Kubernetes.

Installation is done using [rainbond-operator](https://github.com/goodrain/rainbond-operator), which
includes three CRDs (rainbondcluster, rainbondpackage, rainbondvolume). The rainbond-operator exposes
an API for user to configure, and once user clicked "Deploy", then a new CR `rainbondcluster` will be
created and rainbond-operator starts deploying the cluster.

Rainbond contains quite a few [components](https://www.rainbond.com/docs/user-operations/op-guide/component-description/),
providing core [architectures and capabilities](https://www.rainbond.com/docs/architecture/architecture/),
including:
- Rainbond API: providing rainbond API
- API Gateway Service: built with Ingress, and the proxy is based on OpenResty
- Application CI/CD: based on Jenkins, BuildPack, etc, as well as rainbond components rbd-mq, rbd-eventlog
- Application Runtime: set of workers providing application orchestration, backed by core Kubernetes resources
- Monitoring: Prometheus and a monitor component
- Message Queue: queue system based on etcd, which forms a basis of rainbond system
- Logging: collect logs for application, based on rbd-eventlog
- Cluster & Node: based on per-node agent rbd-node (rbd-node running on kube-master is the rbd master)
- Storage for Metadata: based on MySQL
- Registry: based on Docker Distribution
- Artifactory: based on Artifactory from JFrog
