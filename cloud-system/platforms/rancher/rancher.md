<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [v1 and v2](#v1-and-v2)
- [Features](#features)
  - [Unified Cluster Administration](#unified-cluster-administration)
  - [Simplified Cluster Lifecycle Management](#simplified-cluster-lifecycle-management)
  - [Application Workload Management](#application-workload-management)
- [Architecture](#architecture)
  - [Components](#components)
  - [Deployment Mode](#deployment-mode)
- [Experiment: single-node](#experiment-single-node)
  - [Install server](#install-server)
  - [Create custom cluster](#create-custom-cluster)
  - [Add existing cluster](#add-existing-cluster)
- [Experiment: high-availability](#experiment-high-availability)
  - [Run Kubernetes](#run-kubernetes)
  - [Install Rancher server](#install-rancher-server)
- [References](#references)
- [TBA](#tba)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 10/05/2019, v2.2*

## Introduction

Rancher is a complete container platform built on top of Kubernetes. The name Rancher often refers
to the main component "Rancher Server", which provides the UI and manages Kubernetes clusters.

RKE is different from Rancher, it is a stand-alone Kubernetes installer, like kops, kubeadm, etc.
Installing Rancher typically means installing rancher server. Rancher server will not install RKE,
nor do RKE installs Rancher server. RKE is used when users create custom clusters fram Rancher server.

## v1 and v2

Rancher v1 supports both Mesos, Swarm and Kubernetes, while Rancher v2 supports only Kubernetes.

# Features

## Unified Cluster Administration

The core feature of Rancher is unified cluster management, where all clusters are managed under
Rancher server. It includes an authentication proxy to proxy all user requests to underline clusters.

On top of centralized authentication, Rancher supports centralized access control policies, built
with native Kubernetes RBAC capabilities. Authentication and Authorization are integrated with
external systems like Local, GitHub, and Active Directory.

Rancher presents the concepts of users, groups and projects, cluster administrator can manage
permissions across different clusters from Rancher UI.

## Simplified Cluster Lifecycle Management

Rancher provides cluster provisioning, including:
- hosted Kubernetes like GKE, AKS
- rancher hosted Kubernetes using RKE, with nodes from baremetal or cloudproviders
- import existing Kubernetes

Rancher also provides a set of cluster maintainence facilities, including:
- etcd backup/restore
- clone cluster
- certificate rotation
- etc

## Application Workload Management

Rancher offers:
- easier user interface without users knowing all Kubernetes concepts
- expose native Kubernetes concepts managed by Rancher UI
- application catalog built with helm charts
- CI/CD systems integrated with Jenkins, Drone, etc
- monitoring and logging integration with Prometheus, ELK, Sysdig, etc

# Architecture

## Components

Components in Rancher includes:
- Rancher server: Rancher server is the most important component at the management plane. It includes
  - apiserver, with embedded kubernetes apiserver and embedded etcd
  - management controllers
  - user controllers
  - authentication proxy
- Cluster agent: Rancher deploys one cluster agent for each Kubernetes cluster under management.
  The main purpose of cluster agent is to provide a tunnel for Rancher server to communicate with
  user cluster Kubernetes API server. In addition, during registration, cluster agents get service
  account credentials from the Kubernetes cluster and send the service account credentials to the
  Rancher server.
- Node agent: Rancher deploys node agent on each node for each Kubernetes cluster. It performs
  initial install and follow-on upgrades, and work as a proxy to run kubectl command.

For more information, refer to the [architecture ebook](https://info.rancher.com/hubfs/eBooks/Rancher%20Architecture%20-%20v2.1.pdf).

## Deployment Mode

Running Rancher in HA requires a dedicated Kubernetes cluster, once running in the cluster, Rancher
server will register the cluster as "local". It is recommended that the cluster contains at least 3
nodes, and does not run user workload.

Rancher server will detect if it's running in Kubernetes or not. If not, it uses the embedded Kubernetes
API and etcd; otherwise, it will use the Kubernetes cluster to store data.

# Experiment: single-node

## Install server

Single node is suitable for development/testing.

To begin with, run Rancher server in a docker container:

```
$ docker run -d --restart=unless-stopped -p 80:80 -p 443:443 rancher/rancher:v2.2.8
```

The Rancher server itself contains quite a few components, the most important ones are Rancher API
server, controllers (management controllers and user controllers), as well as an embedded Kubernetes
API server and etcd, as mentioned above. Despite the complexity, a single container is all we need
to run a Rancher server (all the components run in a single binary).

Following snippet is a demonstration of the embedded Kubernetes API server and etcd. They serve as
the "database backend" of Rancher server.
- even with many components the container only has the Rancher server process
- the rancher server process is launched with tini
- it's possible to use `kubectl get xxx` from within the container

```
# Exec into the container
$ docker exec -it b281aecbc1f4 bash
root@b281aecbc1f4:/var/lib/rancher# ls
etcd  management-state

root@b281aecbc1f4:/var/lib/rancher# kubectl get crds
NAME                                                            CREATED AT
apprevisions.project.cattle.io                                  2019-10-04T09:04:50Z
apps.project.cattle.io                                          2019-10-04T09:04:50Z
authconfigs.management.cattle.io                                2019-10-04T09:04:50Z
catalogs.management.cattle.io                                   2019-10-04T09:04:50Z
catalogtemplates.management.cattle.io                           2019-10-04T09:04:50Z
catalogtemplateversions.management.cattle.io                    2019-10-04T09:04:50Z
clusteralertgroups.management.cattle.io                         2019-10-04T09:04:50Z
clusteralertrules.management.cattle.io                          2019-10-04T09:04:52Z
clusteralerts.management.cattle.io                              2019-10-04T09:04:50Z
clustercatalogs.management.cattle.io                            2019-10-04T09:04:51Z
clusterloggings.management.cattle.io                            2019-10-04T09:04:51Z
clustermonitorgraphs.management.cattle.io                       2019-10-04T09:04:52Z
clusterregistrationtokens.management.cattle.io                  2019-10-04T09:04:52Z
clusterroletemplatebindings.management.cattle.io                2019-10-04T09:04:52Z
clusters.management.cattle.io                                   2019-10-04T09:04:53Z
composeconfigs.management.cattle.io                             2019-10-04T09:04:53Z
dynamicschemas.management.cattle.io                             2019-10-04T09:04:53Z
etcdbackups.management.cattle.io                                2019-10-04T09:04:53Z
globaldnses.management.cattle.io                                2019-10-04T09:05:00Z
globaldnsproviders.management.cattle.io                         2019-10-04T09:05:00Z
globalrolebindings.management.cattle.io                         2019-10-04T09:04:53Z
globalroles.management.cattle.io                                2019-10-04T09:04:54Z
groupmembers.management.cattle.io                               2019-10-04T09:04:54Z
groups.management.cattle.io                                     2019-10-04T09:04:54Z
kontainerdrivers.management.cattle.io                           2019-10-04T09:04:54Z
listenconfigs.management.cattle.io                              2019-10-04T09:04:54Z
monitormetrics.management.cattle.io                             2019-10-04T09:04:55Z
multiclusterapprevisions.management.cattle.io                   2019-10-04T09:04:55Z
multiclusterapps.management.cattle.io                           2019-10-04T09:04:55Z
nodedrivers.management.cattle.io                                2019-10-04T09:04:55Z
nodepools.management.cattle.io                                  2019-10-04T09:04:55Z
nodes.management.cattle.io                                      2019-10-04T09:04:56Z
nodetemplates.management.cattle.io                              2019-10-04T09:04:56Z
notifiers.management.cattle.io                                  2019-10-04T09:04:56Z
pipelineexecutions.project.cattle.io                            2019-10-04T09:04:50Z
pipelines.project.cattle.io                                     2019-10-04T09:04:50Z
pipelinesettings.project.cattle.io                              2019-10-04T09:04:50Z
podsecuritypolicytemplateprojectbindings.management.cattle.io   2019-10-04T09:04:56Z
podsecuritypolicytemplates.management.cattle.io                 2019-10-04T09:04:56Z
preferences.management.cattle.io                                2019-10-04T09:04:57Z
projectalertgroups.management.cattle.io                         2019-10-04T09:04:57Z
projectalertrules.management.cattle.io                          2019-10-04T09:04:58Z
projectalerts.management.cattle.io                              2019-10-04T09:04:57Z
projectcatalogs.management.cattle.io                            2019-10-04T09:04:57Z
projectloggings.management.cattle.io                            2019-10-04T09:04:57Z
projectmonitorgraphs.management.cattle.io                       2019-10-04T09:04:58Z
projectnetworkpolicies.management.cattle.io                     2019-10-04T09:04:58Z
projectroletemplatebindings.management.cattle.io                2019-10-04T09:04:58Z
projects.management.cattle.io                                   2019-10-04T09:04:58Z
roletemplates.management.cattle.io                              2019-10-04T09:04:59Z
settings.management.cattle.io                                   2019-10-04T09:04:59Z
sourcecodecredentials.project.cattle.io                         2019-10-04T09:04:51Z
sourcecodeproviderconfigs.project.cattle.io                     2019-10-04T09:04:51Z
sourcecoderepositories.project.cattle.io                        2019-10-04T09:04:51Z
templatecontents.management.cattle.io                           2019-10-04T09:04:59Z
templates.management.cattle.io                                  2019-10-04T09:04:59Z
templateversions.management.cattle.io                           2019-10-04T09:04:59Z
tokens.management.cattle.io                                     2019-10-04T09:05:00Z
userattributes.management.cattle.io                             2019-10-04T09:05:00Z
users.management.cattle.io                                      2019-10-04T09:05:00Z

root@b281aecbc1f4:/var/lib/rancher# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   4520   752 ?        Ss   07:23   0:00 tini -- rancher --http-listen-port=80 --https-listen-port=443 --audit-log-path=/var/log/auditlog/rancher-api-audit.log --audit-level=0 --audit-log-maxage=10 --audit-log-maxbackup=10 --audit-log-maxsize=100
root         6 23.7  4.9 11047604 398616 ?     Sl   07:23  14:40 rancher --http-listen-port=80 --https-listen-port=443 --audit-log-path=/var/log/auditlog/rancher-api-audit.log --audit-level=0 --audit-log-maxage=10 --audit-log-maxbackup=10 --audit-log-maxsize=100
root       148  0.0  0.1 273048 11092 ?        Sl   07:25   0:00 telemetry client --url https://localhost:443/v3 --token-key telemetry:nv7dlmwbzn47qw687jjtns86xfdznt4zrzrxcwh8lr9dvqz2827p6v
root       222  1.8  0.0  18508  3408 pts/0    Ss   08:24   0:00 bash
root       238  0.0  0.0  34400  2848 pts/0    R+   08:24   0:00 ps aux
```

## Create custom cluster

From rancher UI, we can create a new custom cluster, and this effectively creates a Kubernetes cluster
with RKE. Rancher will prompt users to run the following container on each node of the to-be-created
cluster:
- The node here contains role `etcd`, `controlplane` and `worker`: this can be changed based on the
  role of the node.
- The agent will register the cluster to Rancher server, open a connection to Rancher server to install
  components, and launch a couple of helper containers to deploy Kubernetes.
- The `--server` param is the address of the rancher server we deployed above. It is required that
  all nodes in the cluster must have access to rancher server.

```
$ docker run -d --privileged --restart=unless-stopped --net=host \
  -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run \
  rancher/rancher-agent:v2.2.8 --server https://192.168.50.179 \
    --token cb7t5fnwwr6bwdsbq7bs9hvwhh8rpf7wsnz8phs84s8p865fvwhh9s \
    --ca-checksum c01818b571952eddd80c94231cef69aaf5cdb9349318ec20f58aa315114b17ed --etcd --controlplane --worker
```

After a while, a new Kubernetes cluster is created, following is the pods and CRDs created.
- RKE doesn't seem to use static Pod to run Kubernetes components.
- By default, RKE will deploy network cni, coredns, ingress, and metrics server.

```
$ kubectl get pods --all-namespaces
NAMESPACE       NAME                                      READY   STATUS             RESTARTS   AGE
cattle-system   cattle-cluster-agent-9dd86fcd-ggt55       1/1     Running            0          7m9s
cattle-system   cattle-node-agent-mshwf                   1/1     Running            0          7m9s
cattle-system   kube-api-auth-lkrsw                       1/1     Running            0          7m9s
ingress-nginx   default-http-backend-5954bd5d8c-vg8fp     1/1     Running            0          7m27s
ingress-nginx   nginx-ingress-controller-r7jv5            1/1     Running            6          7m27s
kube-system     canal-vw4vj                               2/2     Running            0          7m57s
kube-system     coredns-autoscaler-5d5d49b8ff-qkttx       1/1     Running            0          7m45s
kube-system     coredns-bdffbc666-sk7zw                   1/1     Running            0          7m46s
kube-system     metrics-server-7f6bd4c888-zkhjg           1/1     Running            0          7m37s
kube-system     rke-coredns-addon-deploy-job-7fbvh        0/1     Completed          0          7m54s
kube-system     rke-ingress-controller-deploy-job-ms5xg   0/1     Completed          0          7m34s
kube-system     rke-metrics-addon-deploy-job-b46bx        0/1     Completed          0          7m44s
kube-system     rke-network-plugin-deploy-job-sg6nb       0/1     Completed          0          8m4s

$ kubectl get crds --all-namespaces
NAME                                          CREATED AT
alertmanagers.monitoring.coreos.com           2019-10-04T08:43:01Z
bgpconfigurations.crd.projectcalico.org       2019-10-04T08:42:06Z
clusterauthtokens.cluster.cattle.io           2019-10-04T08:42:47Z
clusterinformations.crd.projectcalico.org     2019-10-04T08:42:06Z
clusteruserattributes.cluster.cattle.io       2019-10-04T08:42:47Z
felixconfigurations.crd.projectcalico.org     2019-10-04T08:42:06Z
globalnetworkpolicies.crd.projectcalico.org   2019-10-04T08:42:06Z
globalnetworksets.crd.projectcalico.org       2019-10-04T08:42:06Z
hostendpoints.crd.projectcalico.org           2019-10-04T08:42:06Z
ippools.crd.projectcalico.org                 2019-10-04T08:42:06Z
networkpolicies.crd.projectcalico.org         2019-10-04T08:42:06Z
prometheuses.monitoring.coreos.com            2019-10-04T08:43:01Z
prometheusrules.monitoring.coreos.com         2019-10-04T08:43:01Z
servicemonitors.monitoring.coreos.com         2019-10-04T08:43:01Z
```

The kubeconfig file downloaded from Rancher server shows that rancher API proxies all Kubernetes
requests. That is, instead using Kubernetes API server endpoint like `server: "https://xx.xx.xx.xx:6443"`,
it uses Rancher server endpoint `server: "https://192.168.50.179/k8s/clusters/c-krl78"`.

```
$ cat ~/.kube/config
apiVersion: v1
kind: Config
clusters:
- name: "test"
  cluster:
    server: "https://192.168.50.179/k8s/clusters/c-krl78"
    certificate-authority-data: ...
- name: "test-cherries"
  cluster:
    server: "https://192.168.50.179:6443"
    certificate-authority-data: ...
users:
- name: "user-pxvk2"
  user:
    token: "kubeconfig-user-pxvk2.c-krl78:c92l5wlkbqvntwmbnfd2rchdds579xdtbn8qmbkndf89fnpl5lkwtz"
contexts:
- name: "test"
  context:
    user: "user-pxvk2"
    cluster: "test"
- name: "test-cherries"
  context:
    user: "user-pxvk2"
    cluster: "test-cherries"
current-context: "test"
```

## Add existing cluster

To add existing cluster, Rancher will prompt users to run the following command:

```
# "192.168.50.179" is the IP address of Rancher server
kubectl apply -f https://192.168.50.179/v3/import/4z2hq6gmfxz8f4tr4wnnr6pmtwz7v6dgkhfjmf5twz8rkr8bkkdwr7.yaml
```

Following is the yaml file content, it includes
- a bunch of role & rolebinding
  - ClusterRole `proxy-clusterrole-kubeapiserver`
  - ClusterRole `cattle-admin` to run cluster-agent and node-agent
- a secret containing `url` (rancher server) and `token` (identify the cluster in rancher)
- a deployment for cluster-agent
- a daemonset for node-agent

<details><summary>YAML content</summary><p>

```yaml
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: proxy-clusterrole-kubeapiserver
rules:
- apiGroups: [""]
  resources:
  - nodes/metrics
  - nodes/proxy
  - nodes/stats
  - nodes/log
  - nodes/spec
  verbs: ["get", "list", "watch", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: proxy-role-binding-kubernetes-master
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: proxy-clusterrole-kubeapiserver
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: User
  name: kube-apiserver
---
apiVersion: v1
kind: Namespace
metadata:
  name: cattle-system

---

apiVersion: v1
kind: ServiceAccount
metadata:
  name: cattle
  namespace: cattle-system

---

apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: cattle-admin-binding
  namespace: cattle-system
  labels:
    cattle.io/creator: "norman"
subjects:
- kind: ServiceAccount
  name: cattle
  namespace: cattle-system
roleRef:
  kind: ClusterRole
  name: cattle-admin
  apiGroup: rbac.authorization.k8s.io

---

apiVersion: v1
kind: Secret
metadata:
  name: cattle-credentials-6eb9a94
  namespace: cattle-system
type: Opaque
data:
  url: "aHR0cHM6Ly8xOTIuMTY4LjUwLjE3OQ=="
  token: "czc4NGZ3N2d6Z3BsNmo1c2c4anY4N2w0Nmp2emxwcjh3NWhicmQycXJwNnBnanZ3NjY5Mno4"

---

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cattle-admin
  labels:
    cattle.io/creator: "norman"
rules:
- apiGroups:
  - '*'
  resources:
  - '*'
  verbs:
  - '*'
- nonResourceURLs:
  - '*'
  verbs:
  - '*'

---

apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: cattle-cluster-agent
  namespace: cattle-system
spec:
  selector:
    matchLabels:
      app: cattle-cluster-agent
  template:
    metadata:
      labels:
        app: cattle-cluster-agent
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                - key: beta.kubernetes.io/os
                  operator: NotIn
                  values:
                    - windows
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: node-role.kubernetes.io/controlplane
                operator: In
                values:
                - "true"
          - weight: 1
            preference:
              matchExpressions:
              - key: node-role.kubernetes.io/etcd
                operator: In
                values:
                - "true"
      serviceAccountName: cattle
      tolerations:
      - operator: Exists
      containers:
        - name: cluster-register
          imagePullPolicy: IfNotPresent
          env:
          - name: CATTLE_SERVER
            value: "https://192.168.50.179"
          - name: CATTLE_CA_CHECKSUM
            value: "ad412e83544e8274b5a21a2fe9ec9b7209a1ff17f33aae3c7cc8b345860cd430"
          - name: CATTLE_CLUSTER
            value: "true"
          - name: CATTLE_K8S_MANAGED
            value: "true"
          image: rancher/rancher-agent:v2.2.8
          volumeMounts:
          - name: cattle-credentials
            mountPath: /cattle-credentials
            readOnly: true
      volumes:
      - name: cattle-credentials
        secret:
          secretName: cattle-credentials-6eb9a94

---

apiVersion: extensions/v1beta1
kind: DaemonSet
metadata:
    name: cattle-node-agent
    namespace: cattle-system
spec:
  selector:
    matchLabels:
      app: cattle-agent
  template:
    metadata:
      labels:
        app: cattle-agent
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                - key: beta.kubernetes.io/os
                  operator: NotIn
                  values:
                    - windows
      hostNetwork: true
      serviceAccountName: cattle
      tolerations:
      - operator: Exists
      containers:
      - name: agent
        image: rancher/rancher-agent:v2.2.8
        imagePullPolicy: IfNotPresent
        env:
        - name: CATTLE_NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        - name: CATTLE_SERVER
          value: "https://192.168.50.179"
        - name: CATTLE_CA_CHECKSUM
          value: "ad412e83544e8274b5a21a2fe9ec9b7209a1ff17f33aae3c7cc8b345860cd430"
        - name: CATTLE_CLUSTER
          value: "false"
        - name: CATTLE_K8S_MANAGED
          value: "true"
        - name: CATTLE_AGENT_CONNECT
          value: "true"
        volumeMounts:
        - name: cattle-credentials
          mountPath: /cattle-credentials
          readOnly: true
        - name: k8s-ssl
          mountPath: /etc/kubernetes
        - name: var-run
          mountPath: /var/run
        - name: run
          mountPath: /run
        securityContext:
          privileged: true
      volumes:
      - name: k8s-ssl
        hostPath:
          path: /etc/kubernetes
          type: DirectoryOrCreate
      - name: var-run
        hostPath:
          path: /var/run
          type: DirectoryOrCreate
      - name: run
        hostPath:
          path: /run
          type: DirectoryOrCreate
      - name: cattle-credentials
        secret:
          secretName: cattle-credentials-6eb9a94
  updateStrategy:
    type: RollingUpdate
```

</p></details></br>

Start a local Kubernetes, then run the command; later, the cluster will appear in Rancher UI.
Creating resources from the command line will show up in Rancher UI (not all resources though).
In addition, the kubeconfig file downloaded from Rancher also sets Rancher server as the Kuberentes
server address.

# Experiment: high-availability

## Run Kubernetes

To run Rancher in HA mode, users need to run a Kubernetes cluster first:

```
$ ALLOW_PRIVILEGED=true ./hack/local-up-cluster.sh -O
```

## Install Rancher server

To install Rancher server, first we need helm:

```
kubectl -n kube-system create serviceaccount tiller

kubectl create clusterrolebinding tiller \
  --clusterrole=cluster-admin \
  --serviceaccount=kube-system:tiller

helm init --service-account tiller
```

Then install Rancher on top of the cluster (skip cert-manager):

```
helm repo add rancher-stable https://releases.rancher.com/server-charts/stable

helm install rancher-stable/rancher \
  --name rancher \
  --namespace cattle-system \
  --set hostname=rancher.my.org \
  --set ingress.tls.source=secret
```

After a while, Rancher is deployed to the cluster, following is Rancher pods and the CRDs created
from Rancher. Note the CRDs created here are almost the same as Rancher server deployed in single-node
setup, the difference here is the `monitoring.coreos.com`: in single-node setup, we don't have such
monitoring related CRDs.

```
$ kubectl get all -n cattle-system
NAME                           READY   STATUS    RESTARTS   AGE
pod/rancher-7cf4bb6cf6-62qrh   1/1     Running   2          8m36s
pod/rancher-7cf4bb6cf6-qnmsd   1/1     Running   1          8m36s
pod/rancher-7cf4bb6cf6-skbx2   1/1     Running   1          8m36s


NAME              TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/rancher   ClusterIP   10.0.0.99    <none>        80/TCP    8m36s


NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/rancher   3/3     3            3           8m36s

NAME                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/rancher-7cf4bb6cf6   3         3         3       8m36s

$ kubectl get crds --all-namespaces
NAME                                                            CREATED AT
alertmanagers.monitoring.coreos.com                             2019-10-04T09:03:08Z
apprevisions.project.cattle.io                                  2019-10-04T09:02:54Z
apps.project.cattle.io                                          2019-10-04T09:02:54Z
authconfigs.management.cattle.io                                2019-10-04T09:02:54Z
catalogs.management.cattle.io                                   2019-10-04T09:02:54Z
catalogtemplates.management.cattle.io                           2019-10-04T09:02:54Z
catalogtemplateversions.management.cattle.io                    2019-10-04T09:02:54Z
clusteralertgroups.management.cattle.io                         2019-10-04T09:02:54Z
clusteralertrules.management.cattle.io                          2019-10-04T09:02:54Z
clusteralerts.management.cattle.io                              2019-10-04T09:02:54Z
clustercatalogs.management.cattle.io                            2019-10-04T09:02:54Z
clusterloggings.management.cattle.io                            2019-10-04T09:02:54Z
clustermonitorgraphs.management.cattle.io                       2019-10-04T09:02:54Z
clusterregistrationtokens.management.cattle.io                  2019-10-04T09:02:54Z
clusterroletemplatebindings.management.cattle.io                2019-10-04T09:02:54Z
clusters.management.cattle.io                                   2019-10-04T09:02:54Z
composeconfigs.management.cattle.io                             2019-10-04T09:02:54Z
dynamicschemas.management.cattle.io                             2019-10-04T09:02:54Z
etcdbackups.management.cattle.io                                2019-10-04T09:02:54Z
globaldnses.management.cattle.io                                2019-10-04T09:02:59Z
globaldnsproviders.management.cattle.io                         2019-10-04T09:02:59Z
globalrolebindings.management.cattle.io                         2019-10-04T09:02:54Z
globalroles.management.cattle.io                                2019-10-04T09:02:54Z
groupmembers.management.cattle.io                               2019-10-04T09:02:55Z
groups.management.cattle.io                                     2019-10-04T09:02:55Z
kontainerdrivers.management.cattle.io                           2019-10-04T09:02:55Z
listenconfigs.management.cattle.io                              2019-10-04T09:02:55Z
monitormetrics.management.cattle.io                             2019-10-04T09:02:56Z
multiclusterapprevisions.management.cattle.io                   2019-10-04T09:02:56Z
multiclusterapps.management.cattle.io                           2019-10-04T09:02:56Z
nodedrivers.management.cattle.io                                2019-10-04T09:02:56Z
nodepools.management.cattle.io                                  2019-10-04T09:02:56Z
nodes.management.cattle.io                                      2019-10-04T09:02:57Z
nodetemplates.management.cattle.io                              2019-10-04T09:02:57Z
notifiers.management.cattle.io                                  2019-10-04T09:02:57Z
pipelineexecutions.project.cattle.io                            2019-10-04T09:02:54Z
pipelines.project.cattle.io                                     2019-10-04T09:02:54Z
pipelinesettings.project.cattle.io                              2019-10-04T09:02:54Z
podsecuritypolicytemplateprojectbindings.management.cattle.io   2019-10-04T09:02:57Z
podsecuritypolicytemplates.management.cattle.io                 2019-10-04T09:02:57Z
preferences.management.cattle.io                                2019-10-04T09:02:57Z
projectalertgroups.management.cattle.io                         2019-10-04T09:02:57Z
projectalertrules.management.cattle.io                          2019-10-04T09:02:57Z
projectalerts.management.cattle.io                              2019-10-04T09:02:57Z
projectcatalogs.management.cattle.io                            2019-10-04T09:02:57Z
projectloggings.management.cattle.io                            2019-10-04T09:02:57Z
projectmonitorgraphs.management.cattle.io                       2019-10-04T09:02:58Z
projectnetworkpolicies.management.cattle.io                     2019-10-04T09:02:58Z
projectroletemplatebindings.management.cattle.io                2019-10-04T09:02:58Z
projects.management.cattle.io                                   2019-10-04T09:02:58Z
prometheuses.monitoring.coreos.com                              2019-10-04T09:03:08Z
prometheusrules.monitoring.coreos.com                           2019-10-04T09:03:08Z
roletemplates.management.cattle.io                              2019-10-04T09:02:58Z
servicemonitors.monitoring.coreos.com                           2019-10-04T09:03:08Z
settings.management.cattle.io                                   2019-10-04T09:02:59Z
sourcecodecredentials.project.cattle.io                         2019-10-04T09:02:54Z
sourcecodeproviderconfigs.project.cattle.io                     2019-10-04T09:02:54Z
sourcecoderepositories.project.cattle.io                        2019-10-04T09:02:54Z
templatecontents.management.cattle.io                           2019-10-04T09:02:59Z
templates.management.cattle.io                                  2019-10-04T09:02:59Z
templateversions.management.cattle.io                           2019-10-04T09:02:59Z
tokens.management.cattle.io                                     2019-10-04T09:02:59Z
userattributes.management.cattle.io                             2019-10-04T09:02:59Z
users.management.cattle.io                                      2019-10-04T09:02:59Z
```

# References

**Demo**

- https://thenewstack.io/demo-rancher-2-2-reflects-the-ever-changing-dynamics-of-kubernetes/

**Blogs**

- https://rancher.com/blog/2019/2019-02-04-rancher-vs-rke/

# TBA

- controllers
  - rough role of each controller
  - how do they cache all resources in Kubernetes
- auth
  - how do authn/authz work when rancher proxy all Kubernetes requests
  - what's the underline rbac rules in each Kubernetes cluster
  - what's `kube-api-auth`
