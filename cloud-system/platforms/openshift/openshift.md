<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
  - [Introduction](#introduction)
  - [v3 and v4](#v3-and-v4)
- [Features (Core)](#features-core)
  - [Project](#project)
  - [User](#user)
  - [Deployment](#deployment)
  - [Build](#build)
  - [ImageStream](#imagestream)
  - [Template](#template)
  - [Route](#route)
  - [OAuth](#oauth)
  - [Machine](#machine)
  - [Operators](#operators)
- [Features (Addon)](#features-addon)
  - [Installer](#installer)
  - [Runtime](#runtime)
  - [Jenkins](#jenkins)
  - [Service Broker](#service-broker)
  - [Service Mesh](#service-mesh)
  - [Serverless](#serverless)
  - [Cluster Monitoring](#cluster-monitoring)
  - [Container Native Virtualization](#container-native-virtualization)
  - [Container Native Storage](#container-native-storage)
- [Architecture](#architecture)
  - [OpenShift v3](#openshift-v3)
  - [OpenShift v4](#openshift-v4)
  - [References](#references)
- [Experiment (v3)](#experiment-v3)
  - [Installation](#installation)
  - [Components](#components)
- [Experiment (v4)](#experiment-v4)
  - [Installation](#installation-1)
  - [Components](#components-1)
- [References](#references-1)
- [TBA](#tba)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 10/01/2019, v3.11, v4.1*

## Introduction

> OpenShift Origin is a distribution of Kubernetes optimized for continuous application development
> and multi-tenant deployment. OpenShift adds developer and operations-centric tools on top of
> Kubernetes to enable rapid application development, easy deployment and scaling, and long-term
> lifecycle maintenance for small and large teams.

OpenShift Origin is the official product from RedHat. OKD refers to the OpenShift Origin community
distribution. There are two additional terms in OpenShift:
- CDK (Container Development Kit) for OpenShift Container Platform 3
- CRC (CodeReady Containers) for OpenShift Container Platform 4

## v3 and v4

There are two major versions of OpenShift, v3 and v4. Many aspects of v3 and v4 are the same, a major
difference between v3 and v4 is that OpenShift v4 uses operators as both the fundamental unit of the
product and an option for easily deploying and managing utilities that applications use.

# Features (Core)

OpenShift builds on top of Kubernetes, so all Kubernetes features are available in OpenShift (except
alpha features which are explicitly excluded). In addition, OpenShift adds:
- Source code management, builds, and deployments for developers
- Managing and promoting images using Kuberentes declarative APIs
- Team and user tracking for organizing a large developer organization
- Machine management across different cloud providers, as well as baremetal
- Logging, monitoring, Telemetry infrastructure
- Web Console for easier cluster management

Following is a list of concepts introduced in OpenShift.

## Project

A project is a Kubernetes namespace with additional annotations. For each namespace created/deleted,
OpenShift will sync with corresponding namespace, e.g. creating a namespace will result a new project
created with the same name.

## User

In addition to system users (system:nodes:node-1) and service account in Kubernetes, OpenShift defines
regular users as well. Regular users can register and login into OpenShift. `User` object works like
other object in OpenShift and is stored in etcd.

## Deployment

The OpenShift Container Platform `DeploymentConfig` object defines the following details of a deployment:
- The elements of a ReplicationController definition.
- Triggers for creating a new deployment automatically.
- The strategy for transitioning between deployments.
- Lifecycle hooks (e.g. run a pod with specified command before Recreate or Rolling update deployment).

DeploymentConfig is introduced before Kubernetes Deployment. The long-term plan is to merge Kubernetes
Deployment and OpenShift DeploymentConfig.

## Build

Build configurations (BuildConfig) define a build process for new container images. There are three
types of builds possible:
- a container image build using a Dockerfile
- a Source-to-Image build that uses a specially prepared base image that accepts source code that it
  can make runnable
- a custom build that can run arbitrary container images as a base and accept the build parameters.

Builds run on the cluster and on completion are pushed to the container image registry specified in
the "output" section. A build can be triggered via a webhook, when the base image changes, or when a
user manually requests a new build be created.

Each build created by a build configuration is numbered and refers back to its parent configuration.
Multiple builds can be triggered at once. Builds that do not have "output" set can be used to test
code or run a verification build.

## ImageStream

ImageStream is equivalent to a docker repository: where docker repository holds a collection of real
container images, ImageStream is a collection of references to real container images. Similarly,
ImageStreamTag is a reference to a tagged docker image: it only stores image metadata.

```
oc describe is python
Name:			python
Namespace:		imagestream
Created:		25 hours ago
Labels:			app=python
Annotations:		openshift.io/generated-by=OpenShiftWebConsole
			openshift.io/image.dockerRepositoryCheck=2017-10-03T19:48:00Z
Docker Pull Spec:	docker-registry.default.svc:5000/imagestream/python
Image Lookup:		local=false
Unique Images:		2
Tags:			2

34
  tagged from centos/python-34-centos7

  * centos/python-34-centos7@sha256:28178e2352d31f240de1af1370be855db33ae9782de737bb005247d8791a54d0
      14 seconds ago

35
  tagged from centos/python-35-centos7

  * centos/python-35-centos7@sha256:2efb79ca3ac9c9145a63675fb0c09220ab3b8d4005d35e0644417ee552548b10
      7 seconds ago
```

Users can configure Builds and Deployments to watch an image stream for notifications when new images
are added and react by performing a Build or Deployment, respectively. For example, in the following
DeploymentConfig, a new Deployment will be triggerred when ImageStreamTag `recreate-example:prod` has
changed. User can change the reference using `oc tag`, e.g. `oc tag recreate-example:prod recreate-example:v2`.

```yaml
apiVersion: v1
kind: DeploymentConfig
metadata:
  name: recreate-example
spec:
  replicas: 2
  selector:
    deploymentconfig: recreate-example
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        deploymentconfig: recreate-example
    spec:
      containers:
      - image: openshift/deployment-example:v1
        name: deployment-example
        ports:
        - containerPort: 8080
          protocol: TCP
  triggers:
  - type: ConfigChange
  - imageChangeParams:
      automatic: true
      containerNames:
      - deployment-example
      from:
        kind: ImageStreamTag
        name: recreate-example:prod
    type: ImageChange
```

Changing only image tag reference decouples management of container images from application. If
multiple deployments use the same base image, then by simply changing the reference, we can update
all deployments; otherwise, we have to update deployment manifest one by one. For more information,
refer to [this blog](https://cloudowski.com/articles/why-managing-container-images-on-openshift-is-better-than-on-kubernetes/).

## Template

A template describes a set of objects that can be parameterized and processed to produce a list of
objects for creation by OpenShift. A template can be processed to create anything you have permission
to create within a project, for example services, build configurations, and deployment configurations.

```yaml
apiVersion: v1
kind: Template
metadata:
  name: redis-template
  annotations:
    description: "Description"
    iconClass: "icon-redis"
    tags: "database,nosql"
objects:
- apiVersion: v1
  kind: Pod
  metadata:
    name: redis-master
  spec:
    containers:
    - env:
      - name: REDIS_PASSWORD
        value: ${REDIS_PASSWORD}
      image: dockerfile/redis
      name: master
      ports:
      - containerPort: 6379
        protocol: TCP
parameters:
- description: Password used for Redis authentication
  from: '[A-Z0-9]{8}'
  generate: expression
  name: REDIS_PASSWORD
labels:
  redis: master
```

## Route

Route is equivalent to Kubernetes Ingress, it is introduced before Kubernetes Ingress. By default,
route is backed by HAProxy. Following is an example Route config:

```yaml
apiVersion: v1
kind: Route
metadata:
  name: host-route
spec:
  host: www.example.com
  to:
    kind: Service
    name: service-name
```

An edge loadbalancer is required for in-cluster services to be accessible from outside. A common
deployment strategy is to set a dedicated machine, which will get its own Open vSwitch bridge that
the SDN automatically configures to provide access to the pods and nodes that reside in the cluster.
The routing table is dynamically configured by the SDN as pods are created and deleted, and thus the
routing software is able to reach the pods. The edge machine is usually marked as an unschedulable
node so that no pods end up on the machine itself.

## OAuth

OpenShift includes a built-in OAuth server, and comes with a set of APIs for using OAuth. The
internal server can be configured via API `OAuth`, and new OAuth client can be registered using
API `OAuthClient`.

When a person requests a new OAuth token, the OAuth server uses the configured identity provider
(e.g. GitHub, Google, LDAP) to determine the identity of the person making the request. It then
determines what user that identity maps to, creates an access token for that user, and returns the
token for use.

## Machine

OpenShift v4 includes a machine management APIs, which performs all node host provisioning management
actions after the cluster installation finishes. Because of the system, OpenShift v4 offers an elastic,
dynamic provisioning method on top of public or private cloud infrastructure.

The machine APIs are based on upstream Kuberentes [cluster-api](https://github.com/kubernetes-sigs/cluster-api),
including Machine, MachineSet, etc.

## Operators

OpenShift v4 is an operator-centric platform: nearly every components, including operating systems
and cluster itself, are managed by operators. In another word, every component is managed by an
operator, with configuration exposed via Kuberentes CRDs. The operators are responsible for
installing/upgrading the components.

> OpenShift uses operators to manage every aspect of the cluster.  This includes operators that
> manage essential Kubernetes project components like the api server, scheduler, and controller
> manager.  Additional operators for components like the cluster-autoscaler, cluster-monitoring,
> web console, dns, ingress, networking, node-tuning, and authentication are included to provide
> management of the entire platform.  Each operator exposes a custom resource API interface to
> define the desired state, observe the status of their rollout, and diagnose any issues that may
> occur.  The usage of the operator pattern simplifies operations and avoids configuration drift
> by continually reconciling the observed and desired states.  Finally, the operator lifecycle
> manager component is included to provide a framework for administrators to manage additional
> Kubernetes-native applications that are optionally integrated into the cluster as a day-2 task.

The cluster version operator is the root level operator: it reads the operator manifests included in
each OpenShift release image, and roll-out each operator in a controlled fashion which in turn is
responsible for upgrading their managed component.

It's important to note here that operator itself targets at managing underline components, it doesn't
provide functionalities in OpenShift directly. For example, the `cluster-monitoring-operator` installs
prometheus-operator, alertmanager, grafana, etc. As another example, the `cluster-api-operator` is
not responsible for managing machines, but installing cluster-api components, i.e. machine controller,
node controller, etc. The same applies for `machine-config-operator`, which deploys machine-config-server,
machine-config-controller and machine-config-daemon.

The set of operators can be found use [GitHub searches](https://github.com/openshift?utf8=✓&q=operator&type=&language=),
and the APIs can be found at https://github.com/openshift/api.

# Features (Addon)

## Installer

OpenShift v3 is installed and upgraded via [Ansible](https://github.com/openshift/openshift-ansible).

The installation process has changed dramatically in OpenShift v4. In v4, an [installer](https://github.com/openshift/installer/)
is in charge of installing a cluster. The core idea is to treat the install as a specialization of
an automated upgrade, and use Kubernetes operator pattern to manage the lifecycle of the operating
system, applications and the cluster itself. To use this strategy, we need a Kubernetes cluster in
the first place before actually starting Kubernetes; therefore, a special bootstrap machine is required
during the process. The bootstrap machine runs a temporary Kubernetes cluster, which connects to the
same etcd storage and performs control-plane installation. The whole process can be found [here](https://github.com/openshift/installer/blob/master-4.1/docs/user/overview.md).

Every control plane machine in an OpenShift v4 cluster must use Red Hat Enterprise Linux CoreOS
(RHCOS), while worker nodes can use RHEL as well. For OpenShift v4, RHCOS images are set up
initially with a feature called `Ignition`, which runs only on the system’s first boot. After first
boot, RHCOS systems are managed by the [Machine Config Operator (MCO)](https://github.com/openshift/machine-config-operator)
that runs in the OpenShift cluster. The [Machine API Operator](https://github.com/openshift/machine-config-operator)
handles provisioning of new machines - once the machine-api-operator provisions a machine, the MCO
will take care of configuring it.

> Ignition is the utility that is used by RHCOS to manipulate disks during initial configuration.
> It completes common disk tasks, including partitioning disks, formatting partitions, writing
> files, and configuring users.

In short, OpenShift v4 integrates both operating system and cluster management using operators.
For more details, read [this blog](https://blog.openshift.com/openshift-4-install-experience/).

## Runtime

In OpenShift v4, the default runtime changes from docker to cri-o.

## Jenkins

OpenShift has native integration with Jenkins. The first time a user creates a build configuration
using the Pipeline build strategy (i.e. BuildConfig.Spec.Strategy.JenkinsPipelineStrategy),
OpenShift looks for a template named `jenkins-ephemeral` in the openshift namespace and instantiates
it within the user’s project. The jenkins-ephemeral template that ships with OpenShift, upon
instantiation:
- a deployment configuration for Jenkins using the official OpenShift Jenkins image
- a service and route for accessing the Jenkins deployment
- a new Jenkins service account
- rolebindings to grant the service account edit access to the project

## Service Broker

OpenShift uses Kubernetes [service-catalog](https://github.com/kubernetes-sigs/service-catalog)
project to provide Service Broker capabilities, including:
- Template Service Broker
- Ansible Service Broker
- AWS Service Broker

## Service Mesh

OpenShift Service Mesh is based on istio project, and uses the [istio-operator](https://github.com/Maistra/istio-operator)
to manage the installation of the control plane. Note the istio-operator has a dependency on the
Jaeger Operator, Elasticsearch Operator and Kiali Operator.

## Serverless

OpenShift Serverless is based on the open source Knative project. It implements the building blocks
for developers to create modern, source-centric, container-based applications through a series of
Custom Resource Definitions (CRDs) and associated controllers in Kubernetes.

## Cluster Monitoring

OpenShift provides cluster monitoring via Prometheus, Alertmanager, and Grafana.

## Container Native Virtualization

OpenShift Container-native virtualization allows users to create VMs managed by Kubernetes. It uses
open source project [kubevirt](https://kubevirt.io) internally. Note cri-o is the required container
runtime for use with Container-native Virtualization.

## Container Native Storage

OpenShift Container-native storage a software-defined storage specifically built for container
environments. It is based on Gluster and highly integrated with OpenShift.

# Architecture

## OpenShift v3

OpenShift v3 follows the same architecture as Kubernetes, i.e. cluster is made of master and nodes.

master is also called control-plane, where openshift-apiserver, openshift-controller-manager are
running along side with kube-apiserver, kube-controller-manager, and kube-scheduler. Just like
kube-apierver, openshft-apiserver has direct access to underline etcd cluster (instead of using
Kubernetes API aggregation or CRDs). It follows the same storage schema as Kubernetes, thus once
saved in etcd, the objects can be read using `kubectl`; however, since Kubernetes doesn't understand
OpenShift objects (e.g. Build, Route), users cannot create these objects using `kubectl`.

On the node side, `openshift-sdn` and `openvswitch` is running using a DaemonSet. openshift-sdn is
the default network plugin for OpenShift (both OKD and OCP). It uses Open vSwitch to connect pods
locally, with VXLAN tunnels to connect different nodes. Many other components can be installed on
demand.

## OpenShift v4

Regarding control plane components, OpenShift v4 architecture remains the same, that is, the
openshift-apiserver, openshift-controller-manager runs on the master with kube-apiserver, kube-controller-manager
and kube-scheduler. The openshift-apiserver has direct access to etcd running on the master, the
pattern is:
- use direct etcd access to manage APIs like build, imagestream, etc
- use CRDs to configure and report status for components like kube-apiserver, dns, machine, network, etc
- use operators to install and apply changes to components

## References

- https://blog.openshift.com/how-and-why-were-changing-deployment-topology-in-openshift-4-0/

# Experiment (v3)

## Installation

To run an OpenShift v3 cluster, download and unpack `oc`.

```
$ wget https://github.com/openshift/origin/releases/download/v3.10.0/openshift-origin-client-tools-v3.10.0-dd10d17-linux-64bit.tar.gz
...
```

Make sure Docker is available, then call `oc cluster up`.

<details><summary>Cluster up process</summary><p>

```
$ oc cluster up --skip-registry-check
Getting a Docker client ...
Checking if image openshift/origin-control-plane:v3.10 is available ...
Creating shared mount directory on the remote host ...
Determining server IP ...
Checking if OpenShift is already running ...
Checking for supported Docker version (=>1.22) ...
Checking if required ports are available ...
Checking if OpenShift client is configured properly ...
Checking if image openshift/origin-control-plane:v3.10 is available ...
Starting OpenShift using openshift/origin-control-plane:v3.10 ...
I1001 16:51:34.841697   16334 config.go:42] Running "create-master-config"
I1001 16:51:37.845356   16334 config.go:46] Running "create-node-config"
I1001 16:51:40.876669   16334 flags.go:30] Running "create-kubelet-flags"
I1001 16:51:43.475541   16334 run_kubelet.go:48] Running "start-kubelet"
I1001 16:51:44.518307   16334 run_self_hosted.go:172] Waiting for the kube-apiserver to be ready ...
I1001 16:52:13.522391   16334 interface.go:26] Installing "kube-proxy" ...
I1001 16:52:13.522422   16334 interface.go:26] Installing "kube-dns" ...
I1001 16:52:13.522433   16334 interface.go:26] Installing "openshift-apiserver" ...
I1001 16:52:13.522473   16334 apply_template.go:83] Installing "kube-proxy"
I1001 16:52:13.522479   16334 apply_template.go:83] Installing "openshift-apiserver"
I1001 16:52:13.522501   16334 apply_template.go:83] Installing "kube-dns"
I1001 16:52:18.177833   16334 interface.go:41] Finished installing "kube-proxy" "kube-dns" "openshift-apiserver"
I1001 16:52:55.195010   16334 run_self_hosted.go:224] openshift-apiserver available
I1001 16:52:55.195032   16334 interface.go:26] Installing "openshift-controller-manager" ...
I1001 16:52:55.195045   16334 apply_template.go:83] Installing "openshift-controller-manager"
I1001 16:52:58.039721   16334 interface.go:41] Finished installing "openshift-controller-manager"
Adding default OAuthClient redirect URIs ...
Adding router ...
Adding web-console ...
Adding registry ...
Adding persistent-volumes ...
Adding centos-imagestreams ...
Adding sample-templates ...
I1001 16:52:58.047485   16334 interface.go:26] Installing "openshift-router" ...
I1001 16:52:58.047493   16334 interface.go:26] Installing "openshift-web-console-operator" ...
I1001 16:52:58.047498   16334 interface.go:26] Installing "openshift-image-registry" ...
I1001 16:52:58.047502   16334 interface.go:26] Installing "persistent-volumes" ...
I1001 16:52:58.047507   16334 interface.go:26] Installing "centos-imagestreams" ...
I1001 16:52:58.047512   16334 interface.go:26] Installing "sample-templates" ...
I1001 16:52:58.047536   16334 interface.go:26] Installing "sample-templates/mongodb" ...
I1001 16:52:58.047541   16334 interface.go:26] Installing "sample-templates/mariadb" ...
I1001 16:52:58.047546   16334 interface.go:26] Installing "sample-templates/cakephp quickstart" ...
I1001 16:52:58.047550   16334 interface.go:26] Installing "sample-templates/nodejs quickstart" ...
I1001 16:52:58.047555   16334 interface.go:26] Installing "sample-templates/jenkins pipeline ephemeral" ...
I1001 16:52:58.047559   16334 interface.go:26] Installing "sample-templates/sample pipeline" ...
I1001 16:52:58.047563   16334 interface.go:26] Installing "sample-templates/mysql" ...
I1001 16:52:58.047568   16334 interface.go:26] Installing "sample-templates/postgresql" ...
I1001 16:52:58.047573   16334 interface.go:26] Installing "sample-templates/dancer quickstart" ...
I1001 16:52:58.047577   16334 interface.go:26] Installing "sample-templates/django quickstart" ...
I1001 16:52:58.047583   16334 interface.go:26] Installing "sample-templates/rails quickstart" ...
I1001 16:52:58.047610   16334 apply_list.go:68] Installing "sample-templates/rails quickstart"
I1001 16:52:58.048043   16334 apply_template.go:83] Installing "openshift-web-console-operator"
I1001 16:52:58.051570   16334 apply_list.go:68] Installing "sample-templates/sample pipeline"
I1001 16:52:58.051688   16334 apply_list.go:68] Installing "centos-imagestreams"
I1001 16:52:58.051800   16334 apply_list.go:68] Installing "sample-templates/cakephp quickstart"
I1001 16:52:58.051855   16334 apply_list.go:68] Installing "sample-templates/nodejs quickstart"
I1001 16:52:58.052163   16334 apply_list.go:68] Installing "sample-templates/mongodb"
I1001 16:52:58.052232   16334 apply_list.go:68] Installing "sample-templates/jenkins pipeline ephemeral"
I1001 16:52:58.052448   16334 apply_list.go:68] Installing "sample-templates/mariadb"
I1001 16:52:58.052836   16334 apply_list.go:68] Installing "sample-templates/dancer quickstart"
I1001 16:52:58.053106   16334 apply_list.go:68] Installing "sample-templates/mysql"
I1001 16:52:58.053379   16334 apply_list.go:68] Installing "sample-templates/postgresql"
I1001 16:52:58.053642   16334 apply_list.go:68] Installing "sample-templates/django quickstart"
I1001 16:53:14.263611   16334 interface.go:41] Finished installing "sample-templates/mongodb" "sample-templates/mariadb" "sample-templates/cakephp quickstart" "sample-templates/nodejs quickstart" "sample-templates/jenkins pipeline ephemeral" "sample-templates/sample pipeline" "sample-templates/mysql" "sample-templates/postgresql" "sample-templates/dancer quickstart" "sample-templates/django quickstart" "sample-templates/rails quickstart"
I1001 16:53:40.765511   16334 interface.go:41] Finished installing "openshift-router" "openshift-web-console-operator" "openshift-image-registry" "persistent-volumes" "centos-imagestreams" "sample-templates"
Login to server ...
Creating initial project "myproject" ...
Server Information ...
OpenShift server started.

The server is accessible via web console at:
    https://127.0.0.1:8443

You are logged in as:
    User:     developer
    Password: <any value>

To login as administrator:
    oc login -u system:admin
```

</p></details></br>

Now we have a functional OpenShift cluster running.

## Components

Following is the objects created from `oc cluster up`.

<details><summary>Objects created</summary><p>

```
$ oc get all --all-namespaces
NAMESPACE                      NAME                                                  READY     STATUS      RESTARTS   AGE
default                        pod/docker-registry-1-6csdv                           1/1       Running     0          4h
default                        pod/persistent-volume-setup-tb8gs                     0/1       Completed   0          4h
default                        pod/router-1-s446v                                    1/1       Running     0          4h
kube-dns                       pod/kube-dns-bwrzj                                    1/1       Running     0          4h
kube-proxy                     pod/kube-proxy-td9mr                                  1/1       Running     0          4h
kube-system                    pod/kube-controller-manager-localhost                 1/1       Running     0          4h
kube-system                    pod/kube-scheduler-localhost                          1/1       Running     0          4h
kube-system                    pod/master-api-localhost                              1/1       Running     0          4h
kube-system                    pod/master-etcd-localhost                             1/1       Running     0          4h
openshift-apiserver            pod/openshift-apiserver-98v7k                         1/1       Running     0          4h
openshift-controller-manager   pod/openshift-controller-manager-jcrm9                1/1       Running     0          4h
openshift-core-operators       pod/openshift-web-console-operator-78ddf7cbb7-fc6nx   1/1       Running     0          4h
openshift-web-console          pod/webconsole-c99667df5-v76lm                        1/1       Running     0          4h

NAMESPACE   NAME                                      DESIRED   CURRENT   READY     AGE
default     replicationcontroller/docker-registry-1   1         1         1         4h
default     replicationcontroller/router-1            1         1         1         4h

NAMESPACE               NAME                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                   AGE
default                 service/docker-registry    ClusterIP   172.30.1.1      <none>        5000/TCP                  4h
default                 service/kubernetes         ClusterIP   172.30.0.1      <none>        443/TCP,53/UDP,53/TCP     4h
default                 service/router             ClusterIP   172.30.81.12    <none>        80/TCP,443/TCP,1936/TCP   4h
kube-dns                service/kube-dns           ClusterIP   172.30.0.2      <none>        53/UDP,53/TCP             4h
openshift-apiserver     service/api                ClusterIP   172.30.48.3     <none>        443/TCP                   4h
openshift-web-console   service/webconsole         ClusterIP   172.30.122.47   <none>        443/TCP                   4h

NAMESPACE                      NAME                                          DESIRED   CURRENT   READY     UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
kube-dns                       daemonset.apps/kube-dns                       1         1         1         1            1           <none>          4h
kube-proxy                     daemonset.apps/kube-proxy                     1         1         1         1            1           <none>          4h
openshift-apiserver            daemonset.apps/openshift-apiserver            1         1         1         1            1           <none>          4h
openshift-controller-manager   daemonset.apps/openshift-controller-manager   1         1         1         1            1           <none>          4h

NAMESPACE                  NAME                                             DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
openshift-core-operators   deployment.apps/openshift-web-console-operator   1         1         1            1           4h
openshift-web-console      deployment.apps/webconsole                       1         1         1            1           4h

NAMESPACE                  NAME                                                        DESIRED   CURRENT   READY     AGE
openshift-core-operators   replicaset.apps/openshift-web-console-operator-78ddf7cbb7   1         1         1         4h
openshift-web-console      replicaset.apps/webconsole-5b6df64745                       0         0         0         4h
openshift-web-console      replicaset.apps/webconsole-c99667df5                        1         1         1         4h

NAMESPACE   NAME                                DESIRED   SUCCESSFUL   AGE
default     job.batch/persistent-volume-setup   1         1            4h

NAMESPACE   NAME                                                 REVISION   DESIRED   CURRENT   TRIGGERED BY
default     deploymentconfig.apps.openshift.io/docker-registry   1          1         1         config
default     deploymentconfig.apps.openshift.io/router            1          1         1         config

NAMESPACE   NAME                                        DOCKER REPO                            TAGS                           UPDATED
openshift   imagestream.image.openshift.io/dotnet       172.30.1.1:5000/openshift/dotnet       latest,2.0                     5 hours ago
openshift   imagestream.image.openshift.io/httpd        172.30.1.1:5000/openshift/httpd        2.4,latest                     5 hours ago
openshift   imagestream.image.openshift.io/jenkins      172.30.1.1:5000/openshift/jenkins      1,2,latest                     5 hours ago
openshift   imagestream.image.openshift.io/mariadb      172.30.1.1:5000/openshift/mariadb      10.1,10.2,latest               5 hours ago
openshift   imagestream.image.openshift.io/mongodb      172.30.1.1:5000/openshift/mongodb      2.4,2.6,3.2 + 2 more...        5 hours ago
openshift   imagestream.image.openshift.io/mysql        172.30.1.1:5000/openshift/mysql        5.5,5.6,5.7 + 1 more...        5 hours ago
openshift   imagestream.image.openshift.io/nginx        172.30.1.1:5000/openshift/nginx        latest,1.10,1.12 + 1 more...   5 hours ago
openshift   imagestream.image.openshift.io/nodejs       172.30.1.1:5000/openshift/nodejs       6,8,latest + 2 more...         5 hours ago
openshift   imagestream.image.openshift.io/perl         172.30.1.1:5000/openshift/perl         latest,5.16,5.20 + 1 more...   5 hours ago
openshift   imagestream.image.openshift.io/php          172.30.1.1:5000/openshift/php          7.0,7.1,latest + 2 more...     5 hours ago
openshift   imagestream.image.openshift.io/postgresql   172.30.1.1:5000/openshift/postgresql   9.2,9.4,9.5 + 2 more...        5 hours ago
openshift   imagestream.image.openshift.io/python       172.30.1.1:5000/openshift/python       3.3,3.4,3.5 + 3 more...        5 hours ago
openshift   imagestream.image.openshift.io/redis        172.30.1.1:5000/openshift/redis        latest,3.2                     5 hours ago
openshift   imagestream.image.openshift.io/ruby         172.30.1.1:5000/openshift/ruby         2.5,latest,2.0 + 3 more...     5 hours ago
openshift   imagestream.image.openshift.io/wildfly      172.30.1.1:5000/openshift/wildfly      8.1,9.0,latest + 4 more...     5 hours ago

$ oc get templates --all-namespaces
NAMESPACE   NAME                       DESCRIPTION                                                                        PARAMETERS        OBJECTS
openshift   cakephp-mysql-persistent   An example CakePHP application with a MySQL database. For more information ab...   20 (4 blank)      9
openshift   dancer-mysql-persistent    An example Dancer application with a MySQL database. For more information abo...   17 (5 blank)      9
openshift   django-psql-persistent     An example Django application with a PostgreSQL database. For more informatio...   20 (5 blank)      9
openshift   jenkins-ephemeral          Jenkins service, without persistent storage....                                    7 (all set)       6
openshift   jenkins-pipeline-example   This example showcases the new Jenkins Pipeline integration in OpenShift,...       16 (4 blank)      8
openshift   mariadb-persistent         MariaDB database service, with persistent storage. For more information about...   9 (3 generated)   4
openshift   mongodb-persistent         MongoDB database service, with persistent storage. For more information about...   9 (3 generated)   4
openshift   mysql-persistent           MySQL database service, with persistent storage. For more information about u...   9 (3 generated)   4
openshift   nodejs-mongo-persistent    An example Node.js application with a MongoDB database. For more information...    19 (4 blank)      9
openshift   postgresql-persistent      PostgreSQL database service, with persistent storage. For more information ab...   8 (2 generated)   4
openshift   rails-pgsql-persistent     An example Rails application with a PostgreSQL database. For more information...   21 (4 blank)      9

$ oc get users
NAME        UID                                    FULL NAME   IDENTITIES
admin       bfd97342-e4e1-11e9-938b-4cedfbc8aee0               anypassword:admin
developer   c9c2a834-e4d7-11e9-938b-4cedfbc8aee0               anypassword:developer
```

</p></details></br>

This is not a comprehensive list, to see all the objects, use etcd:

```
$ cd openshift.local.clusterup/kube-apiserver
~/openshift.local.clusterup/kube-apiserver

$ etcdctl get / --prefix --keys-only --endpoints="https://127.0.0.1:4001" --key=master.etcd-client.key --cert=master.etcd-client.crt --cacert=ca.crt
...
```

Quick notes:
- `registry` and `router` Pods are docker registry and HAProxy, used for OpenShift specific features.
- Pods running in `kube-` namespaces are unmodified Kubernetes components, i.e. dns, proxy,
  controller-manager, scheduler, apiserver (master-api-localhost) and etcd (master-etcd-localhost).
  Kubelet is running in a docker container (not a Pod). Note if we inspect logs in the Pods, we'll
  see the following:
  ```
  github.com/openshift/origin/vendor/k8s.io/client-go/informers/factory.go:87 ....
  ```
  This is because OpenShift venders all Kubernetes code and build hyperkube from the vendor directory.
- Pods running in `openshift-` namespaces are OpenShift specific components, i.e. apiserver,
  controller-manager, web-console and web-console-operator.
- In OpenShift v3, the only CRD is `openshiftwebconsoleconfigs`. Using CRD config + operator to manage
  component is an experimental feature in OpenShift v3: the pattern is fully adopted in OpenShift v4.
  ```
  $ oc get crds --all-namespaces
  NAME                                                          AGE
  openshiftwebconsoleconfigs.webconsole.operator.openshift.io   5h

  $ oc get OpenShiftWebConsoleConfig instance
  NAME       AGE
  instance   5h
  ```
- The resource type `deploymentconfig` and `imagestream` are new resources defined in OpenShift.

# Experiment (v4)

## Installation

To install OpenShift v4, use [Code Ready Container](https://code-ready.github.io/crc/). To simply put:

```
$ crc setup

$ crc start
```

Network manager is required for crc. If dns config is not working, we can manually add them to `/etc/hosts`:

```
192.168.130.11 crc.testing
192.168.130.11 api.crc.testing
192.168.130.11 oauth-openshift.apps-crc.testing
```

## Components

<details><summary>Objects created</summary><p>

```
$ oc get pods --all-namespaces
NAMESPACE                                               NAME                                                              READY   STATUS      RESTARTS   AGE
openshift-apiserver-operator                            openshift-apiserver-operator-6db995744c-nc5pj                     1/1     Running     2          6d9h
openshift-apiserver                                     apiserver-d6dm8                                                   1/1     Running     5          6d8h
openshift-authentication-operator                       authentication-operator-668f5dd5cb-px72d                          1/1     Running     2          6d9h
openshift-authentication                                oauth-openshift-7949ccf5d-2j4dc                                   1/1     Running     0          36m
openshift-authentication                                oauth-openshift-7949ccf5d-dnzpb                                   1/1     Running     0          36m
openshift-cloud-credential-operator                     cloud-credential-operator-846fd45d76-zvr5b                        1/1     Running     2          6d9h
openshift-cluster-machine-approver                      machine-approver-d599647f4-b9bl5                                  1/1     Running     2          6d9h
openshift-cluster-node-tuning-operator                  cluster-node-tuning-operator-568db95869-g7g5v                     1/1     Running     2          6d9h
openshift-cluster-node-tuning-operator                  tuned-9t25z                                                       1/1     Running     0          38m
openshift-cluster-samples-operator                      cluster-samples-operator-84464ff57-qb9pc                          1/1     Running     2          6d8h
openshift-cluster-storage-operator                      cluster-storage-operator-6bc658fc74-cq7ph                         1/1     Running     2          6d8h
openshift-console-operator                              console-operator-cdc56f566-hl6n5                                  1/1     Running     2          6d8h
openshift-console                                       console-55bf5684d6-hc9xp                                          1/1     Running     2          6d8h
openshift-console                                       console-55bf5684d6-r7tv8                                          1/1     Running     2          6d8h
openshift-console                                       downloads-5bb8997d85-89kq9                                        1/1     Running     0          37m
openshift-console                                       downloads-5bb8997d85-lzq78                                        1/1     Running     2          6d8h
openshift-controller-manager-operator                   openshift-controller-manager-operator-7d857c6dff-gxcfk            1/1     Running     2          6d9h
openshift-controller-manager                            controller-manager-xmph4                                          1/1     Running     2          5d9h
openshift-dns-operator                                  dns-operator-566bc5d97b-jrb7h                                     1/1     Running     2          6d9h
openshift-dns                                           dns-default-jb2bx                                                 2/2     Running     4          6d9h
openshift-etcd                                          etcd-member-crc-chc9n-master-0                                    2/2     Running     4          6d9h
openshift-image-registry                                cluster-image-registry-operator-97d8b7fcb-q9fss                   2/2     Running     4          6d8h
openshift-image-registry                                image-registry-85b59cb6d5-tp4tf                                   1/1     Running     2          6d8h
openshift-image-registry                                node-ca-246rk                                                     1/1     Running     2          6d8h
openshift-ingress-operator                              ingress-operator-fbdb949c9-kkm8f                                  1/1     Running     2          6d8h
openshift-ingress                                       router-default-746885fd94-tknxp                                   1/1     Running     2          6d8h
openshift-insights                                      insights-operator-d8b996d8f-nmwps                                 1/1     Running     2          6d9h
openshift-kube-apiserver-operator                       kube-apiserver-operator-5cc9ccd675-9mwfk                          1/1     Running     2          6d9h
openshift-kube-apiserver                                installer-10-crc-chc9n-master-0                                   0/1     Completed   0          5d14h
openshift-kube-apiserver                                installer-11-crc-chc9n-master-0                                   0/1     Completed   0          5d9h
openshift-kube-apiserver                                installer-8-crc-chc9n-master-0                                    0/1     Completed   0          6d8h
openshift-kube-apiserver                                installer-9-crc-chc9n-master-0                                    0/1     Completed   0          5d14h
openshift-kube-apiserver                                kube-apiserver-crc-chc9n-master-0                                 3/3     Running     6          5d9h
openshift-kube-apiserver                                revision-pruner-10-crc-chc9n-master-0                             0/1     Completed   0          5d14h
openshift-kube-apiserver                                revision-pruner-11-crc-chc9n-master-0                             0/1     Completed   0          5d9h
openshift-kube-apiserver                                revision-pruner-7-crc-chc9n-master-0                              0/1     Completed   0          6d8h
openshift-kube-apiserver                                revision-pruner-8-crc-chc9n-master-0                              0/1     Completed   0          6d8h
openshift-kube-apiserver                                revision-pruner-9-crc-chc9n-master-0                              0/1     Completed   0          5d14h
openshift-kube-controller-manager-operator              kube-controller-manager-operator-5dd9c9c59-94k96                  1/1     Running     2          6d9h
openshift-kube-controller-manager                       installer-7-crc-chc9n-master-0                                    0/1     Completed   0          5d14h
openshift-kube-controller-manager                       kube-controller-manager-crc-chc9n-master-0                        2/2     Running     4          5d14h
openshift-kube-controller-manager                       revision-pruner-6-crc-chc9n-master-0                              0/1     Completed   0          6d8h
openshift-kube-controller-manager                       revision-pruner-7-crc-chc9n-master-0                              0/1     Completed   0          5d14h
openshift-kube-scheduler-operator                       openshift-kube-scheduler-operator-545747d6f-nwwfm                 1/1     Running     2          6d9h
openshift-kube-scheduler                                openshift-kube-scheduler-crc-chc9n-master-0                       1/1     Running     2          6d8h
openshift-kube-scheduler                                revision-pruner-6-crc-chc9n-master-0                              0/1     OOMKilled   0          6d8h
openshift-machine-api                                   machine-api-controllers-fcb76c4d5-wgzgv                           3/3     Running     6          6d8h
openshift-machine-config-operator                       machine-config-daemon-96hcr                                       1/1     Running     2          6d9h
openshift-machine-config-operator                       machine-config-server-4vbrr                                       1/1     Running     2          6d9h
openshift-marketplace                                   certified-operators-c76bb4784-vrnwj                               1/1     Running     0          37m
openshift-marketplace                                   community-operators-8678dc9469-b5kjr                              1/1     Running     0          36m
openshift-marketplace                                   marketplace-operator-7fd7d89795-2rjj9                             1/1     Running     2          6d8h
openshift-marketplace                                   redhat-operators-5f695556ff-kcjsd                                 1/1     Running     0          37m
openshift-monitoring                                    alertmanager-main-0                                               3/3     Running     6          6d8h
openshift-monitoring                                    alertmanager-main-1                                               3/3     Running     6          6d8h
openshift-monitoring                                    alertmanager-main-2                                               3/3     Running     6          6d8h
openshift-monitoring                                    node-exporter-qb7p7                                               2/2     Running     4          6d8h
openshift-multus                                        multus-admission-controller-vmhqk                                 1/1     Running     2          6d9h
openshift-multus                                        multus-t5gzr                                                      1/1     Running     2          6d9h
openshift-network-operator                              network-operator-685d4878c4-bx2pd                                 1/1     Running     2          6d9h
openshift-operator-lifecycle-manager                    catalog-operator-765c6f78b7-9wq57                                 1/1     Running     2          6d9h
openshift-operator-lifecycle-manager                    olm-operator-8597cfb57-xztm8                                      1/1     Running     2          6d9h
openshift-operator-lifecycle-manager                    packageserver-65bf47b9bb-kzrbr                                    1/1     Running     0          38m
openshift-operator-lifecycle-manager                    packageserver-65bf47b9bb-zxn92                                    1/1     Running     0          37m
openshift-sdn                                           ovs-4xn8v                                                         1/1     Running     2          6d9h
openshift-sdn                                           sdn-controller-4p7tb                                              1/1     Running     2          6d9h
openshift-sdn                                           sdn-fgftv                                                         1/1     Running     2          6d9h
openshift-service-ca-operator                           service-ca-operator-77f4fc8f5d-fxbxx                              1/1     Running     2          6d9h
openshift-service-ca                                    apiservice-cabundle-injector-5b97d64df-kctxh                      1/1     Running     2          6d9h
openshift-service-ca                                    configmap-cabundle-injector-79989ddcb9-bn7xw                      1/1     Running     2          6d9h
openshift-service-ca                                    service-serving-cert-signer-7787d496cf-rdg7m                      1/1     Running     2          6d9h
openshift-service-catalog-apiserver-operator            openshift-service-catalog-apiserver-operator-8564d47db4-bg6zz     1/1     Running     2          6d9h
openshift-service-catalog-controller-manager-operator   openshift-service-catalog-controller-manager-operator-797dz8rdw   1/1     Running     2          6d9h

$ oc get all --all-namespaces
NAMESPACE                                               NAME                                                                  READY   STATUS      RESTARTS   AGE
openshift-apiserver-operator                            pod/openshift-apiserver-operator-6db995744c-nc5pj                     1/1     Running     2          6d9h
openshift-apiserver                                     pod/apiserver-d6dm8                                                   1/1     Running     5          6d8h
openshift-authentication-operator                       pod/authentication-operator-668f5dd5cb-px72d                          1/1     Running     2          6d9h
openshift-authentication                                pod/oauth-openshift-7949ccf5d-2j4dc                                   1/1     Running     0          37m
openshift-authentication                                pod/oauth-openshift-7949ccf5d-dnzpb                                   1/1     Running     0          36m
openshift-cloud-credential-operator                     pod/cloud-credential-operator-846fd45d76-zvr5b                        1/1     Running     2          6d9h
openshift-cluster-machine-approver                      pod/machine-approver-d599647f4-b9bl5                                  1/1     Running     2          6d9h
openshift-cluster-node-tuning-operator                  pod/cluster-node-tuning-operator-568db95869-g7g5v                     1/1     Running     2          6d9h
openshift-cluster-node-tuning-operator                  pod/tuned-9t25z                                                       1/1     Running     0          38m
openshift-cluster-samples-operator                      pod/cluster-samples-operator-84464ff57-qb9pc                          1/1     Running     2          6d8h
openshift-cluster-storage-operator                      pod/cluster-storage-operator-6bc658fc74-cq7ph                         1/1     Running     2          6d8h
openshift-console-operator                              pod/console-operator-cdc56f566-hl6n5                                  1/1     Running     2          6d8h
openshift-console                                       pod/console-55bf5684d6-hc9xp                                          1/1     Running     2          6d8h
openshift-console                                       pod/console-55bf5684d6-r7tv8                                          1/1     Running     2          6d8h
openshift-console                                       pod/downloads-5bb8997d85-89kq9                                        1/1     Running     0          37m
openshift-console                                       pod/downloads-5bb8997d85-lzq78                                        1/1     Running     2          6d8h
openshift-controller-manager-operator                   pod/openshift-controller-manager-operator-7d857c6dff-gxcfk            1/1     Running     2          6d9h
openshift-controller-manager                            pod/controller-manager-xmph4                                          1/1     Running     2          5d9h
openshift-dns-operator                                  pod/dns-operator-566bc5d97b-jrb7h                                     1/1     Running     2          6d9h
openshift-dns                                           pod/dns-default-jb2bx                                                 2/2     Running     4          6d9h
openshift-etcd                                          pod/etcd-member-crc-chc9n-master-0                                    2/2     Running     4          6d9h
openshift-image-registry                                pod/cluster-image-registry-operator-97d8b7fcb-q9fss                   2/2     Running     4          6d8h
openshift-image-registry                                pod/image-registry-85b59cb6d5-tp4tf                                   1/1     Running     2          6d8h
openshift-image-registry                                pod/node-ca-246rk                                                     1/1     Running     2          6d8h
openshift-ingress-operator                              pod/ingress-operator-fbdb949c9-kkm8f                                  1/1     Running     2          6d8h
openshift-ingress                                       pod/router-default-746885fd94-tknxp                                   1/1     Running     2          6d8h
openshift-insights                                      pod/insights-operator-d8b996d8f-nmwps                                 1/1     Running     2          6d9h
openshift-kube-apiserver-operator                       pod/kube-apiserver-operator-5cc9ccd675-9mwfk                          1/1     Running     2          6d9h
openshift-kube-apiserver                                pod/installer-10-crc-chc9n-master-0                                   0/1     Completed   0          5d14h
openshift-kube-apiserver                                pod/installer-11-crc-chc9n-master-0                                   0/1     Completed   0          5d9h
openshift-kube-apiserver                                pod/installer-8-crc-chc9n-master-0                                    0/1     Completed   0          6d8h
openshift-kube-apiserver                                pod/installer-9-crc-chc9n-master-0                                    0/1     Completed   0          5d14h
openshift-kube-apiserver                                pod/kube-apiserver-crc-chc9n-master-0                                 3/3     Running     6          5d9h
openshift-kube-apiserver                                pod/revision-pruner-10-crc-chc9n-master-0                             0/1     Completed   0          5d14h
openshift-kube-apiserver                                pod/revision-pruner-11-crc-chc9n-master-0                             0/1     Completed   0          5d9h
openshift-kube-apiserver                                pod/revision-pruner-7-crc-chc9n-master-0                              0/1     Completed   0          6d8h
openshift-kube-apiserver                                pod/revision-pruner-8-crc-chc9n-master-0                              0/1     Completed   0          6d8h
openshift-kube-apiserver                                pod/revision-pruner-9-crc-chc9n-master-0                              0/1     Completed   0          5d14h
openshift-kube-controller-manager-operator              pod/kube-controller-manager-operator-5dd9c9c59-94k96                  1/1     Running     2          6d9h
openshift-kube-controller-manager                       pod/installer-7-crc-chc9n-master-0                                    0/1     Completed   0          5d14h
openshift-kube-controller-manager                       pod/kube-controller-manager-crc-chc9n-master-0                        2/2     Running     4          5d14h
openshift-kube-controller-manager                       pod/revision-pruner-6-crc-chc9n-master-0                              0/1     Completed   0          6d8h
openshift-kube-controller-manager                       pod/revision-pruner-7-crc-chc9n-master-0                              0/1     Completed   0          5d14h
openshift-kube-scheduler-operator                       pod/openshift-kube-scheduler-operator-545747d6f-nwwfm                 1/1     Running     2          6d9h
openshift-kube-scheduler                                pod/openshift-kube-scheduler-crc-chc9n-master-0                       1/1     Running     2          6d8h
openshift-kube-scheduler                                pod/revision-pruner-6-crc-chc9n-master-0                              0/1     OOMKilled   0          6d8h
openshift-machine-api                                   pod/machine-api-controllers-fcb76c4d5-wgzgv                           3/3     Running     6          6d8h
openshift-machine-config-operator                       pod/machine-config-daemon-96hcr                                       1/1     Running     2          6d9h
openshift-machine-config-operator                       pod/machine-config-server-4vbrr                                       1/1     Running     2          6d9h
openshift-marketplace                                   pod/certified-operators-c76bb4784-vrnwj                               1/1     Running     0          37m
openshift-marketplace                                   pod/community-operators-8678dc9469-b5kjr                              1/1     Running     0          37m
openshift-marketplace                                   pod/marketplace-operator-7fd7d89795-2rjj9                             1/1     Running     2          6d8h
openshift-marketplace                                   pod/redhat-operators-5f695556ff-kcjsd                                 1/1     Running     0          37m
openshift-monitoring                                    pod/alertmanager-main-0                                               3/3     Running     6          6d8h
openshift-monitoring                                    pod/alertmanager-main-1                                               3/3     Running     6          6d8h
openshift-monitoring                                    pod/alertmanager-main-2                                               3/3     Running     6          6d8h
openshift-monitoring                                    pod/node-exporter-qb7p7                                               2/2     Running     4          6d8h
openshift-multus                                        pod/multus-admission-controller-vmhqk                                 1/1     Running     2          6d9h
openshift-multus                                        pod/multus-t5gzr                                                      1/1     Running     2          6d9h
openshift-network-operator                              pod/network-operator-685d4878c4-bx2pd                                 1/1     Running     2          6d9h
openshift-operator-lifecycle-manager                    pod/catalog-operator-765c6f78b7-9wq57                                 1/1     Running     2          6d9h
openshift-operator-lifecycle-manager                    pod/olm-operator-8597cfb57-xztm8                                      1/1     Running     2          6d9h
openshift-operator-lifecycle-manager                    pod/packageserver-65bf47b9bb-kzrbr                                    1/1     Running     0          39m
openshift-operator-lifecycle-manager                    pod/packageserver-65bf47b9bb-zxn92                                    1/1     Running     0          37m
openshift-sdn                                           pod/ovs-4xn8v                                                         1/1     Running     2          6d9h
openshift-sdn                                           pod/sdn-controller-4p7tb                                              1/1     Running     2          6d9h
openshift-sdn                                           pod/sdn-fgftv                                                         1/1     Running     2          6d9h
openshift-service-ca-operator                           pod/service-ca-operator-77f4fc8f5d-fxbxx                              1/1     Running     2          6d9h
openshift-service-ca                                    pod/apiservice-cabundle-injector-5b97d64df-kctxh                      1/1     Running     2          6d9h
openshift-service-ca                                    pod/configmap-cabundle-injector-79989ddcb9-bn7xw                      1/1     Running     2          6d9h
openshift-service-ca                                    pod/service-serving-cert-signer-7787d496cf-rdg7m                      1/1     Running     2          6d9h
openshift-service-catalog-apiserver-operator            pod/openshift-service-catalog-apiserver-operator-8564d47db4-bg6zz     1/1     Running     2          6d9h
openshift-service-catalog-controller-manager-operator   pod/openshift-service-catalog-controller-manager-operator-797dz8rdw   1/1     Running     2          6d9h

NAMESPACE                                               NAME                                       TYPE           CLUSTER-IP       EXTERNAL-IP                            PORT(S)                      AGE
default                                                 service/kubernetes                         ClusterIP      172.30.0.1       <none>                                 443/TCP                      6d9h
default                                                 service/openshift                          ExternalName   <none>           kubernetes.default.svc.cluster.local   <none>                       6d8h
kube-system                                             service/kubelet                            ClusterIP      None             <none>                                 10250/TCP                    6d8h
openshift-apiserver-operator                            service/metrics                            ClusterIP      172.30.7.96      <none>                                 443/TCP                      6d9h
openshift-apiserver                                     service/api                                ClusterIP      172.30.191.198   <none>                                 443/TCP                      6d9h
openshift-authentication-operator                       service/metrics                            ClusterIP      172.30.66.140    <none>                                 443/TCP                      6d9h
openshift-authentication                                service/oauth-openshift                    ClusterIP      172.30.147.183   <none>                                 443/TCP                      6d8h
openshift-cloud-credential-operator                     service/controller-manager-service         ClusterIP      172.30.210.129   <none>                                 443/TCP                      6d9h
openshift-cluster-version                               service/cluster-version-operator           ClusterIP      172.30.8.10      <none>                                 9099/TCP                     6d9h
openshift-console-operator                              service/metrics                            ClusterIP      172.30.160.131   <none>                                 443/TCP                      6d8h
openshift-console                                       service/console                            ClusterIP      172.30.42.64     <none>                                 443/TCP                      6d8h
openshift-console                                       service/downloads                          ClusterIP      172.30.95.188    <none>                                 80/TCP                       6d8h
openshift-controller-manager-operator                   service/metrics                            ClusterIP      172.30.7.187     <none>                                 443/TCP                      6d9h
openshift-controller-manager                            service/controller-manager                 ClusterIP      172.30.97.25     <none>                                 443/TCP                      6d9h
openshift-dns                                           service/dns-default                        ClusterIP      172.30.0.10      <none>                                 53/UDP,53/TCP,9153/TCP       6d9h
openshift-etcd                                          service/etcd                               ClusterIP      172.30.103.87    <none>                                 2379/TCP,9979/TCP            6d9h
openshift-etcd                                          service/host-etcd                          ClusterIP      None             <none>                                 2379/TCP                     6d9h
openshift-image-registry                                service/image-registry                     ClusterIP      172.30.145.34    <none>                                 5000/TCP                     6d8h
openshift-ingress                                       service/router-internal-default            ClusterIP      172.30.37.247    <none>                                 80/TCP,443/TCP,1936/TCP      6d8h
openshift-kube-apiserver-operator                       service/metrics                            ClusterIP      172.30.216.177   <none>                                 443/TCP                      6d9h
openshift-kube-apiserver                                service/apiserver                          ClusterIP      172.30.214.235   <none>                                 443/TCP                      6d9h
openshift-kube-controller-manager-operator              service/metrics                            ClusterIP      172.30.28.74     <none>                                 443/TCP                      6d9h
openshift-kube-controller-manager                       service/kube-controller-manager            ClusterIP      172.30.155.106   <none>                                 443/TCP                      6d9h
openshift-kube-scheduler-operator                       service/metrics                            ClusterIP      172.30.19.220    <none>                                 443/TCP                      6d9h
openshift-kube-scheduler                                service/scheduler                          ClusterIP      172.30.251.60    <none>                                 443/TCP                      6d9h
openshift-machine-api                                   service/cluster-autoscaler-operator        ClusterIP      172.30.252.27    <none>                                 443/TCP,8080/TCP             6d9h
openshift-machine-api                                   service/machine-api-operator               ClusterIP      172.30.206.1     <none>                                 8080/TCP                     6d9h
openshift-marketplace                                   service/certified-operators                ClusterIP      172.30.3.29      <none>                                 50051/TCP                    37m
openshift-marketplace                                   service/community-operators                ClusterIP      172.30.64.131    <none>                                 50051/TCP                    37m
openshift-marketplace                                   service/marketplace-operator-metrics       ClusterIP      172.30.46.101    <none>                                 8383/TCP                     6d9h
openshift-marketplace                                   service/redhat-operators                   ClusterIP      172.30.76.87     <none>                                 50051/TCP                    37m
openshift-monitoring                                    service/alertmanager-main                  ClusterIP      172.30.128.198   <none>                                 9094/TCP                     6d8h
openshift-monitoring                                    service/alertmanager-operated              ClusterIP      None             <none>                                 9093/TCP,9094/TCP,9094/UDP   6d8h
openshift-monitoring                                    service/cluster-monitoring-operator        ClusterIP      None             <none>                                 8080/TCP                     6d8h
openshift-monitoring                                    service/grafana                            ClusterIP      172.30.198.155   <none>                                 3000/TCP                     6d8h
openshift-monitoring                                    service/kube-state-metrics                 ClusterIP      None             <none>                                 8443/TCP,9443/TCP            6d8h
openshift-monitoring                                    service/node-exporter                      ClusterIP      None             <none>                                 9100/TCP                     6d8h
openshift-monitoring                                    service/openshift-state-metrics            ClusterIP      None             <none>                                 8443/TCP,9443/TCP            6d8h
openshift-monitoring                                    service/prometheus-adapter                 ClusterIP      172.30.114.73    <none>                                 443/TCP                      6d8h
openshift-monitoring                                    service/prometheus-k8s                     ClusterIP      172.30.64.158    <none>                                 9091/TCP,9092/TCP            6d8h
openshift-monitoring                                    service/prometheus-operated                ClusterIP      None             <none>                                 9090/TCP                     6d8h
openshift-monitoring                                    service/prometheus-operator                ClusterIP      None             <none>                                 8080/TCP                     6d8h
openshift-monitoring                                    service/telemeter-client                   ClusterIP      None             <none>                                 8443/TCP                     6d8h
openshift-multus                                        service/multus-admission-controller        ClusterIP      172.30.228.130   <none>                                 443/TCP                      6d9h
openshift-operator-lifecycle-manager                    service/catalog-operator-metrics           ClusterIP      172.30.219.192   <none>                                 8081/TCP                     6d9h
openshift-operator-lifecycle-manager                    service/olm-operator-metrics               ClusterIP      172.30.104.29    <none>                                 8081/TCP                     6d9h
openshift-operator-lifecycle-manager                    service/v1-packages-operators-coreos-com   ClusterIP      172.30.171.157   <none>                                 443/TCP                      39m
openshift-sdn                                           service/sdn                                ClusterIP      None             <none>                                 9101/TCP                     6d9h
openshift-service-catalog-apiserver-operator            service/metrics                            ClusterIP      172.30.9.246     <none>                                 443/TCP                      6d9h
openshift-service-catalog-controller-manager-operator   service/metrics                            ClusterIP      172.30.197.199   <none>                                 443/TCP                      6d9h

NAMESPACE                                NAME                                         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR                     AGE
openshift-apiserver                      daemonset.apps/apiserver                     1         1         1       1            1           node-role.kubernetes.io/master=   6d9h
openshift-cluster-node-tuning-operator   daemonset.apps/tuned                         1         1         1       1            1           kubernetes.io/os=linux            38m
openshift-controller-manager             daemonset.apps/controller-manager            1         1         1       1            1           node-role.kubernetes.io/master=   6d9h
openshift-dns                            daemonset.apps/dns-default                   1         1         1       1            1           kubernetes.io/os=linux            6d9h
openshift-image-registry                 daemonset.apps/node-ca                       1         1         1       1            1           kubernetes.io/os=linux            6d8h
openshift-machine-config-operator        daemonset.apps/machine-config-daemon         1         1         1       1            1           kubernetes.io/os=linux            6d9h
openshift-machine-config-operator        daemonset.apps/machine-config-server         1         1         1       1            1           node-role.kubernetes.io/master=   6d9h
openshift-monitoring                     daemonset.apps/node-exporter                 1         1         1       1            1           kubernetes.io/os=linux            6d8h
openshift-multus                         daemonset.apps/multus                        1         1         1       1            1           kubernetes.io/os=linux            6d9h
openshift-multus                         daemonset.apps/multus-admission-controller   1         1         1       1            1           node-role.kubernetes.io/master=   6d9h
openshift-sdn                            daemonset.apps/ovs                           1         1         1       1            1           kubernetes.io/os=linux            6d9h
openshift-sdn                            daemonset.apps/sdn                           1         1         1       1            1           kubernetes.io/os=linux            6d9h
openshift-sdn                            daemonset.apps/sdn-controller                1         1         1       1            1           node-role.kubernetes.io/master=   6d9h

NAMESPACE                                               NAME                                                                    READY   UP-TO-DATE   AVAILABLE   AGE
openshift-apiserver-operator                            deployment.apps/openshift-apiserver-operator                            1/1     1            1           6d9h
openshift-authentication-operator                       deployment.apps/authentication-operator                                 1/1     1            1           6d9h
openshift-authentication                                deployment.apps/oauth-openshift                                         2/2     2            2           6d8h
openshift-cloud-credential-operator                     deployment.apps/cloud-credential-operator                               1/1     1            1           6d9h
openshift-cluster-machine-approver                      deployment.apps/machine-approver                                        1/1     1            1           6d9h
openshift-cluster-node-tuning-operator                  deployment.apps/cluster-node-tuning-operator                            1/1     1            1           6d9h
openshift-cluster-samples-operator                      deployment.apps/cluster-samples-operator                                1/1     1            1           6d9h
openshift-cluster-storage-operator                      deployment.apps/cluster-storage-operator                                1/1     1            1           6d9h
openshift-cluster-version                               deployment.apps/cluster-version-operator                                0/0     0            0           6d9h
openshift-console-operator                              deployment.apps/console-operator                                        1/1     1            1           6d8h
openshift-console                                       deployment.apps/console                                                 2/2     2            2           6d8h
openshift-console                                       deployment.apps/downloads                                               2/2     2            2           6d8h
openshift-controller-manager-operator                   deployment.apps/openshift-controller-manager-operator                   1/1     1            1           6d9h
openshift-dns-operator                                  deployment.apps/dns-operator                                            1/1     1            1           6d9h
openshift-image-registry                                deployment.apps/cluster-image-registry-operator                         1/1     1            1           6d9h
openshift-image-registry                                deployment.apps/image-registry                                          1/1     1            1           6d8h
openshift-ingress-operator                              deployment.apps/ingress-operator                                        1/1     1            1           6d9h
openshift-ingress                                       deployment.apps/router-default                                          1/1     1            1           6d8h
openshift-insights                                      deployment.apps/insights-operator                                       1/1     1            1           6d9h
openshift-kube-apiserver-operator                       deployment.apps/kube-apiserver-operator                                 1/1     1            1           6d9h
openshift-kube-controller-manager-operator              deployment.apps/kube-controller-manager-operator                        1/1     1            1           6d9h
openshift-kube-scheduler-operator                       deployment.apps/openshift-kube-scheduler-operator                       1/1     1            1           6d9h
openshift-machine-api                                   deployment.apps/cluster-autoscaler-operator                             0/0     0            0           6d8h
openshift-machine-api                                   deployment.apps/machine-api-controllers                                 1/1     1            1           6d9h
openshift-machine-api                                   deployment.apps/machine-api-operator                                    0/0     0            0           6d9h
openshift-machine-config-operator                       deployment.apps/machine-config-controller                               0/0     0            0           6d9h
openshift-machine-config-operator                       deployment.apps/machine-config-operator                                 0/0     0            0           6d9h
openshift-marketplace                                   deployment.apps/certified-operators                                     1/1     1            1           6d8h
openshift-marketplace                                   deployment.apps/community-operators                                     1/1     1            1           6d8h
openshift-marketplace                                   deployment.apps/marketplace-operator                                    1/1     1            1           6d9h
openshift-marketplace                                   deployment.apps/redhat-operators                                        1/1     1            1           6d8h
openshift-monitoring                                    deployment.apps/cluster-monitoring-operator                             0/0     0            0           6d9h
openshift-monitoring                                    deployment.apps/grafana                                                 0/0     0            0           6d8h
openshift-monitoring                                    deployment.apps/kube-state-metrics                                      0/0     0            0           6d8h
openshift-monitoring                                    deployment.apps/openshift-state-metrics                                 0/0     0            0           6d8h
openshift-monitoring                                    deployment.apps/prometheus-adapter                                      0/0     0            0           6d8h
openshift-monitoring                                    deployment.apps/prometheus-operator                                     0/0     0            0           6d8h
openshift-monitoring                                    deployment.apps/telemeter-client                                        0/0     0            0           6d8h
openshift-network-operator                              deployment.apps/network-operator                                        1/1     1            1           6d9h
openshift-operator-lifecycle-manager                    deployment.apps/catalog-operator                                        1/1     1            1           6d9h
openshift-operator-lifecycle-manager                    deployment.apps/olm-operator                                            1/1     1            1           6d9h
openshift-operator-lifecycle-manager                    deployment.apps/packageserver                                           2/2     2            2           6d9h
openshift-service-ca-operator                           deployment.apps/service-ca-operator                                     1/1     1            1           6d9h
openshift-service-ca                                    deployment.apps/apiservice-cabundle-injector                            1/1     1            1           6d9h
openshift-service-ca                                    deployment.apps/configmap-cabundle-injector                             1/1     1            1           6d9h
openshift-service-ca                                    deployment.apps/service-serving-cert-signer                             1/1     1            1           6d9h
openshift-service-catalog-apiserver-operator            deployment.apps/openshift-service-catalog-apiserver-operator            1/1     1            1           6d9h
openshift-service-catalog-controller-manager-operator   deployment.apps/openshift-service-catalog-controller-manager-operator   1/1     1            1           6d9h

NAMESPACE                                               NAME                                                                              DESIRED   CURRENT   READY   AGE
openshift-apiserver-operator                            replicaset.apps/openshift-apiserver-operator-6db995744c                           1         1         1       6d9h
openshift-authentication-operator                       replicaset.apps/authentication-operator-668f5dd5cb                                1         1         1       6d9h
openshift-authentication                                replicaset.apps/oauth-openshift-6cb69c9fcb                                        0         0         0       4d22h
openshift-authentication                                replicaset.apps/oauth-openshift-7949ccf5d                                         2         2         2       37m
openshift-authentication                                replicaset.apps/oauth-openshift-7fc64cbb8c                                        0         0         0       49m
openshift-authentication                                replicaset.apps/oauth-openshift-bbb4844d5                                         0         0         0       6d8h
openshift-cloud-credential-operator                     replicaset.apps/cloud-credential-operator-846fd45d76                              1         1         1       6d9h
openshift-cluster-machine-approver                      replicaset.apps/machine-approver-d599647f4                                        1         1         1       6d9h
openshift-cluster-node-tuning-operator                  replicaset.apps/cluster-node-tuning-operator-568db95869                           1         1         1       6d9h
openshift-cluster-samples-operator                      replicaset.apps/cluster-samples-operator-84464ff57                                1         1         1       6d9h
openshift-cluster-storage-operator                      replicaset.apps/cluster-storage-operator-6bc658fc74                               1         1         1       6d9h
openshift-cluster-version                               replicaset.apps/cluster-version-operator-65ddc5569d                               0         0         0       6d9h
openshift-cluster-version                               replicaset.apps/cluster-version-operator-6d87fcc576                               0         0         0       6d9h
openshift-console-operator                              replicaset.apps/console-operator-cdc56f566                                        1         1         1       6d8h
openshift-console                                       replicaset.apps/console-55bf5684d6                                                2         2         2       6d8h
openshift-console                                       replicaset.apps/console-6b56655b5                                                 0         0         0       6d8h
openshift-console                                       replicaset.apps/console-d7cc5f5ff                                                 0         0         0       6d8h
openshift-console                                       replicaset.apps/downloads-5bb8997d85                                              2         2         2       6d8h
openshift-controller-manager-operator                   replicaset.apps/openshift-controller-manager-operator-7d857c6dff                  1         1         1       6d9h
openshift-dns-operator                                  replicaset.apps/dns-operator-566bc5d97b                                           1         1         1       6d9h
openshift-image-registry                                replicaset.apps/cluster-image-registry-operator-97d8b7fcb                         1         1         1       6d9h
openshift-image-registry                                replicaset.apps/image-registry-85b59cb6d5                                         1         1         1       6d8h
openshift-ingress-operator                              replicaset.apps/ingress-operator-fbdb949c9                                        1         1         1       6d9h
openshift-ingress                                       replicaset.apps/router-default-746885fd94                                         1         1         1       6d8h
openshift-insights                                      replicaset.apps/insights-operator-d8b996d8f                                       1         1         1       6d9h
openshift-kube-apiserver-operator                       replicaset.apps/kube-apiserver-operator-5cc9ccd675                                1         1         1       6d9h
openshift-kube-controller-manager-operator              replicaset.apps/kube-controller-manager-operator-5dd9c9c59                        1         1         1       6d9h
openshift-kube-scheduler-operator                       replicaset.apps/openshift-kube-scheduler-operator-545747d6f                       1         1         1       6d9h
openshift-machine-api                                   replicaset.apps/cluster-autoscaler-operator-5f6dc59b85                            0         0         0       6d8h
openshift-machine-api                                   replicaset.apps/machine-api-controllers-fcb76c4d5                                 1         1         1       6d9h
openshift-machine-api                                   replicaset.apps/machine-api-operator-6b645465df                                   0         0         0       6d9h
openshift-machine-config-operator                       replicaset.apps/machine-config-controller-6ccb48c449                              0         0         0       6d9h
openshift-machine-config-operator                       replicaset.apps/machine-config-operator-b9d5fd6d                                  0         0         0       6d9h
openshift-marketplace                                   replicaset.apps/certified-operators-6c6cc95955                                    0         0         0       64m
openshift-marketplace                                   replicaset.apps/certified-operators-6db888f478                                    0         0         0       6d8h
openshift-marketplace                                   replicaset.apps/certified-operators-78656bd9c9                                    0         0         0       37m
openshift-marketplace                                   replicaset.apps/certified-operators-7f789459dd                                    0         0         0       50m
openshift-marketplace                                   replicaset.apps/certified-operators-c76bb4784                                     1         1         1       37m
openshift-marketplace                                   replicaset.apps/community-operators-79c9d7f5f8                                    0         0         0       6d8h
openshift-marketplace                                   replicaset.apps/community-operators-8678dc9469                                    1         1         1       37m
openshift-marketplace                                   replicaset.apps/community-operators-9d4db544c                                     0         0         0       50m
openshift-marketplace                                   replicaset.apps/community-operators-bf7c595d                                      0         0         0       64m
openshift-marketplace                                   replicaset.apps/marketplace-operator-7fd7d89795                                   1         1         1       6d9h
openshift-marketplace                                   replicaset.apps/redhat-operators-5f695556ff                                       1         1         1       37m
openshift-marketplace                                   replicaset.apps/redhat-operators-6594f859cd                                       0         0         0       50m
openshift-marketplace                                   replicaset.apps/redhat-operators-78f7b4b78f                                       0         0         0       6d8h
openshift-marketplace                                   replicaset.apps/redhat-operators-cc5cdf444                                        0         0         0       64m
openshift-monitoring                                    replicaset.apps/cluster-monitoring-operator-647cb8b7bf                            0         0         0       6d9h
openshift-monitoring                                    replicaset.apps/grafana-c47f869c7                                                 0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/kube-state-metrics-59fd9b67f5                                     0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/openshift-state-metrics-69d7b8b5d5                                0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/prometheus-adapter-d6578d668                                      0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/prometheus-operator-668f98845c                                    0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/prometheus-operator-bdb767f79                                     0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/telemeter-client-647fb7d797                                       0         0         0       6d8h
openshift-monitoring                                    replicaset.apps/telemeter-client-8b5c9dc6                                         0         0         0       6d8h
openshift-network-operator                              replicaset.apps/network-operator-685d4878c4                                       1         1         1       6d9h
openshift-operator-lifecycle-manager                    replicaset.apps/catalog-operator-765c6f78b7                                       1         1         1       6d9h
openshift-operator-lifecycle-manager                    replicaset.apps/olm-operator-8597cfb57                                            1         1         1       6d9h
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-595959b48b                                          0         0         0       51m
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-5b5d7dc9b                                           0         0         0       67m
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-5cfc5ff89b                                          0         0         0       6d9h
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-65bf47b9bb                                          2         2         2       39m
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-676958774f                                          0         0         0       5d14h
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-7798798999                                          0         0         0       51m
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-8c499dc98                                           0         0         0       6d8h
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-d7b7cc458                                           0         0         0       6d8h
openshift-operator-lifecycle-manager                    replicaset.apps/packageserver-dd88c6b44                                           0         0         0       67m
openshift-service-ca-operator                           replicaset.apps/service-ca-operator-77f4fc8f5d                                    1         1         1       6d9h
openshift-service-ca                                    replicaset.apps/apiservice-cabundle-injector-5b97d64df                            1         1         1       6d9h
openshift-service-ca                                    replicaset.apps/configmap-cabundle-injector-79989ddcb9                            1         1         1       6d9h
openshift-service-ca                                    replicaset.apps/service-serving-cert-signer-7787d496cf                            1         1         1       6d9h
openshift-service-catalog-apiserver-operator            replicaset.apps/openshift-service-catalog-apiserver-operator-8564d47db4           1         1         1       6d9h
openshift-service-catalog-controller-manager-operator   replicaset.apps/openshift-service-catalog-controller-manager-operator-797d9dd57   1         1         1       6d9h

NAMESPACE              NAME                                 READY   AGE
openshift-monitoring   statefulset.apps/alertmanager-main   3/3     6d8h
openshift-monitoring   statefulset.apps/prometheus-k8s      0/0     6d8h

NAMESPACE   NAME                                                                          IMAGE REPOSITORY                                                                                                 TAGS                                                  UPDATED
openshift   imagestream.image.openshift.io/apicast-gateway                                default-route-openshift-image-registry.apps-crc.testing/openshift/apicast-gateway                                2.1.0.GA,2.2.0.GA,2.3.0.GA,2.4.0.GA + 2 more...       6 days ago
openshift   imagestream.image.openshift.io/apicurito-ui                                   default-route-openshift-image-registry.apps-crc.testing/openshift/apicurito-ui                                   1.2,1.3                                               6 days ago
openshift   imagestream.image.openshift.io/cli                                            default-route-openshift-image-registry.apps-crc.testing/openshift/cli                                            latest
openshift   imagestream.image.openshift.io/cli-artifacts                                  default-route-openshift-image-registry.apps-crc.testing/openshift/cli-artifacts                                  latest                                                6 days ago
openshift   imagestream.image.openshift.io/dotnet                                         default-route-openshift-image-registry.apps-crc.testing/openshift/dotnet                                         2.1,2.2,latest                                        6 days ago
openshift   imagestream.image.openshift.io/dotnet-runtime                                 default-route-openshift-image-registry.apps-crc.testing/openshift/dotnet-runtime                                 2.1,2.2,latest                                        6 days ago
openshift   imagestream.image.openshift.io/eap-cd-openshift                               default-route-openshift-image-registry.apps-crc.testing/openshift/eap-cd-openshift                               12,12.0,13,13.0,14,14.0,15,15.0,16,16.0 + 1 more...   6 days ago
openshift   imagestream.image.openshift.io/fis-java-openshift                             default-route-openshift-image-registry.apps-crc.testing/openshift/fis-java-openshift                             1.0,2.0                                               6 days ago
openshift   imagestream.image.openshift.io/fis-karaf-openshift                            default-route-openshift-image-registry.apps-crc.testing/openshift/fis-karaf-openshift                            1.0,2.0                                               6 days ago
openshift   imagestream.image.openshift.io/fuse-apicurito-generator                       default-route-openshift-image-registry.apps-crc.testing/openshift/fuse-apicurito-generator                       1.2,1.3                                               6 days ago
openshift   imagestream.image.openshift.io/fuse7-console                                  default-route-openshift-image-registry.apps-crc.testing/openshift/fuse7-console                                  1.0,1.1,1.2,1.3                                       6 days ago
openshift   imagestream.image.openshift.io/fuse7-eap-openshift                            default-route-openshift-image-registry.apps-crc.testing/openshift/fuse7-eap-openshift                            1.0,1.1,1.2,1.3                                       6 days ago
openshift   imagestream.image.openshift.io/fuse7-java-openshift                           default-route-openshift-image-registry.apps-crc.testing/openshift/fuse7-java-openshift                           1.0,1.1,1.2,1.3                                       6 days ago
openshift   imagestream.image.openshift.io/fuse7-karaf-openshift                          default-route-openshift-image-registry.apps-crc.testing/openshift/fuse7-karaf-openshift                          1.0,1.1,1.2,1.3                                       6 days ago
openshift   imagestream.image.openshift.io/golang                                         default-route-openshift-image-registry.apps-crc.testing/openshift/golang                                         1.11.5,latest                                         6 days ago
openshift   imagestream.image.openshift.io/httpd                                          default-route-openshift-image-registry.apps-crc.testing/openshift/httpd                                          2.4,latest                                            6 days ago
openshift   imagestream.image.openshift.io/installer                                      default-route-openshift-image-registry.apps-crc.testing/openshift/installer                                      latest                                                6 days ago
openshift   imagestream.image.openshift.io/installer-artifacts                            default-route-openshift-image-registry.apps-crc.testing/openshift/installer-artifacts                            latest
openshift   imagestream.image.openshift.io/java                                           default-route-openshift-image-registry.apps-crc.testing/openshift/java                                           11,8,latest                                           6 days ago
openshift   imagestream.image.openshift.io/jboss-amq-62                                   default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-amq-62                                   1.1,1.2,1.3,1.4,1.5,1.6,1.7                           6 days ago
openshift   imagestream.image.openshift.io/jboss-amq-63                                   default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-amq-63                                   1.0,1.1,1.2,1.3,1.4                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-datagrid65-client-openshift              default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datagrid65-client-openshift              1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/jboss-datagrid65-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datagrid65-openshift                     1.2,1.3,1.4,1.5,1.6                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-datagrid71-client-openshift              default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datagrid71-client-openshift              1.0                                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-datagrid71-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datagrid71-openshift                     1.0,1.1,1.2,1.3                                       6 days ago
openshift   imagestream.image.openshift.io/jboss-datagrid72-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datagrid72-openshift                     1.0,1.1,1.2                                           6 days ago
openshift   imagestream.image.openshift.io/jboss-datagrid73-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datagrid73-openshift                     1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/jboss-datavirt64-driver-openshift              default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datavirt64-driver-openshift              1.0,1.1,1.2,1.3,1.4,1.5,1.6                           6 days ago
openshift   imagestream.image.openshift.io/jboss-datavirt64-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-datavirt64-openshift                     1.0,1.1,1.2,1.3,1.4,1.5,1.6                           6 days ago
openshift   imagestream.image.openshift.io/jboss-decisionserver64-openshift               default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-decisionserver64-openshift               1.0,1.1,1.2,1.3,1.4,1.5                               6 days ago
openshift   imagestream.image.openshift.io/jboss-eap64-openshift                          default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-eap64-openshift                          1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9 + 1 more...       6 days ago
openshift   imagestream.image.openshift.io/jboss-eap70-openshift                          default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-eap70-openshift                          1.3,1.4,1.5,1.6,1.7                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-eap71-openshift                          default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-eap71-openshift                          1.1,1.2,1.3,1.4,latest                                6 days ago
openshift   imagestream.image.openshift.io/jboss-eap72-openshift                          default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-eap72-openshift                          1.0,latest                                            6 days ago
openshift   imagestream.image.openshift.io/jboss-fuse70-console                           default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-fuse70-console                           1.0                                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-fuse70-eap-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-fuse70-eap-openshift                     1.0                                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-fuse70-java-openshift                    default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-fuse70-java-openshift                    1.0                                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-fuse70-karaf-openshift                   default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-fuse70-karaf-openshift                   1.0                                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-processserver64-openshift                default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-processserver64-openshift                1.0,1.1,1.2,1.3,1.4,1.5                               6 days ago
openshift   imagestream.image.openshift.io/jboss-webserver30-tomcat7-openshift            default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-webserver30-tomcat7-openshift            1.1,1.2,1.3                                           6 days ago
openshift   imagestream.image.openshift.io/jboss-webserver30-tomcat8-openshift            default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-webserver30-tomcat8-openshift            1.1,1.2,1.3                                           6 days ago
openshift   imagestream.image.openshift.io/jboss-webserver31-tomcat7-openshift            default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-webserver31-tomcat7-openshift            1.0,1.1,1.2,1.3,1.4                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-webserver31-tomcat8-openshift            default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-webserver31-tomcat8-openshift            1.0,1.1,1.2,1.3,1.4                                   6 days ago
openshift   imagestream.image.openshift.io/jboss-webserver50-tomcat9-openshift            default-route-openshift-image-registry.apps-crc.testing/openshift/jboss-webserver50-tomcat9-openshift            1.0,1.1,1.2,latest                                    6 days ago
openshift   imagestream.image.openshift.io/jenkins                                        default-route-openshift-image-registry.apps-crc.testing/openshift/jenkins                                        2,latest                                              6 days ago
openshift   imagestream.image.openshift.io/jenkins-agent-maven                            default-route-openshift-image-registry.apps-crc.testing/openshift/jenkins-agent-maven                            latest,v4.0                                           6 days ago
openshift   imagestream.image.openshift.io/jenkins-agent-nodejs                           default-route-openshift-image-registry.apps-crc.testing/openshift/jenkins-agent-nodejs                           latest,v4.0                                           6 days ago
openshift   imagestream.image.openshift.io/mariadb                                        default-route-openshift-image-registry.apps-crc.testing/openshift/mariadb                                        10.2,latest                                           6 days ago
openshift   imagestream.image.openshift.io/modern-webapp                                  default-route-openshift-image-registry.apps-crc.testing/openshift/modern-webapp                                  10.x,latest                                           6 days ago
openshift   imagestream.image.openshift.io/mongodb                                        default-route-openshift-image-registry.apps-crc.testing/openshift/mongodb                                        3.2,3.4,3.6,latest                                    6 days ago
openshift   imagestream.image.openshift.io/must-gather                                    default-route-openshift-image-registry.apps-crc.testing/openshift/must-gather                                    latest                                                6 days ago
openshift   imagestream.image.openshift.io/mysql                                          default-route-openshift-image-registry.apps-crc.testing/openshift/mysql                                          5.7,8.0,latest                                        6 days ago
openshift   imagestream.image.openshift.io/nginx                                          default-route-openshift-image-registry.apps-crc.testing/openshift/nginx                                          1.10,1.12,latest                                      6 days ago
openshift   imagestream.image.openshift.io/nodejs                                         default-route-openshift-image-registry.apps-crc.testing/openshift/nodejs                                         10,8,8-RHOAR,latest                                   6 days ago
openshift   imagestream.image.openshift.io/openjdk-11-rhel7                               default-route-openshift-image-registry.apps-crc.testing/openshift/openjdk-11-rhel7                               1.0                                                   6 days ago
openshift   imagestream.image.openshift.io/perl                                           default-route-openshift-image-registry.apps-crc.testing/openshift/perl                                           5.24,5.26,latest                                      6 days ago
openshift   imagestream.image.openshift.io/php                                            default-route-openshift-image-registry.apps-crc.testing/openshift/php                                            7.0,7.1,7.2,latest                                    6 days ago
openshift   imagestream.image.openshift.io/postgresql                                     default-route-openshift-image-registry.apps-crc.testing/openshift/postgresql                                     10,9.6,latest                                         6 days ago
openshift   imagestream.image.openshift.io/python                                         default-route-openshift-image-registry.apps-crc.testing/openshift/python                                         2.7,3.5,3.6,latest                                    6 days ago
openshift   imagestream.image.openshift.io/redhat-openjdk18-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/redhat-openjdk18-openshift                     1.0,1.1,1.2,1.3,1.4,1.5                               6 days ago
openshift   imagestream.image.openshift.io/redhat-sso70-openshift                         default-route-openshift-image-registry.apps-crc.testing/openshift/redhat-sso70-openshift                         1.3,1.4                                               6 days ago
openshift   imagestream.image.openshift.io/redhat-sso71-openshift                         default-route-openshift-image-registry.apps-crc.testing/openshift/redhat-sso71-openshift                         1.0,1.1,1.2,1.3                                       6 days ago
openshift   imagestream.image.openshift.io/redhat-sso72-openshift                         default-route-openshift-image-registry.apps-crc.testing/openshift/redhat-sso72-openshift                         1.0,1.1,1.2,1.3,1.4                                   6 days ago
openshift   imagestream.image.openshift.io/redhat-sso73-openshift                         default-route-openshift-image-registry.apps-crc.testing/openshift/redhat-sso73-openshift                         1.0,latest                                            6 days ago
openshift   imagestream.image.openshift.io/redis                                          default-route-openshift-image-registry.apps-crc.testing/openshift/redis                                          3.2,latest                                            6 days ago
openshift   imagestream.image.openshift.io/rhdm73-decisioncentral-indexing-openshift      default-route-openshift-image-registry.apps-crc.testing/openshift/rhdm73-decisioncentral-indexing-openshift      1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhdm73-decisioncentral-openshift               default-route-openshift-image-registry.apps-crc.testing/openshift/rhdm73-decisioncentral-openshift               1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhdm73-kieserver-openshift                     default-route-openshift-image-registry.apps-crc.testing/openshift/rhdm73-kieserver-openshift                     1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhdm73-optaweb-employee-rostering-openshift    default-route-openshift-image-registry.apps-crc.testing/openshift/rhdm73-optaweb-employee-rostering-openshift    1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhpam73-businesscentral-indexing-openshift     default-route-openshift-image-registry.apps-crc.testing/openshift/rhpam73-businesscentral-indexing-openshift     1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhpam73-businesscentral-monitoring-openshift   default-route-openshift-image-registry.apps-crc.testing/openshift/rhpam73-businesscentral-monitoring-openshift   1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhpam73-businesscentral-openshift              default-route-openshift-image-registry.apps-crc.testing/openshift/rhpam73-businesscentral-openshift              1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhpam73-kieserver-openshift                    default-route-openshift-image-registry.apps-crc.testing/openshift/rhpam73-kieserver-openshift                    1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/rhpam73-smartrouter-openshift                  default-route-openshift-image-registry.apps-crc.testing/openshift/rhpam73-smartrouter-openshift                  1.0,1.1                                               6 days ago
openshift   imagestream.image.openshift.io/ruby                                           default-route-openshift-image-registry.apps-crc.testing/openshift/ruby                                           2.3,2.4,2.5,latest                                    6 days ago
openshift   imagestream.image.openshift.io/tests                                          default-route-openshift-image-registry.apps-crc.testing/openshift/tests                                          latest                                                6 days ago

NAMESPACE                  NAME                                         HOST/PORT                                                 PATH   SERVICES            PORT    TERMINATION            WILDCARD
openshift-authentication   route.route.openshift.io/oauth-openshift     oauth-openshift.apps-crc.testing                                 oauth-openshift     6443    passthrough/Redirect   None
openshift-console          route.route.openshift.io/console             console-openshift-console.apps-crc.testing                       console             https   reencrypt/Redirect     None
openshift-console          route.route.openshift.io/downloads           downloads-openshift-console.apps-crc.testing                     downloads           http    edge/Redirect          None
openshift-image-registry   route.route.openshift.io/default-route       default-route-openshift-image-registry.apps-crc.testing          image-registry      <all>   reencrypt              None
openshift-monitoring       route.route.openshift.io/alertmanager-main   alertmanager-main-openshift-monitoring.apps-crc.testing          alertmanager-main   web     reencrypt/Redirect     None
openshift-monitoring       route.route.openshift.io/grafana             grafana-openshift-monitoring.apps-crc.testing                    grafana             https   reencrypt/Redirect     None
openshift-monitoring       route.route.openshift.io/prometheus-k8s      prometheus-k8s-openshift-monitoring.apps-crc.testing             prometheus-k8s      web     reencrypt/Redirect     None

$ oc get crds
NAME                                                        CREATED AT
alertmanagers.monitoring.coreos.com                         2019-09-27T16:37:34Z
apiservers.config.openshift.io                              2019-09-27T16:09:22Z
authentications.config.openshift.io                         2019-09-27T16:09:22Z
authentications.operator.openshift.io                       2019-09-27T16:09:36Z
baremetalhosts.metal3.io                                    2019-09-27T16:13:34Z
builds.config.openshift.io                                  2019-09-27T16:09:22Z
catalogsourceconfigs.operators.coreos.com                   2019-09-27T16:09:34Z
catalogsources.operators.coreos.com                         2019-09-27T16:09:45Z
clusterautoscalers.autoscaling.openshift.io                 2019-09-27T16:09:34Z
clusternetworks.network.openshift.io                        2019-09-27T16:10:26Z
clusteroperators.config.openshift.io                        2019-09-27T16:09:20Z
clusterresourcequotas.quota.openshift.io                    2019-09-27T16:09:21Z
clusterserviceversions.operators.coreos.com                 2019-09-27T16:09:39Z
clusterversions.config.openshift.io                         2019-09-27T16:09:20Z
configs.imageregistry.operator.openshift.io                 2019-09-27T16:09:32Z
configs.samples.operator.openshift.io                       2019-09-27T16:09:33Z
consoleclidownloads.console.openshift.io                    2019-09-27T16:09:33Z
consoleexternalloglinks.console.openshift.io                2019-09-27T16:09:40Z
consolelinks.console.openshift.io                           2019-09-27T16:09:35Z
consolenotifications.console.openshift.io                   2019-09-27T16:09:44Z
consoles.config.openshift.io                                2019-09-27T16:09:22Z
consoles.operator.openshift.io                              2019-09-27T16:09:45Z
containerruntimeconfigs.machineconfiguration.openshift.io   2019-09-27T16:11:26Z
controllerconfigs.machineconfiguration.openshift.io         2019-09-27T16:11:22Z
credentialsrequests.cloudcredential.openshift.io            2019-09-27T16:09:34Z
dnses.config.openshift.io                                   2019-09-27T16:09:23Z
dnses.operator.openshift.io                                 2019-09-27T16:09:34Z
dnsrecords.ingress.operator.openshift.io                    2019-09-27T16:09:34Z
egressnetworkpolicies.network.openshift.io                  2019-09-27T16:10:27Z
featuregates.config.openshift.io                            2019-09-27T16:09:23Z
hostsubnets.network.openshift.io                            2019-09-27T16:10:26Z
imagecontentsourcepolicies.operator.openshift.io            2019-09-27T16:09:23Z
images.config.openshift.io                                  2019-09-27T16:09:23Z
infrastructures.config.openshift.io                         2019-09-27T16:09:23Z
ingresscontrollers.operator.openshift.io                    2019-09-27T16:09:40Z
ingresses.config.openshift.io                               2019-09-27T16:09:23Z
installplans.operators.coreos.com                           2019-09-27T16:09:40Z
kubeapiservers.operator.openshift.io                        2019-09-27T16:09:33Z
kubecontrollermanagers.operator.openshift.io                2019-09-27T16:09:33Z
kubeletconfigs.machineconfiguration.openshift.io            2019-09-27T16:11:24Z
kubeschedulers.operator.openshift.io                        2019-09-27T16:09:35Z
machineautoscalers.autoscaling.openshift.io                 2019-09-27T16:09:39Z
machineconfigpools.machineconfiguration.openshift.io        2019-09-27T16:11:23Z
machineconfigs.machineconfiguration.openshift.io            2019-09-27T16:11:21Z
machinedisruptionbudgets.healthchecking.openshift.io        2019-09-27T16:10:32Z
machinehealthchecks.healthchecking.openshift.io             2019-09-27T16:10:29Z
machines.machine.openshift.io                               2019-09-27T16:10:28Z
machinesets.machine.openshift.io                            2019-09-27T16:10:28Z
mcoconfigs.machineconfiguration.openshift.io                2019-09-27T16:09:37Z
netnamespaces.network.openshift.io                          2019-09-27T16:10:27Z
network-attachment-definitions.k8s.cni.cncf.io              2019-09-27T16:10:22Z
networks.config.openshift.io                                2019-09-27T16:09:24Z
networks.operator.openshift.io                              2019-09-27T16:09:25Z
oauths.config.openshift.io                                  2019-09-27T16:09:24Z
openshiftapiservers.operator.openshift.io                   2019-09-27T16:09:35Z
openshiftcontrollermanagers.operator.openshift.io           2019-09-27T16:09:35Z
operatorgroups.operators.coreos.com                         2019-09-27T16:09:50Z
operatorhubs.config.openshift.io                            2019-09-27T16:09:21Z
operatorsources.operators.coreos.com                        2019-09-27T16:09:39Z
podmonitors.monitoring.coreos.com                           2019-09-27T16:37:36Z
projects.config.openshift.io                                2019-09-27T16:09:24Z
prometheuses.monitoring.coreos.com                          2019-09-27T16:37:34Z
prometheusrules.monitoring.coreos.com                       2019-09-27T16:37:36Z
proxies.config.openshift.io                                 2019-09-27T16:09:21Z
rolebindingrestrictions.authorization.openshift.io          2019-09-27T16:09:21Z
schedulers.config.openshift.io                              2019-09-27T16:09:24Z
securitycontextconstraints.security.openshift.io            2019-09-27T16:09:21Z
servicecas.operator.openshift.io                            2019-09-27T16:09:35Z
servicecatalogapiservers.operator.openshift.io              2019-09-27T16:09:34Z
servicecatalogcontrollermanagers.operator.openshift.io      2019-09-27T16:09:34Z
servicemonitors.monitoring.coreos.com                       2019-09-27T16:37:35Z
subscriptions.operators.coreos.com                          2019-09-27T16:09:45Z
tuneds.tuned.openshift.io                                   2019-09-27T16:09:34Z
```

</p></details></br>

This is not a comprehensive list, to see all the objects, use etcd as before.

# References

**Official Docs**

- https://docs.openshift.com/container-platform/3.11
- https://docs.openshift.com/container-platform/4.1

**OpenShift v4 Vision**

- https://blog.openshift.com/the-modern-software-platform/
- https://blog.openshift.com/openshift-4-a-noops-platform/
- https://blog.openshift.com/openshift-4-install-experience/

**Blogs**

- https://cloudowski.com/articles/10-differences-between-openshift-and-kubernetes/
- https://cloudowski.com/articles/honest-review-of-openshift-4/

# TBA

- auth
  - OAuth Client
