# CKA certification

## Scope

The online exam consists of a set of performance-based items (problems) to be solved in a
command line running **Version 1.10.2** and candidates have 3 hours to complete the tasks.

The Certification focuses on the skills required to be a successful Kubernetes Administrator
in industry today. This includes these general domains and their weights on the exam:

* Application Lifecycle Management 8%
* Installation, Configuration & Validation 12%
* Core Concepts 19%
* Networking 11%
* Scheduling 5%
* Security 12%
* Cluster Maintenance 11%
* Logging / Monitoring 5%
* Storage 7%
* Troubleshooting 10%

Readings:

* https://www.cncf.io/certification/cka/
* https://github.com/cncf/curriculum/blob/master/certified_kubernetes_administrator_exam_v1.9.0.pdf

## Details

### Application Liftcycle Management

1. Understand Deployments and how to perform rolling updates and rollbacks
1. Know various ways to configure applications
1. Know how to scale applications
1. Understand the primitives necessary to create a self-healing application

Item 1 is VERY important topic in Kubernetes and CKA.

Item 2 is VERY important; this includes secrets, configmap, resource, etc, and how to use
them in Kubernetes Pods.

Item 3 and 4 are already coverred in the first two items.

_**Readings**_

- https://kubernetes.io/docs/tutorials/kubernetes-basics/deploy-intro/
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
- https://kubernetes.io/docs/concepts/configuration/secret/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/

_**Mock Questions**_

- Given a deployment name, perform rolling update, e.g. upgrade from nginx:1.12 to nginx 1.13
- Create a configmap or secret, then consume the configmap using env variable or volume mount

### Installation, Configuration & Validation

1. Design a Kubernetes cluster
1. Install Kubernetes masters and nodes, including the use of TLS bootstrapping
1. Configure secure cluster communications
1. Configure a Highly-Available Kubernetes cluster
1. Know where to get the Kubernetes release binaries
1. Provision underlying infrastructure to deploy a Kubernetes clusterd
1. Choose a network solution
1. Choose your Kubernetes infrastructure configuration
1. Run end-to-end tests on your cluster
1. Analyse end-to-end tests results
1. Run Node end-to-end tests

The first 9 items are hard even for experienced Kubernetes administrator. Try your best!

For the last 3 items, you are not required to understand the e2e tests; they are there
mostly as a reference.

_**Readings**_

- https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/
- https://kubernetes.io/docs/getting-started-guides/scratch/

_**Optional readings**_

- https://kubernetes.io/docs/setup/pick-right-solution/

_**Mock Questions**_

- An empty cluster is given to you, and you are required to bring up a Kubernetes cluster
- Master is already running, you are tasked to add new nodes to it
- Nodes are already running, you are tasked to configure master to recognize them
- Cluster is running without HTTPS; given certificates, you need to make their communication secure

### Core Concepts

1. Understand the Kubernetes API primitives.
1. Understand the Kubernetes cluster architecture.
1. Understand Services and other network primitives.

_**Readings**_

Command line:

- https://kubernetes.io/docs/reference/kubectl/overview/

Arch & APIs:

- https://kubernetes.io/docs/concepts/overview/components/
- https://kubernetes.io/docs/concepts/overview/kubernetes-api/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/kubernetes-objects/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/

Workloads:

- https://kubernetes.io/docs/concepts/workloads/pods/pod-overview/
- https://kubernetes.io/docs/concepts/workloads/pods/pod/
- https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- https://kubernetes.io/docs/concepts/workloads/pods/init-containers/
- https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
- https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/
- https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/
- https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/

Misc:

- https://kubernetes.io/docs/concepts/architecture/nodes/

_**Mock Questions**_

- Add liveness, readiness hooks to existing pods
- Create a multi-container Pod with given environment variables, images, etc
- Create a pod with init-container where the init container will do some initialization
- Perform scale, update operations on existing statefulset
- Run a job which calcutes some number, or a cronjob calculating the number periodically
- Run a daemonset with given parameters
- Find Pods with specific labels; find Pods with matching criteria
- Find unhealthy/notready nodes; find nodes with matching conditions

### Networking

1. Understand the networking configuration on the cluster nodes
1. Understand Pod networking concepts
1. Understand service networking
1. Deploy and configure network load balancer
1. Know how to use Ingress rules
1. Know how to configure and use the cluster DNS
1. Understand CNI

Item 1 & 7, CNI and cluster networking configuration are included in the installation part.

Item 2 & 3 & 6 are very important, and serve as the basis of Kubernetes and CKA exam.

Item 4 & 5 are about exposing your application to outside of cluster. You need to be familiar with ingress and service.type = LoadBalancer.

_**Readings**_

- https://kubernetes.io/docs/concepts/services-networking/service/
- https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
- https://kubernetes.io/docs/concepts/services-networking/connect-applications-service/
- https://kubernetes.io/docs/concepts/services-networking/ingress/

_**Optional Readings**_

- https://github.com/kubernetes/ingress-nginx/tree/master

_**Mock Questions**_

- Create a service for given deployment
- A service is not reachable in kubernetes cluster, you need to find where is the problem (e.g. iptables rules are not correct, kube-proxy is not running, etc)
- Deploy an ingress controller for given service and pod, then configure rules to allow accessing service with hostname
- Find out endpoint IPs of a specific cluster DNS

### Scheduling

1. Use label selectors to schedule Pods
1. Understand the role of DaemonSets
1. Understand how resource limits can affect Pod scheduling
1. Understand how to run multiple schedulers and how to configure Pods to use them
1. Manually schedule a pod without a scheduler
1. Display scheduler events
1. Know how to configure the Kubernetes scheduler

CKA exam focuses more on scheduling pods on node, make sure you understand the topic.

_**Readings**_

- https://kubernetes.io/docs/concepts/configuration/assign-pod-node/
- https://kubernetes.io/docs/tasks/administer-cluster/static-pod/
- https://kubernetes.io/docs/tasks/administer-cluster/configure-multiple-schedulers/

_**Optional Readings**_

- https://kubernetes.io/docs/concepts/configuration/taint-and-toleration/

_**Mock Questions**_

- Assign a pod to a specific node (affinity or node selector)
- Avoid scheduling a pod to specific pods
- Run two pods on the same node
- Run a static pod

### Security

1. Know how to configure authentication and authorization
1. Understand Kubernetes security primitives
1. Know to configure network policies
1. Create and manage TLS certificates for cluster components
1. Work with images securely
1. Define security contexts
1. Secure persistent key value store
1. Work with role-based access control

Authentication (token, etc), Authorization (RBAC), Security context and Network Policy are
four most important security topics in Kubernetes.

_**Readings**_

- https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/
- https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- https://kubernetes.io/docs/admin/authorization/rbac/

_**Mock Questions**_

- Configure network policy to restrict access of Pod A (do not allow pod B to access pod A)
- Add service account to a Pod and create RBAC rules to limit the pod to access only specific resources
- Configure pod security context to disallow the pod to be ran as root user

## Cluster Maintenance

1. Understand Kubernetes cluster upgrade process
1. Facilitate operating system upgrades
1. Implement backup and restore methodologies

Although important, upgrading Kubernetes cluster is probably too much for an online test.
However, you want to understand various concepts for maintaining a Kubernetes cluster.

_**Readings**_

- https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/

_**Mock Questions**_

- A node is broken, we want to move it out of cluster to do maintenance.

## Logging / Monitoring

- Understand how to monitor all cluster components
- Understand how to monitor applications
- Manage cluster component logs
- Manage application logs

Logging and monitoring spread all across CKA exam, whether it is cluster logs or application
logs. CKA clusters use systemd, make sure you know where to find cluster logs.

_**Readings**_

- https://kubernetes.io/docs/concepts/cluster-administration/logging/

_**Mock Questions**_

- Find logs of a Pod and save it somewhere
- Find pods use the most CPUs

## Storage

- Understand persistent volumes and know how to create them
- Understand access modes for volumes
- Understand persistent volume claims primitive
- Understand Kubernetes storage objects
- Know how to configure applications with persistent storage

You need to understand PV/PVC/StorageClass.

_**Readings**_

- https://kubernetes.io/docs/concepts/storage/volumes/#background
- https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- https://kubernetes.io/docs/concepts/storage/storage-classes/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-volume-storage/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/

_**Mock Questions**_

- Find all PVs or find PVs of a specific storage class
- Create a hostpath persistent volume, a pvc requesting the pv and use it in a Pod
- Create storageclass with given parameters

## Troubleshooting

- Troubleshoot application failure
- Troubleshoot control plane failure
- Troubleshoot worker node failure
- Troubleshoot networking

_**Readings**_

- https://kubernetes.io/docs/tasks/debug-application-cluster/debug-cluster/
- https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/
- https://kubernetes.io/docs/tasks/debug-application-cluster/debug-pod-replication-controller/
- https://kubernetes.io/docs/tasks/debug-application-cluster/debug-service/

_**Mock Questions**_

- Something is wrong with cluster components (apiserver, scheduler, etc), check logs and see what's the problem
- An application is not running: deployment exists but there is no pod, what's the problem?


## Tips

- 需要有英文的证件
- 在 chrome 上，全程会开摄像头，并分享屏幕
- 考试前先把其他程序退掉
- 考试环境需要桌面没其他东西
- 可以来一个新的 tab 查资料
- 考试页面左边是题目，右边是 ssh 终端
- 默认在一个跳板机上，记得切换环境
- 保存到指定地方文件，需要 sudo
- 注意熟悉系统环境和 k8s 版本
- 题目有操作题，有写 yaml 保存到指定位置，有给某个操作的结果保存到文件
- 题目，顺序和难度无关
- 有个 nodepad 可以保存笔记什么的
- 题目不一定直接对应到 k8s 的某个概念
- 诊断类问题，通常指给一个环境，问题描述比较简单，需要自己查原因
- 确保在正确的集群上操作
- 熟悉 systemctl journalctl 等命令
- web ssh 操作要熟悉，多行复制可能有问题
- 熟悉 yaml 怎么写，好多写 yaml 的，预先找找哪里有快速参考 yaml 模板
- 网络稳，自备翻墙
- 大部分题目很快可以做完，先把这些做了，部署题、调试题放最后
