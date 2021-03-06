<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [20171201 - cluster api](#20171201---cluster-api)
  - [20180707 - componentconfig api types to staging](#20180707---componentconfig-api-types-to-staging)
- [Feature & Design](#feature--design)
  - [(large) federation v2](#large-federation-v2)
  - [(small) federation cluster selector](#small-federation-cluster-selector)
  - [(deprecated) federation v1](#deprecated-federation-v1)
  - [(deprecated) cluster registry](#deprecated-cluster-registry)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes multicluster.

- [SIG-Cluster-Lifecycle KEPs](https://github.com/kubernetes/enhancements/tree/master/keps/sig-cluster-lifecycle)
- [SIG-Cluster-Lifecycle Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/cluster-lifecycle)
- [SIG-Cluster-Lifecycle Community](https://github.com/kubernetes/community/tree/master/sig-cluster-lifecycle)
- [SIG-Multicluster Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/multicluster)
- [SIG-Multicluster Community](https://github.com/kubernetes/community/tree/master/sig-multicluster)

# KEPs

## 20171201 - cluster api

- *Date: 2020/06/26*

Official introduction:

> The Cluster API is a Kubernetes project to bring declarative, Kubernetes-style APIs to cluster
> creation, configuration, and management. It provides optional, additive functionality on top of
> core Kubernetes.

The set of APIs proposed in cluster-api includes:
- Cluster
- Machine
- MachineSet
- MachineDeployment
- MachineHealthcheck
- etc

<details><summary>CRDs created in cluster-api project</summary><p>

```
$ kubectl get crds | grep cluster.x-k8s.io
clusters.cluster.x-k8s.io                            2020-06-26T08:02:31Z
kubeadmconfigs.bootstrap.cluster.x-k8s.io            2020-06-26T08:02:35Z
kubeadmconfigtemplates.bootstrap.cluster.x-k8s.io    2020-06-26T08:02:36Z
kubeadmcontrolplanes.controlplane.cluster.x-k8s.io   2020-06-26T08:02:39Z
machinedeployments.cluster.x-k8s.io                  2020-06-26T08:02:31Z
machinehealthchecks.cluster.x-k8s.io                 2020-06-26T08:02:32Z
machinepools.exp.cluster.x-k8s.io                    2020-06-26T08:02:32Z
machines.cluster.x-k8s.io                            2020-06-26T08:02:32Z
machinesets.cluster.x-k8s.io                         2020-06-26T08:02:32Z
providers.clusterctl.cluster.x-k8s.io                2020-06-26T08:01:37Z
```

</p></details></br>

The core controllers of cluster-api manage cluster lifecycle, machine lifecycle, etc, and a lot of
provider-specific details are implemented outside of cluster-api (cluster-api defines rules around
defining provider-specific APIs for conformance). There are two different kinds of providers:
- bootstrap provider: provider that used to provision Kubernetes, e.g. kubeadm
- infrastructure provider: provider that runs underline infrastructure, e.g. [cluster-api-provider-aws](https://github.com/kubernetes-sigs/cluster-api-provider-aws).

The default bootstrap provider kubeadm is usually deployed with cluster-api, while infrastructure
providers are added on-demand. Generally, both type of providers consist of:
- controller: runs the core business logic
- CRDs: provider-specific datastructure, and will be referenced by corresponding cluster-api CRDs, e.g.
  - for infrastructure provider aws, the CRDs are awscluster, awsmachine, awsmachinetemplate
  - for bootstrap provider kubeadm, the CRDs are kubeadmconfigs, kubeadmconfigtemplates, kubeadmcontrolplanes

<details><summary>Run a minimal cluster-api</summary><p>

```
$ clusterctl init
Fetching providers
Installing cert-manager
Waiting for cert-manager to be available...
Installing Provider="cluster-api" Version="v0.3.7-alpha.0" TargetNamespace="capi-system"
Installing Provider="bootstrap-kubeadm" Version="v0.3.7-alpha.0" TargetNamespace="capi-kubeadm-boots
trap-system"
Installing Provider="control-plane-kubeadm" Version="v0.3.7-alpha.0" TargetNamespace="capi-kubeadm-c
ontrol-plane-system"

Your management cluster has been initialized successfully!

You can now create your first workload cluster by running the following:

  clusterctl config cluster [name] --kubernetes-version [version] | kubectl apply -f -


$ kubectl get pods --all-namespaces
NAMESPACE                           NAME                                                             READY   STATUS    RESTARTS   AGE
capi-kubeadm-bootstrap-system       capi-kubeadm-bootstrap-controller-manager-d5fddb749-hsqfk        2/2     Running   0          89m
capi-kubeadm-control-plane-system   capi-kubeadm-control-plane-controller-manager-56c9f665d9-549bq   2/2     Running   0          89m
capi-system                         capi-controller-manager-7b8d44f7fb-26h8v                         2/2     Running   0          89m
capi-webhook-system                 capi-controller-manager-858464588c-p24xl                         2/2     Running   0          89m
capi-webhook-system                 capi-kubeadm-bootstrap-controller-manager-6f597c49c4-wt7pc       2/2     Running   0          89m
capi-webhook-system                 capi-kubeadm-control-plane-controller-manager-549dc9f898-ngd8h   2/2     Running   1          89m
cert-manager                        cert-manager-544d659678-kkb8k                                    1/1     Running   0          90m
cert-manager                        cert-manager-cainjector-64c9f978d7-84mvw                         1/1     Running   0          90m
cert-manager                        cert-manager-webhook-5855bb8c8c-z796r                            1/1     Running   0          90m
kube-system                         coredns-66bff467f8-75sjx                                         1/1     Running   0          102m
kube-system                         coredns-66bff467f8-pnz8t                                         1/1     Running   0          102m
kube-system                         etcd-kind-control-plane                                          1/1     Running   0          102m
kube-system                         kindnet-qdbh8                                                    1/1     Running   0          102m
kube-system                         kube-apiserver-kind-control-plane                                1/1     Running   0          102m
kube-system                         kube-controller-manager-kind-control-plane                       1/1     Running   0          102m
kube-system                         kube-proxy-4ckzr                                                 1/1     Running   0          102m
kube-system                         kube-scheduler-kind-control-plane                                1/1     Running   0          102m
local-path-storage                  local-path-provisioner-bd4bb6b75-khzng                           1/1     Running   0          102m
```

</p></details></br>

*References*

- [cluster api KEP link](https://github.com/kubernetes/enhancements/blob/f9e23231f8484922d62b7b06e72053bb49e551f0/keps/sig-cluster-lifecycle/clusterapi/0003-cluster-api.md)
- https://github.com/kubernetes-sigs/cluster-api
- https://cluster-api.sigs.k8s.io/introduction.html

## 20180707 - componentconfig api types to staging

- *Date: 04/04/2020, v1.18, alpha*

Historically, all component configurations are in the core Kubernetes repository. The KEP proposes
to migrate them to individual repositories, similar to [Kubernetes API group](https://github.com/kubernetes/api),
to make it easy for thirdparty consumption. Eventually, the `componentconfig` API group will be removed.

To the end, multiple repositories are created or changed:
- https://github.com/kubernetes/kube-scheduler
- https://github.com/kubernetes/kube-controller-manager
- https://github.com/kubernetes/kubelet
- https://github.com/kubernetes/kube-proxy
- https://github.com/kubernetes/apiserver
- https://github.com/kubernetes/apimachinery

All components follow the same convention, notably:
- API group name: `{component}.config.k8s.io`
- Kind name: `{Component}Configuration`
- External types: `k8s.io/{component}/config/{version}/types.go`
- Internal types: `k8s.io/kubernetes/pkg/{component}/apis/config` (will move to component repository later)
- Other Kubernetes API conventions also apply here, e.g. conversion, schema, etc

Note here,
- There is no `kube-apiserver` repository, but eventually, there is plan to add APIServerConfiguration.
- There is no `cloud-controller-manager` repository, and there no plan to publish its API neither.

The KEP is about moving componentcofig api types to staging, but in general, Kubernetes is working on
a simplifed component configuration for many releases. Following is a great summary from [Versioned
Component Configuration Files](https://docs.google.com/document/d/1FdaEJUEh091qf5B98HM6_8MS764iXrxxigNIdwHYW9c/edit#).

TL;DR, This is the ideal command-line API for every core cluster component:
```
$ component --config=path
```

The component exposes only one flag on its command line. This flag provides the file path to a config
file with a versioned format. All other relevant configuration information is referenced via this file.
One, stable flag where everything else is versioned config is the ideal API recommended by componentconfig.
If you are creating a new component from scratch, begin and end with this API. For several reasons
discussed in the next section, the migration from flags to versioned config is a serious journey for
most existing components, and these may want or even need a couple more flags at the end of the day.

In general, every core cluster component should:
- Maintain a distinct Kubernetes API group called {component}.config.k8s.io, which contains versioned
  sets of config objects - primarily a {Component}Configuration struct in each version. This struct,
  serialized to disk by the API machinery, is the file format for configuration.
- Ensure {component}.config.k8s.io adheres to the standard Kubernetes API deprecation policy, API conventions, and API changes policy.
- Expose a flag named `--config`, which accepts a path to a file that contains a serialized {Component}Configuration struct.
- Use the Kubernetes API machinery to deserialize the config file data, apply defaults, and convert to an internal version for runtime use.
- Validate the internal version prior to using it. If validation fails, refuse to run with the specified configuration.
- Ensure third-party libraries aren't leaking flags.

*References*

- [componentconfig api types to staging KEP link](https://github.com/kubernetes/enhancements/blob/d7306177022e9af921e5f6196b0dd592d01e5c28/keps/sig-cluster-lifecycle/wgs/0014-20180707-componentconfig-api-types-to-staging.md)

# Feature & Design

## (large) federation v2

- *Date: 07/23/2018, v1.11, design*
- *Date: 04/04/2020, v1.18, alpha. The project kubefed has its own release schedule*

Architecture-wise, federation v2 only has a controller manager. The apiserver in v1 is removed and
replaced with quite a few CRDs. The following abstractions support the propagation of a logical
federated type:
- Template: defines the representation of the resource common across clusters
- Placement: defines which clusters the resource is intended to appear in
- Override: optionally defines per-cluster field-level variation to apply to the template

Here is a concrete example of the three concepts. Creating the following resources in a federation
cluster will create 5 nginx replicas in cluster1 (default from  template) and 10 nginx replicas in
cluster2 (overwritten).

```yaml
apiVersion: core.federation.k8s.io/v1alpha1
kind: FederatedReplicaSet
metadata:
  namespace: default
  name: frontend
spec:
  template:
    apiVersion: apps/v1
    kind: ReplicaSet
    metadata:
      name: nginx-deployment
      labels:
        app: nginx
    spec:
      replicas: 5
      selector:
        matchLabels:
          app: nginx
      template:
        metadata:
          labels:
            app: nginx
        spec:
          containers:
          - name: nginx
            image: nginx:1.7.9
            ports:
            - containerPort: 80
---
apiVersion: core.federation.k8s.io/v1alpha1
kind: FederatedReplicaSetPlacement
metadata:
  namespace: default
  name: frontend
spec:
  clusterNames:
  - cluster1
  - cluster2
---
apiVersion: core.federation.k8s.io/v1alpha1
kind: FederatedReplicaSetOverride
metadata:
  namespace: default
  name: frontend
spec:
  overrides:
  - clusterName: cluster2
    replicas: 10
```

These 3 abstractions provide a concise representation of a resource intended to appear in multiple
clusters. Since the details encoded by the abstractions are the minimum required for propagation,
they are well-suited to serve as the glue between any given propagation mechanism (federation control
plane pushes resource to individual clusters or clusters pull resources from federation control plane)
and higher-order behaviors like policy-based placement and dynamic scheduling.

*References*

- [federation v2 design doc](https://docs.google.com/document/d/1ihWETo-zE8U_QNuzw5ECxOWX0Df_2BVfO3lC4OesKRQ/edit#)
- https://kubernetes.io/blog/2018/12/12/kubernetes-federation-evolution/
- https://github.com/kubernetes-sigs/kubefed

## (small) federation cluster selector

- *Date: 08/07/2018, v1.11, beta*

One problem with federation v1 is that we have to manually specify pods placement using cluster name
in `federation.kubernetes.io/replica-set-preferences` annotation.

This is not ideal in the event of updating cluster; for example, when adding a new cluster, we have
to update our yaml manifests. Instead, the doc proposes a cluster selector where user can select
clusters using labels, instead of hardcode cluster names, etc:

```yaml
apiVersion: v1
data:
  myconfigkey: myconfigdata
kind: ConfigMap
metadata:
  annotations:
    federation.alpha.kubernetes.io/cluster-selector: '[{"key": "location", "operator":
      "in", "values": ["europe"]}, {"key": "environment", "operator": "==", "values":
      ["prod"]}]'
  creationTimestamp: 2017-02-07T19:43:40Z
  name: myconfig
```

*References*

- [federation cluster selector design doc](https://github.com/kubernetes/community/blob/b33dca0b5bffcc9513cb5f4cb00a05b1812c4b94/contributors/design-proposals/multicluster/federation-clusterselector.md)

## (deprecated) federation v1

- *Date: 07/23/2018, v1.11, deprecated*

**Architecture**

A control plane is running on one of the clusters (called `host cluster`). There are two components
in the control plane: federated apiserver, and federated controller manager. The federated apiserver
requires a separate etcd to save cross cluster manifests.

The core of federation v1 is to provide native kubernetes APIs. For example, we can run a deployment
of 5 replicas against federated api server; the deployment uese exactly same deployment yaml found
in normal cluster. Federation control plane will spread the deployment replica by creating new
deployment in individual clusters. The APIs are installed in federation apiserver:

```go
installFederationAPIs(m, genericConfig.RESTOptionsGetter, apiResourceConfigSource)
installCoreAPIs(s, m, genericConfig.RESTOptionsGetter, apiResourceConfigSource)
installExtensionsAPIs(m, genericConfig.RESTOptionsGetter, apiResourceConfigSource)
installBatchAPIs(m, genericConfig.RESTOptionsGetter, apiResourceConfigSource)
installAutoscalingAPIs(m, genericConfig.RESTOptionsGetter, apiResourceConfigSource)
```

**Sync Flow**

Once resources are created in federation control plane, a sync controller will push corresponding
resources to underlying clusters. Changes in underlying clusters will NOT be resynced from control
plane. Kubernetes version 1.6 includes support for cascading deletion of federated resources. With
cascading deletion, when you delete a resource from the federation control plane, you also delete
the corresponding resources in all underlying clusters.

**federation v1 - federated Job**

Once a federated job is created, the federation control plane creates a job in all underlying
Kubernetes clusters. The jobs in the underlying clusters match the federated job except in the
number of parallelism and completions. The federation control plane ensures that the sum of the
parallelism and completions in each cluster matches the desired number of parallelism and
completions in the federated job.

**federation v1 - federated configmap**

Once a Federated ConfigMap is created, the federation control plane will create a matching
ConfigMap in all underlying Kubernetes clusters.

**federation v1 - federated service**

kube-dns needs to be configured using the following yaml config to understand which zone it is part
of. A cross-cluster DNS is required to run federated. This can be done using public cloud dns
provider, or setup on prem solutions like with coredns, which requires another etcd instance.

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: kube-dns
  namespace: kube-system
data:
  federations: federation=${DNS_ZONE_NAME}
```

To leverage federation service, pods need to use `nginx.mynamespace.myfederation` instead of just
`nginx`; the latter will resolve to `nginx.mynamespace.svc.cluster.local`  while the former will
resolve to local service if one exists, or resolve to public ingress.

*References*

- https://kubernetes.io/docs/tasks/federation/federation-service-discovery/

**federation v1 - federated ingress**

An old design doc can be found [here](https://github.com/kubernetes/community/blob/f79277a0475ac494206c7aa201bed1b668997106/contributors/design-proposals/multicluster/federated-ingress.md)
for federation v1 ingress. The core idea is that we leverage cloud capability to implement cross
cluster ingress and load balancing.
- For GCE, the preferred way is to use corss-region anycast VIP which will intelligently route
  traffic to different clusters. There are a lot of concetps in GCE global loadbalancer; in federated
  ingress, they will be automated via federated ingress controller or kubemci command. For more
  information about GCE global loadbalancer, see [here](https://cloud.google.com/load-balancing/docs/https/cross-region-example).
- For AWS, the idea is to use Geo-aware DNS (Route53) to direct traffic to closest regional elastic
  load balancer (ELB only works within a single region).

The kubemci tool is the same as federated ingress (think of kubemci as the client side implementation
of federated controller manager). In short, the workflow is:
- Create multiple clusters
- Create Deployment
- Create Service. Service should use NodePort and all clusters must expose the same port
- Reserve static public IP
- Use kubemci to create a federated ingress resource

```
$ kubemci create zone-printer \
    --ingress=ingress/ingress.yaml \
    --kubeconfig=clusters.yaml
Created Ingress in cluster: gke_generated-motif-735_us-east4-a_cluster-1
Created Ingress in cluster: gke_generated-motif-735_europe-west1-c_cluster-2
Ensuring health checks
Pod zoneprinter-5f6fc6d85-tl48l matching service selectors app=zoneprinter (targetport ): lacks a matching HTTP probe for use in health checks.
Pod zoneprinter-5f6fc6d85-6trqs matching service selectors app=zoneprinter (targetport ): lacks a matching HTTP probe for use in health checks.
Path for healthcheck is /
Ensuring health check for port: {SvcName:default/zoneprinter SvcPort:{Type:0 IntVal:80 StrVal:} NodePort:30061 Protocol:HTTP SvcTargetPort: NEGEnabled:false}
Creating health check mci1-hc-30061--zone-printer
Health check mci1-hc-30061--zone-printer created successfully
Determining instance groups for cluster gke_generated-motif-735_europe-west1-c_cluster-2
Waiting for ingress ( default : zoneprinter ) to get ingress.gcp.kubernetes.io/instance-groups annotation.....
Determining instance groups for cluster gke_generated-motif-735_us-east4-a_cluster-1
Fetching instance group: europe-west1-c k8s-ig--1977094e3db4cb2b
Fetched instance group: europe-west1-c/k8s-ig--1977094e3db4cb2b, got named ports: port: &{Name:port30061 Port:30061 ForceSendFields:[] NullFields:[]} port: &{Name:port32408 Port:32408 ForceSendFields:[] NullFields:[]}
Ensuring backend services
Ensuring backend service for port: {default/zoneprinter {0 80 } 30061 HTTP  false}
Creating backend service mci1-be-30061--zone-printer
Backend service mci1-be-30061--zone-printer created successfully
Ensuring url map
Creating url map mci1-um--zone-printer
URL Map mci1-um--zone-printer created successfully
Ensuring http target proxy.
Ensuring target http proxy. UrlMap: https://www.googleapis.com/compute/v1/projects/generated-motif-735/global/urlMaps/mci1-um--zone-printer
Creating target HTTP proxy mci1-tp--zone-printer
Creating target http proxy mci1-tp--zone-printer
Target http proxy mci1-tp--zone-printer created successfully
Ensuring http forwarding rule
Creating forwarding rule mci1-fw--zone-printer
Forwarding rule mci1-fw--zone-printer created successfully
```

*References*

- https://github.com/GoogleCloudPlatform/k8s-multicluster-ingress
- [cluster-federation-and-global-load-balancing-on-kubernetes-1](https://medium.com/google-cloud/planet-scale-microservices-with-cluster-federation-and-global-load-balancing-on-kubernetes-and-cd182f981653)
- [cluster-federation-and-global-load-balancing-on-kubernetes-2](https://medium.com/google-cloud/planet-scale-microservices-with-cluster-federation-and-global-load-balancing-on-kubernetes-and-a8e7ef5efa5e)

**federation v1 - federated HPA**

Once a federated HPA is created, the federation control plane partitions and creates the HPA in all
underlying Kubernetes clusters. The HPA in the underlying clusters will match the federation HPA
except in the number of min and max replicas. The federation control plane ensures that the sum of
max replicas in each cluster matches the specified max replicas on the federated HPA object, and
the sum of minimum replicas will be greater than or equal to the minimum specified on the federated
HPA object.

**federation v1 - limitations**

- 100% compatible and mirrors Kubernetes APIs makes federation v1 hard to scale and extend. For
  example, how do we support rolling update in different clusters considering there's no such config
  knob in deployment API (now we have to use annotations); how do we support arbitrary APIs with
  custom CRDs.
- There are security issues with current design - having access to federation control plane means
  having access to all clusters, for example, we can delete a deloyment from federation control
  plane, and deployments in all clusters will be deleted.
- The architecture makes federation control plane a single point of failure, and the extra storage
  requirement (etcd) adds up operation overhead.
- Since cluster names are required (e.g. in `federation.kubernetes.io/replica-set-preferences`), in
  situations where clusters are added/removed from Federation it would require the object definitions
  to change in order to maintain the same configuration.

**federation v1 - service**

Federation service in v1 is similar to ingress, leveraging similar constructs to provide cross
cluster service discovery and resiliency. One core difference is that in federated service, each
cluster has a sophisticated dns resolution, see above proposal.

*References*

- [federated service design doc](  https://github.com/kubernetes/community/blob/b33dca0b5bffcc9513cb5f4cb00a05b1812c4b94/contributors/design-proposals/multicluster/federated-services.md)

**federation v1 - references**

- [federation design doc](https://github.com/kubernetes/community/blob/1171a23ab2e4f8950cb1b88a007e2aae8c7bb194/contributors/design-proposals/multicluster/federation.md)
- https://github.com/kubernetes/federation
- https://github.com/kelseyhightower/kubernetes-cluster-federation
- https://medium.com/@shakamunyi/kubernetes-federation-achieving-higher-availability-for-your-applications-1d527e5e4b3

## (deprecated) cluster registry

- *Date: 07/23/2018, v1.11, alpha*

The cluster registry is just an API definition, intended to be used for other projects with different
kind of use cases. It is helpful to think of it as a registry for `kubeconfig` file. A couple
important notes from the design doc:
- Cluster API object has `spec` and `status`, though `status` is not yet defined.
- There is no built-in auth construct in cluster registry (e.g. something like `cluster.spec.auth.token`).
  The project uses pointers for this purpose, e.g. pointers to secret. This is to make the API easier
  to reason about - we don't want to make cluster registry a credential store.
- There is no controller or operator; it is up to the registry consumer to implement any control logic.

*References*

- [cluster registry design doc](https://github.com/kubernetes/community/blob/1171a23ab2e4f8950cb1b88a007e2aae8c7bb194/contributors/design-proposals/multicluster/cluster-registry/api-design.md)
- https://github.com/kubernetes/cluster-registry
