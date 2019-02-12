<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 05/29/2021*

[kubeapps](https://github.com/kubeapps/kubeapps) is a web-based UI for deploying and managing
applications in Kubernetes clusters. The core features of kubeapps include:
- Browse and deploy Helm charts from chart repositories
- Inspect, upgrade and delete Helm-based applications installed in the cluster
- Add custom and private chart repositories (e.g. ChartMuseum, Harbor, etc)
- Browse and provision external services from the Service Catalog and available Service Brokers
- Connect Helm-based applications to external services with Service Catalog Bindings
- Secure authentication and authorization based on Kubernetes Role-Based Access Control

To simply put, kubeapps support web-based UI to manage Helm and Service Catalog.

The set of assets created from kubeapps include:

```sh
$ kubectl get deployments -n kubeapps
NAME                                         READY   UP-TO-DATE   AVAILABLE   AGE
kubeapps                                     2/2     2            2           66m
kubeapps-internal-apprepository-controller   1/1     1            1           66m
kubeapps-internal-assetsvc                   2/2     2            2           66m
kubeapps-internal-dashboard                  2/2     2            2           66m
kubeapps-internal-kubeops                    2/2     2            2           66m
kubeapps-mongodb                             1/1     1            1           66m

$ kubectl get cronjob -n kubeapps
NAME                              SCHEDULE       SUSPEND   ACTIVE   LAST SCHEDULE   AGE
apprepo-kubeapps-sync-bitnami     */10 * * * *   False     0        4m13s           63m
apprepo-kubeapps-sync-incubator   */10 * * * *   False     0        4m13s           63m
apprepo-kubeapps-sync-stable      */10 * * * *   False     0        4m13s           63m
apprepo-kubeapps-sync-svc-cat     */10 * * * *   False     0        4m13s           63m

$ kubectl get crds --all-namespaces
NAME                           CREATED AT
apprepositories.kubeapps.com   2020-05-29T07:07:11Z
```

By default, Service Catalog is not installed, to use Service Catalog integration, we need to:
- deploy service catalog helm charts via kubeapps or command line
- deploy service broker implementation

# Architecture

For architecture of kubeapps, refer to [architecture overview](https://github.com/kubeapps/kubeapps/blob/v1.10.0/docs/architecture/overview.md).
The takeaways are:
- use a CRD to represent repository
- use cronjob to sync upstream helm repository, one for each repository: [bitnami](https://github.com/bitnami/charts), [incubator](https://github.com/helm/charts/tree/master/incubator), [stable](https://github.com/helm/charts/tree/master/stable), [svc-cat](https://github.com/kubernetes-sigs/service-catalog/tree/master/charts)
- use a dedicate component `kubeops` to communicate with helm and other kubernetes resources
