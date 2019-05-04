<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Service Catalog (v0.0.9)](#service-catalog-v009)
  - [Overview](#overview)
  - [Application (e.g. kubernetes deployment)](#application-eg-kubernetes-deployment)
  - [Broker (or ServiceBroker)](#broker-or-servicebroker)
  - [Service (or ServiceClass)](#service-or-serviceclass)
  - [Instance (or ServiceInstance)](#instance-or-serviceinstance)
  - [Binding (or ServiceBinding)](#binding-or-servicebinding)
- [Service Catalog (v0.1.4)](#service-catalog-v014)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Service Catalog (v0.0.9)

Date: 06/10/2017, kubernetes v1.6, project v0.0.9

## Overview

Service catalog is an incubator project to integrate service broker API with Kubernetes. The service
catalog is NOT a service broker itself - it is the `brain` in platform marketplace, i.e.

```
service1 --
           \
service2 --- service broker1
           /                \
service3 --                  \
                              -- service catalog apiserver/controller (platform marketplace)
serviceX --                  /
           \                /
serviceY --- service broker2
           /
serviceZ --
```

## Application (e.g. kubernetes deployment)

Kubernetes uses the term "service" in a different way than Service Catalog does, so to avoid
confusion the term `Application` will refer to the kubernetes deployment artifact that will use
a Service Instance.

## Broker (or ServiceBroker)

A broker represents a service broker in above diagram. For example, the following is a service broker
from bestdatabase.

```yaml
apiVersion: servicecatalog.k8s.io/v1alpha1
kind: Broker
metadata:
  name: ups-broker
spec:
  url: http://ups-broker.ups-broker.svc.cluster.local:8000
status:
  conditions:
  - message: Successfully fetched catalog from broker
    reason: FetchedCatalog
    status: "True"
    type: Ready
```

## Service (or ServiceClass)

Service catalog controller will watch above Broker resource. After a Broker resource is created, the
Service Catalog Controller will receive an event indicating its addition to the datastore. The
controller will then query the Service Broker for the list of available Services. Per service broker
API spec, the url for the above example is:
```
http://ups-broker.ups-broker.svc.cluster.local:8000/v2/catalog
```

Each service will then have a corresponding ServiceClass resource created, e.g. following is a `ServiceClass`:

```yaml
apiVersion: servicecatalog.k8s.io/v1alpha1
kind: ServiceClass
metadata:
  name: user-provided-service
brokerName: ups-broker
externalID: 4F6E6CF6-FFDD-425F-A2C7-3C9258AD2468
bindable: false
planUpdatable: false
plans:
- name: default
  osbFree: true
  externalID: 86064792-7ea2-467b-af93-ac9694d96d52
```

## Instance (or ServiceInstance)

Each independent use of a Service Class is called a Service Instance. Think of `ServiceClass ==
StorageClass`, and `ServiceInstance == PersistentVolume`. For example, following yaml creates an
instance from `user-provided-service`:

```yaml
apiVersion: servicecatalog.k8s.io/v1alpha1
kind: Instance
metadata:
  name: ups-instance
  namespace: test-ns
spec:
  externalID: 34c984e1-4626-4574-8a95-9e500d0d48d3
  planName: default
  serviceClassName: user-provided-service
status:
  conditions:
  - message: The instance was provisioned successfully
    reason: ProvisionedSuccessfully
    status: "True"
    type: Ready
```

## Binding (or ServiceBinding)

Before a service instance can be used it must be "bound" to an Application. This is done by creating
a new Binding resource:

```yaml
apiVersion: servicecatalog.k8s.io/v1alpha1
kind: Binding
metadata:
  name: ups-binding
  namespace: test-ns
spec:
  instanceRef:
    name: ups-instance
  externalID: b041db94-a5a0-41a2-87ae-1025ba760918
  secretName: my-secret
status:
  conditions:
  - message: Injected bind result
    reason: InjectedBindResult
    status: "True"
    type: Ready
```

Notice that the status has a Ready condition set. This means our binding is ready to use. If we look
at the Secrets in our test-ns namespace, we should see a new one created:

```
$ kubectl get secrets -n test-ns
NAME                  TYPE                                  DATA      AGE
default-token-3k61z   kubernetes.io/service-account-token   3         29m
my-secret             Opaque                                2         1m
```

Now that applications in kubernetes can use this secret to consume the service instance.

*References*

- https://github.com/kubernetes-incubator/service-catalog/blob/v0.0.9/docs/
- https://github.com/kubernetes-incubator/service-catalog/blob/v0.0.9/docs/design.md
- https://github.com/kubernetes-incubator/service-catalog/blob/v0.0.9/docs/walkthrough.md
- file://$HOME/code/projects/middleware/servicebroker/servicebroker.md

# Service Catalog (v0.1.4)

Date: 01/21/2019, kubernetes v1.9, project v0.1.4

There is no major updates, expect that now the project use Kubernetes API aggregation feature,
instead of just CRDs. Also, CRD names are updated.

*References*

- https://kubernetes.io/docs/concepts/extend-kubernetes/service-catalog/
- https://github.com/kubernetes-incubator/service-catalog/blob/v0.1.4/docs/
