<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Helm v3](#helm-v3)
- [Experiment (v2)](#experiment-v2)
- [Experiment (v3)](#experiment-v3)
- [Projects](#projects)
  - [helm-operator](#helm-operator)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Helm is a tool for managing Kubernetes charts. Charts are packages of pre-configured Kubernetes
resources. The goal of helm is to be the package manager for Kubernetes, just like apt-get for
Debian, homebrew for MacOS.

For Helm, there are three important concepts:
- The **chart** is a bundle of information necessary to create an instance of a Kubernetes application.
- The **config** contains config information that can be merged into a packaged chart to create a releasable object.
- A **release** is a running instance of a chart, combined with a specific config.

# Helm v3

Helm v3 is a large rewrite of the helm core, with minimal changes to user interface and APIs.
Changes in helm v3 include:
- Removal of Tiller
- Improved Upgrade Strategy: 3-way Strategic Merge Patches
- Release Names are now scoped to the Namespace
- Secrets as the default storage driver
- Go import path changes
- Capabilities
- Validating Chart Values with JSONSchema
- Consolidation of requirements.yaml into Chart.yaml
- Name (or --generate-name) is now required on install
- Pushing Charts to OCI Registries
- Removal of `helm serve`
- Library chart support
- Chart.yaml apiVersion bump
- XDG Base Directory Support
- CLI Command Renames
- (Do Not) Automatically creating namespaces

For more information, see [changes since helm 2](https://helm.sh/docs/faq/#changes-since-helm-2).
Below is a few takeaways:
- For Kubernetes native system, it's better to directly use Kubernetes API, to leverage its security
  constructs. As mentioned in the doc: Tiller's release management system did not need to rely upon
  an in-cluster operator to maintain state or act as a central hub for Helm release information.
  Instead, we could simply fetch information from the Kubernetes API server, render the Charts
  client-side, and store a record of the installation in Kubernetes.
- For any tool built on top of Kubernetes, it's possible that user changes cluster state via `kubectl`,
  which makes its bookkeeping outdate. Helm v2 will flush the changes based on its own storage, i.e.
  information in its configmap; in helm v3, it performs 3-way strategic merge to solve the problem.
- It's not clear when setting default value is appropriate. The lesson from helm is that:
  - don't automatically create name for release
  - don't automatically provide a default repository
  - don't automatically create namespaces
  - do automatically delete real resources when calling delete (instead of just helm data)
- For command line naming and conventions:
  - helm delete -> helm uninstall
  - helm inspect -> helm show
  - helm fetch -> helm pull
  - helm delete ~~--purge~~: purge by default
- It's trendy to store artifacts (here, charts) in OCR registry.

[Architecture-wise](https://helm.sh/docs/topics/architecture/), Helm v3 is a single command line
tool with no additional components or CRDs.

# Experiment (v2)

**Installation**

After downloading helm binary, just run:

```
helm init
```

Note when RBAC are enabled, we also need to set **RBAC for Tiler**:

```bash
kubectl create serviceaccount --namespace kube-system tiller
kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'
```

All data, configuration related to helm are located under `~/.helm`:

```bash
$ ls ~/.helm
cache  plugins  repository  starters
```

**Chart & Release**

Helm includes a default repository with [stable charts](https://github.com/helm/charts). To install
a chart, simply do:

```
$ helm repo update # make sure charts are up-to-date
$ helm install stable/mysql

$ helm list
NAME            REVISION        UPDATED                         STATUS          CHART           APP VERSION     NAMESPACE
unsung-moose    1               Sun May 10 16:18:14 2020        DEPLOYED        mysql-1.6.3     5.7.28          default
```

Note here:
- Usually, we will use a config file, e.g. `helm install -f config.yaml stable/wordpress`;
- Helm command includes many options, e.g. install into different namespaces;
- After installing, we can list, upgrade, inspect, delete releases.

Implementation-wise, it's important to note that helm use configmaps to store release versions for
features like rollback. For more information, see [how-helm-uses-configmaps-to-store-data](http://technosophos.com/2017/03/23/how-helm-uses-configmaps-to-store-data.html).

```
$ kubectl get configmap --all-namespaces
NAMESPACE     NAME                                 DATA   AGE
default       unsung-moose-mysql-test              1      11m
kube-system   extension-apiserver-authentication   6      56m
kube-system   kube-dns                             0      56m
kube-system   unsung-moose.v1                      1      11m
```

**Development**

To develop helm locally:

- switch to helm repository and `make bootstrap` to install tools and vendors
- run `make build` to build binary
- run `./bin/tilter` to run a local tilter server which will talk to kubernetes cluster defined in ~/.kube/config
- run `export HELM_HOST=localhost:44134` to tell helm client to talk to this local tilter server
- use `./bin/helm` to start helm client

To test without actually installing chart, use `--dry-run` flag.

# Experiment (v3)

**Install charts in v3**

Helm v3 doesn't provide a default repository, thus we need to first add repository:

```
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com/

# Based on XDG specification.
$ ls ~/.cache/helm
repository

$ helm search repo stable
...
```

Similar to helm v3, we can install, uninstall charts, e.g.

```
$ helm install stable/mysql --namespace=helm-demo --generate-name --create-namespace
NAME: mysql-1589104566
...

$ helm uninstall mysql-1589104566 -n helm-demo
...
```

**Create charts and lint**

To create a new chart:

```
$ helm create mychart
...
```

To lint helm `values.yaml`, we can put a file `values.schema.json` in the same directory and run:

```
$ helm lint .
==> Linting .
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

# Projects

## helm-operator

[helm-operator](https://docs.fluxcd.io/projects/helm-operator/en/stable/) is a project in fluxcd to
manage helm release declaratively, primarily for GitOps use case. The core of the project is a CRD
named `HelmRelease` and an operator for managing the resource: **any changes made directly via `helm`
will be reverted back by the operator.**

Once an `HelmRelease` is created, the operator will pull the charts from specified location and
create a Helm release:

<details><summary>Create HelmRelease</summary><p>

```
$ cat <<EOF | kubectl apply -f -
apiVersion: helm.fluxcd.io/v1
kind: HelmRelease
metadata:
  name: podinfo
  namespace: default
spec:
  chart:
    repository: https://stefanprodan.github.io/podinfo
    name: podinfo
    version: 3.2.0
EOF
helmrelease.helm.fluxcd.io/podinfo created


$ kubectl describe hr podinfo
Name:         podinfo
Namespace:    default
Labels:       <none>
Annotations:  kubectl.kubernetes.io/last-applied-configuration:
                {"apiVersion":"helm.fluxcd.io/v1","kind":"HelmRelease","metadata":{"annotations":{},"name":"podinfo","namespace":"default"},"spec":{"chart...
API Version:  helm.fluxcd.io/v1
Kind:         HelmRelease
Metadata:
  Creation Timestamp:  2020-05-30T14:24:48Z
  Generation:          1
  Resource Version:    382
  Self Link:           /apis/helm.fluxcd.io/v1/namespaces/default/helmreleases/podinfo
  UID:                 c9ad2b25-c61a-4570-b7b9-498a786ff105
Spec:
  Chart:
    Name:        podinfo
    Repository:  https://stefanprodan.github.io/podinfo
    Version:     3.2.0
Status:
  Conditions:
    Last Transition Time:   2020-05-30T14:24:56Z
    Last Update Time:       2020-05-30T14:24:56Z
    Message:                Chart fetch was successful for Helm release 'default-podinfo' in 'default'.
    Reason:                 ChartFetched
    Status:                 True
    Type:                   ChartFetched
    Last Transition Time:   2020-05-30T14:24:58Z
    Last Update Time:       2020-05-30T14:24:58Z
    Message:                Release was successful for Helm release 'default-podinfo' in 'default'.
    Reason:                 Succeeded
    Status:                 True
    Type:                   Released
  Last Attempted Revision:  3.2.0
  Observed Generation:      1
  Phase:                    Succeeded
  Revision:                 3.2.0
Events:
  Type    Reason         Age   From           Message
  ----    ------         ----  ----           -------
  Normal  ReleaseSynced  2s    helm-operator  managed release 'default-podinfo' in namespace 'default' synchronized
```

</p></details></br>

The release created from HelmRelease will be visible in Helm:

```
$ kubectl get configmap --all-namespaces
NAMESPACE     NAME                                 DATA   AGE
flux          helm-operator-kube-config            1      26m
kube-system   extension-apiserver-authentication   6      27m
kube-system   kube-dns                             0      27m


$ helm list --all-namespaces
NAME           	NAMESPACE	REVISION	UPDATED                                	STATUS  	CHART              	APP VERSION
default-podinfo	default  	1       	2020-05-30 14:24:58.743383812 +0000 UTC	deployed	podinfo-3.2.0      	3.2.0
helm-operator  	flux     	1       	2020-05-30 22:24:19.341574532 +0800 CST	deployed	helm-operator-1.1.0	1.1.0
```
