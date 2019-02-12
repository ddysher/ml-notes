<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
  - [operator-sdk](#operator-sdk)
  - [operator lifecycle manager (olm)](#operator-lifecycle-manager-olm)
  - [operator registry](#operator-registry)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 05/21/2020, v0.17.0*

The Operator Framework is a project to create, manage and automate Operators. For more information,
refer to the [introduction blog post](https://coreos.com/blog/introducing-operator-framework).
Operator Framework consists of several components, including:
- [operator-sdk](https://github.com/operator-framework/operator-sdk)
- [operator lifycycle manager](https://github.com/operator-framework/operator-lifecycle-manager)
- [operator registry](https://github.com/operator-framework/operator-registry)

# Components

## operator-sdk

The Operator SDK is a framework that uses the `controller-runtime` library (and `kubebuilder` tool)
to make writing operators easier by providing:
- High level APIs and abstractions to write the operational logic more intuitively
- Tools for scaffolding and code generation to bootstrap a new project fast
- Extensions to cover common operator use cases

Using operator-sdk to create an operator is fairly easy:
- run `operator-sdk new` to init a new project
- run `operator-sdk add api` to add a new api under `pkg/apis/`
- update api types, under `pkg/apis/{group}/v1alpha1/{kind}_types.go`
- run `operator-sdk generate crds` to generate crd manifest based api definition
- run `operator-sdk add controller` to add a new controller under `pkg/controller`
- update business logic in `pkg/controller/{kind}/{kind}_controller.go`
- run `operator-sdk build` to build image
- run `operator-skd run local` to run operator directly
- repeat

## operator lifecycle manager (olm)

OLM extends Kubernetes to provide a declarative way to install, manage, and upgrade Operators and
their dependencies in a cluster. It provides the following features:
- over-the-air updates and catalogs
- dependency model
- discoverability
- cluster stability
- declarative ui controls

Concepts in OLM:
- Bundle: A bundle typically includes a `ClusterServiceVersion` and the CRDs that define the owned
  APIs of the CSV in its manifest directory; bundle is stored using container image. For example:
  ```
   etcd
   ├── manifests
   │   ├── etcdcluster.crd.yaml
   │   └── etcdoperator.clusterserviceversion.yaml
   └── metadata
       └── annotations.yaml
   ```
- Catalog: A list of bundles available to install and being kept up to date.
- CatalogSource: A backend for serving Catalog, e.g. operator registry (see blow).
- Channel: channel maps to a particular application definition, allow package authors to write
  different upgrade paths for different users, e.g. alpha vs beta.

OLM has integration with operator-sdk, to install OLM, run:

<details><summary>Install OLM</summary><p>

```
$ operator-sdk olm install --version 0.14.1
INFO[0000] Fetching CRDs for version "0.14.1"
INFO[0002] Fetching resources for version "0.14.1"
INFO[0008] Creating CRDs and resources
INFO[0008]   Creating CustomResourceDefinition "clusterserviceversions.operators.coreos.com"
INFO[0008]   Creating CustomResourceDefinition "installplans.operators.coreos.com"
INFO[0008]   Creating CustomResourceDefinition "subscriptions.operators.coreos.com"
INFO[0008]   Creating CustomResourceDefinition "catalogsources.operators.coreos.com"
INFO[0008]   Creating CustomResourceDefinition "operatorgroups.operators.coreos.com"
INFO[0008]   Creating Namespace "olm"
INFO[0008]   Creating Namespace "operators"
INFO[0008]   Creating ServiceAccount "olm/olm-operator-serviceaccount"
INFO[0008]   Creating ClusterRole "system:controller:operator-lifecycle-manager"
INFO[0008]   Creating ClusterRoleBinding "olm-operator-binding-olm"
INFO[0008]   Creating Deployment "olm/olm-operator"
INFO[0008]   Creating Deployment "olm/catalog-operator"
INFO[0008]   Creating ClusterRole "aggregate-olm-edit"
INFO[0008]   Creating ClusterRole "aggregate-olm-view"
INFO[0008]   Creating OperatorGroup "operators/global-operators"
INFO[0010]   Creating OperatorGroup "olm/olm-operators"
INFO[0010]   Creating ClusterServiceVersion "olm/packageserver"
INFO[0010]   Creating CatalogSource "olm/operatorhubio-catalog"
INFO[0012] Waiting for deployment/olm-operator rollout to complete
INFO[0012]   Waiting for Deployment "olm/olm-operator" to rollout: 0 of 1 updated replicas are available
INFO[0055]   Deployment "olm/olm-operator" successfully rolled out
INFO[0055] Waiting for deployment/catalog-operator rollout to complete
INFO[0055]   Waiting for Deployment "olm/catalog-operator" to rollout: 0 of 1 updated replicas are available
INFO[0062]   Deployment "olm/catalog-operator" successfully rolled out
INFO[0062] Waiting for deployment/packageserver rollout to complete
INFO[0062]   Waiting for Deployment "olm/packageserver" to rollout: 1 of 2 updated replicas are available
INFO[0063]   Deployment "olm/packageserver" successfully rolled out
INFO[0063] Successfully installed OLM version "0.14.1"

NAME                                            NAMESPACE    KIND                        STATUS
clusterserviceversions.operators.coreos.com                  CustomResourceDefinition    Installed
installplans.operators.coreos.com                            CustomResourceDefinition    Installed
subscriptions.operators.coreos.com                           CustomResourceDefinition    Installed
catalogsources.operators.coreos.com                          CustomResourceDefinition    Installed
operatorgroups.operators.coreos.com                          CustomResourceDefinition    Installed
olm                                                          Namespace                   Installed
operators                                                    Namespace                   Installed
olm-operator-serviceaccount                     olm          ServiceAccount              Installed
system:controller:operator-lifecycle-manager                 ClusterRole                 Installed
olm-operator-binding-olm                                     ClusterRoleBinding          Installed
olm-operator                                    olm          Deployment                  Installed
catalog-operator                                olm          Deployment                  Installed
aggregate-olm-edit                                           ClusterRole                 Installed
aggregate-olm-view                                           ClusterRole                 Installed
global-operators                                operators    OperatorGroup               Installed
olm-operators                                   olm          OperatorGroup               Installed
packageserver                                   olm          ClusterServiceVersion       Installed
operatorhubio-catalog                           olm          CatalogSource               Installed
```

</p></details></br>

<details><summary>View Installed OLM Resources</summary><p>

```
$ kubectl get pods -n olm
NAME                                                  READY   STATUS    RESTARTS   AGE
catalog-operator-64b6b59c4f-btf8k                     1/1     Running   0          63m
olm-operator-844fb69f58-6m64w                         1/1     Running   0          63m
operatorhubio-catalog-k6zg8                           1/1     Running   6          62m
packageserver-85d9cd6985-7qkvg                        1/1     Running   0          63m
packageserver-85d9cd6985-9dk7b                        1/1     Running   0          63m

$ kubectl get crds
NAME                                          CREATED AT
catalogsources.operators.coreos.com           2020-05-21T01:40:19Z
clusterserviceversions.operators.coreos.com   2020-05-21T01:40:19Z
installplans.operators.coreos.com             2020-05-21T01:40:19Z
operatorgroups.operators.coreos.com           2020-05-21T01:40:19Z
subscriptions.operators.coreos.com            2020-05-21T01:40:19Z
```

</p></details></br>

The main use case of OLM is the lifecycle management of operators. To use OLM with operator, we need
to create ClusterServiceVersion for an operator and a corresponding bundle:

<details><summary>Generate CSV and Bundle</summary><p>

```
$ operator-sdk generate csv --csv-version 0.1.0
INFO[0000] Generating CSV manifest version 0.1.0
INFO[0004] Fill in the following required fields in file memcached-operator.clusterserviceversion.yaml:
        spec.description
        spec.keywords
        spec.provider
INFO[0004] CSV manifest generated successfully

$ operator-sdk bundle create --generate-only
INFO[0000] Building annotations.yaml
INFO[0000] Generating output manifests directory
INFO[0000] Building Dockerfile
```

</p></details></br>

For testing, run the following command, which will create memcached operator as well as an operator
registry:

<details><summary>Create Memcached Operator</summary><p>

```
$ operator-sdk run --olm --operator-version 0.1.0
INFO[0000] loading Bundles                               dir=deploy/olm-catalog/memcached-operator
INFO[0000] directory                                     dir=deploy/olm-catalog/memcached-operator file=memcached-operator load=bundles
INFO[0000] directory                                     dir=deploy/olm-catalog/memcached-operator file=manifests load=bundles
INFO[0000] found csv, loading bundle                     dir=deploy/olm-catalog/memcached-operator file=memcached-operator.clusterservi
ceversion.yaml load=bundles
INFO[0000] loading bundle file                           dir=deploy/olm-catalog/memcached-operator/manifests file=cache.example.com_mem
cacheds_crd.yaml load=bundle
INFO[0000] loading bundle file                           dir=deploy/olm-catalog/memcached-operator/manifests file=memcached-operator.cl
usterserviceversion.yaml load=bundle
INFO[0000] directory                                     dir=deploy/olm-catalog/memcached-operator file=metadata load=bundles
INFO[0000] loading Packages and Entries                  dir=deploy/olm-catalog/memcached-operator
INFO[0000] directory                                     dir=deploy/olm-catalog/memcached-operator file=memcached-operator load=package
INFO[0000] directory                                     dir=deploy/olm-catalog/memcached-operator file=manifests load=package
INFO[0000] directory                                     dir=deploy/olm-catalog/memcached-operator file=metadata load=package
INFO[0000] Creating registry
INFO[0000]   Creating ConfigMap "olm/memcached-operator-registry-bundles"
INFO[0000]   Creating Deployment "olm/memcached-operator-registry-server"
INFO[0000]   Creating Service "olm/memcached-operator-registry-server"
INFO[0000] Waiting for Deployment "olm/memcached-operator-registry-server" rollout to complete
INFO[0000]   Waiting for Deployment "olm/memcached-operator-registry-server" to rollout: 0 out of 1 new replicas have been updated
INFO[0001]   Waiting for Deployment "olm/memcached-operator-registry-server" to rollout: 0 of 1 updated replicas are available
INFO[0089]   Deployment "olm/memcached-operator-registry-server" successfully rolled out
INFO[0089] Creating resources
INFO[0089]   Creating CatalogSource "default/memcached-operator-ocs"
INFO[0089]   Creating Subscription "default/memcached-operator-v0-1-0-sub"
INFO[0089]   Creating OperatorGroup "default/operator-sdk-og"
INFO[0089] Waiting for ClusterServiceVersion "default/memcached-operator.v0.1.0" to reach 'Succeeded' phase
INFO[0089]   Waiting for ClusterServiceVersion "default/memcached-operator.v0.1.0" to appear
INFO[0093]   Found ClusterServiceVersion "default/memcached-operator.v0.1.0" phase: Pending
INFO[0095]   Found ClusterServiceVersion "default/memcached-operator.v0.1.0" phase: InstallReady
INFO[0096]   Found ClusterServiceVersion "default/memcached-operator.v0.1.0" phase: Installing
INFO[0098]   Found ClusterServiceVersion "default/memcached-operator.v0.1.0" phase: Succeeded
INFO[0098] Successfully installed "memcached-operator.v0.1.0" on OLM version "0.14.1"
NAME                            NAMESPACE    KIND                        STATUS
memcached-operator.v0.1.0       default      ClusterServiceVersion       Installed
memcacheds.cache.example.com    default      CustomResourceDefinition    Installed
```

</p></details></br>

<details><summary>View Installed Resources</summary><p>

```
$ kubectl get pods
NAME                                 READY   STATUS    RESTARTS   AGE
memcached-operator-8cfbcd9d8-hq5zr   1/1     Running   0          22m

$ kubectl get pods --all-namespaces
NAMESPACE     NAME                                                  READY   STATUS    RESTARTS   AGE
default       memcached-operator-8cfbcd9d8-hq5zr                    1/1     Running   0          22m
kube-system   kube-dns-547db76c8f-cvrlf                             3/3     Running   0          92m
olm           catalog-operator-64b6b59c4f-btf8k                     1/1     Running   0          65m
olm           memcached-operator-registry-server-6c6c7696cb-bpx8f   1/1     Running   0          23m
olm           olm-operator-844fb69f58-6m64w                         1/1     Running   0          65m
olm           operatorhubio-catalog-k6zg8                           1/1     Running   6          64m
olm           packageserver-85d9cd6985-7qkvg                        1/1     Running   0          64m
olm           packageserver-85d9cd6985-9dk7b                        1/1     Running   0          64m

$ kubectl get crds
NAME                                          CREATED AT
catalogsources.operators.coreos.com           2020-05-21T01:40:19Z
clusterserviceversions.operators.coreos.com   2020-05-21T01:40:19Z
installplans.operators.coreos.com             2020-05-21T01:40:19Z
memcacheds.cache.example.com                  2020-05-21T02:22:58Z
operatorgroups.operators.coreos.com           2020-05-21T01:40:19Z
subscriptions.operators.coreos.com            2020-05-21T01:40:19Z
```

</p></details></br>

## operator registry

Operator Registry runs in a Kubernetes or OpenShift cluster to provide operator catalog data to OLM.
In an other word, once a bundle (packed in container image) is published via `docker push`,
operator-registry is where bundle discovery is implemented. It uses an "index image" to index all
bundles for OLM to consume.

Running a operator registry is done by creating `ConfigSource`:

```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: CatalogSource
metadata:
  name: example-manifests
  namespace: default
spec:
  sourceType: grpc
  image: example-registry:latest
```

Now to consume bundle in the registry via OLM, create a `Subscription`:

```
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: etcd-subscription
  namespace: default
spec:
  channel: alpha
  name: etcd
  source: example-manifests
  sourceNamespace: default
```

Note in the above OLM related commands, registry is already installed, i.e. `memcached-operator-registry-server`
and `operatorhubio-catalog`.

<details><summary>View Installed Registries</summary><p>

```
$ kubectl get pods -n olm memcached-operator-registry-server-6c6c7696cb-bpx8f -o wide
NAME                                                  READY   STATUS    RESTARTS   AGE    IP           NODE        NOMINATED NODE   RE
ADINESS GATES
memcached-operator-registry-server-6c6c7696cb-bpx8f   1/1     Running   0          170m   172.17.0.7   127.0.0.1   <none>           <none>

$ grpcurl -plaintext 172.17.0.7:50051 api.Registry/ListPackages
{
  "name": "memcached-operator"
}


$ kubectl get pods -n olm operatorhubio-catalog-k6zg8 -o wide
NAME                          READY   STATUS    RESTARTS   AGE    IP           NODE        NOMINATED NODE   READINESS GATES
operatorhubio-catalog-k6zg8   1/1     Running   6          101m   172.17.0.8   127.0.0.1   <none>           <none>

$ grpcurl -plaintext 172.17.0.8:50051 api.Registry/ListPackages
{
  "name": "akka-cluster-operator"
}
{
  "name": "anchore-engine"
}
{
  "name": "api-operator"
}
{
  "name": "apicast-community-operator"
}
{
  "name": "appdynamics-operator"
}
{
  "name": "appranix"
}
{
  "name": "appsody-operator"
}
{
  "name": "aqua"
}
{
  "name": "argocd-operator"
}
{
  "name": "argocd-operator-helm"
}
{
  "name": "atlasmap-operator"
}
{
  "name": "awss3-operator-registry"
}
{
  "name": "banzaicloud-kafka-operator"
}
{
  "name": "camel-k"
}
{
  "name": "cassandra-operator"
}
{
  "name": "chaosblade-operator"
}
{
  "name": "clickhouse"
}
{
  "name": "cockroachdb"
}
{
  "name": "composable-operator"
}
{
  "name": "container-security-operator"
}
{
  "name": "cos-bucket-operator"
}
{
  "name": "couchbase-enterprise"
}
{
  "name": "couchdb-operator"
}
{
  "name": "crossplane"
}
{
  "name": "csi-operator"
}
{
  "name": "datadog-operator"
}
{
  "name": "eclipse-che"
}
{
  "name": "elastic-cloud-eck"
}
{
  "name": "enmasse"
}
{
  "name": "esindex-operator"
}
{
  "name": "etcd"
}
{
  "name": "eunomia"
}
{
  "name": "event-streams-topic"
}
{
  "name": "ext-postgres-operator"
}
{
  "name": "falco"
}
{
  "name": "federatorai"
}
{
  "name": "grafana-operator"
}
{
  "name": "halkyon"
}
{
  "name": "ham-deploy"
}
{
  "name": "hazelcast-enterprise-operator"
}
{
  "name": "hazelcast-jet-enterprise-operator"
}
{
  "name": "hazelcast-jet-operator"
}
{
  "name": "hazelcast-operator"
}
{
  "name": "hive-operator"
}
{
  "name": "hpa-operator"
}
{
  "name": "hpe-csi-driver-operator"
}
{
  "name": "ibm-block-csi-operator-community"
}
{
  "name": "ibm-spectrum-scale-csi-operator"
}
{
  "name": "ibmcloud-operator"
}
{
  "name": "infinispan"
}
{
  "name": "instana-agent"
}
{
  "name": "iot-simulator"
}
{
  "name": "istio"
}
{
  "name": "jaeger"
}
{
  "name": "jenkins-operator"
}
{
  "name": "keda"
}
{
  "name": "keycloak-operator"
}
{
  "name": "kiali"
}
{
  "name": "knative-eventing-operator"
}
{
  "name": "knative-serving-operator"
}
{
  "name": "kong"
}
{
  "name": "kube-arangodb"
}
{
  "name": "kubefed-operator"
}
{
  "name": "kubeflow"
}
{
  "name": "kubemq-operator"
}
{
  "name": "kubernetes-imagepuller-operator"
}
{
  "name": "kubestone"
}
{
  "name": "kubeturbo"
}
{
  "name": "kubevirt"
}
{
  "name": "lib-bucket-provisioner"
}
{
  "name": "lightbend-console-operator"
}
{
  "name": "litmuschaos"
}
{
  "name": "mariadb-operator-app"
}
{
  "name": "mattermost-operator"
}
{
  "name": "metering-upstream"
}
{
  "name": "microcks"
}
{
  "name": "minio-operator"
}
{
  "name": "mongodb-enterprise"
}
{
  "name": "multicluster-operators-subscription"
}
{
  "name": "myvirtualdirectory"
}
{
  "name": "neuvector-operator"
}
{
  "name": "nexus-operator-m88i"
}
{
  "name": "noobaa-operator"
}
{
  "name": "nsm-operator-registry"
}
{
  "name": "nuodb-operator-bundle"
}
{
  "name": "oneagent"
}
{
  "name": "open-liberty"
}
{
  "name": "openebs"
}
{
  "name": "opsmx-spinnaker-operator"
}
{
  "name": "percona-server-mongodb-operator"
}
{
  "name": "percona-xtradb-cluster-operator"
}
{
  "name": "planetscale"
}
{
  "name": "portworx"
}
{
  "name": "postgres-operator"
}
{
  "name": "postgresql"
}
{
  "name": "postgresql-operator"
}
{
  "name": "postgresql-operator-dev4devs-com"
}
{
  "name": "prisma-cloud-compute-console-operator"
}
{
  "name": "prometheus"
}
{
  "name": "quay"
}
{
  "name": "radanalytics-spark"
}
{
  "name": "redis-enterprise"
}
{
  "name": "redis-operator"
}
{
  "name": "ripsaw"
}
{
  "name": "robin-operator"
}
{
  "name": "rook-ceph"
}
{
  "name": "rook-edgefs"
}
{
  "name": "rqlite-operator"
}
{
  "name": "runtime-component-operator"
}
{
  "name": "seldon-operator"
}
{
  "name": "sematext"
}
{
  "name": "siddhi-operator"
}
{
  "name": "skydive-operator"
}
{
  "name": "snapscheduler"
}
{
  "name": "spark-gcp"
}
{
  "name": "spinnaker-operator"
}
{
  "name": "splunk"
}
{
  "name": "storageos"
}
{
  "name": "strimzi-kafka-operator"
}
{
  "name": "submariner"
}
{
  "name": "synopsys"
}
{
  "name": "sysdig"
}
{
  "name": "t8c"
}
{
  "name": "tidb-operator"
}
{
  "name": "traefikee-operator"
}
{
  "name": "vault"
}
{
  "name": "wavefront"
}
{
  "name": "wildfly"
}
{
  "name": "wso2am-operator"
}
{
  "name": "yugabyte-operator"
}
```

</p></details></br>
