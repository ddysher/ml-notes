<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [KEPs](#keps)
  - [bounding self labeling kubelets](#bounding-self-labeling-kubelets)
- [Feature & Design](#feature--design)
  - [node authorizer](#node-authorizer)
  - [limit node object self control](#limit-node-object-self-control)
  - [what is service account](#what-is-service-account)
  - [security context and pod security context](#security-context-and-pod-security-context)
  - [pod security policy](#pod-security-policy)
  - [encryption for secrets](#encryption-for-secrets)
  - [tls certificates in kubernetes](#tls-certificates-in-kubernetes)
  - [kubelet tls bootstrapping](#kubelet-tls-bootstrapping)
  - [aggregated cluster role](#aggregated-cluster-role)
  - [image provenance](#image-provenance)
- [Workflow](#workflow)
  - [how authn/z works](#how-authnz-works)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes APIs.

- [SIG-Auth KEPs](https://github.com/kubernetes/enhancements/blob/master/keps/sig-auth)
- [SIG-Auth Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/auth)
- [SIG-Auth Community](https://github.com/kubernetes/community/tree/master/sig-auth)

# KEPs

## bounding self labeling kubelets

The KEP aims at removing the capability of Kubelet to add arbitrary labels to its Node object. Today,
many features rely on node label, thus a compromising Kubelet with such capability has a large attack
surface.

The KEP proposes to modify the `NodeRestriction` admission plugin to prevent Kubelets from self-setting
labels within the `k8s.io` and `kubernetes.io` namespaces except for these specifically allowed
labels/prefixes:
```
kubernetes.io/hostname
kubernetes.io/instance-type
kubernetes.io/os
kubernetes.io/arch

beta.kubernetes.io/instance-type
beta.kubernetes.io/os
beta.kubernetes.io/arch

failure-domain.beta.kubernetes.io/zone
failure-domain.beta.kubernetes.io/region

failure-domain.kubernetes.io/zone
failure-domain.kubernetes.io/region

[*.]kubelet.kubernetes.io/*
[*.]node.kubernetes.io/*
```

In addition, a new `node-restriction.kubernetes.io/*` label prefix is reserved for cluster administrators
to label their Node objects centrally for isolation purposes. That is, `NodeRestriction` admission
will prevent Kubelets from adding/removing/modifying labels with the prefix.

Apart from the above mentioned labels, users can use arbitrary labels as before, e.g. labels outside
of `k8s.io` and `kbuernetes.io` prefix.

*References*

- [bounding-self-labeling-kubelets KEP link](https://github.com/kubernetes/enhancements/blob/6861b7279948db44b58b8056450bc45102ea60bb/keps/sig-auth/0000-20170814-bounding-self-labeling-kubelets.md)

# Feature & Design

## node authorizer

*Date: 03/10/2018, v1.9, stable*

As of 1.6, kubelets have read/write access to all Node and Pod objects, and read access to all Secret,
ConfigMap, PersistentVolumeClaim, and PersistentVolume objects. This means that compromising a node
gives access to credentials that allow modifying other nodes, pods belonging to other nodes, and
accessing confidential data unrelated to the node's pods. Therefore, a proposal is in place to solve
the problem. The proposal proposes to add:
- Node authorizer: A new authorizer is added to authorize requests from identifiable nodes using a
  fixed policy identical to the default RBAC "system:node" cluster role. Note that the node authorizer
  is a new authorizer, in parallel with RBAC: it's not a subset of RBAC. The reason for not using
  RBAC is that a Kubernetes cluster is quite dynamic, using RBAC policy requires frequently rule
  updates; on the other hand, not all clusters enable RBAC by default, even though it's recommended
  best practices.
- Node admission: A new admission plugin is added to limit node to only be able to mutate their own
  Node API object, to create/mutate mirror pods bound to themselves, etc. Admission is needed because
  node authorizer does not have access to request bodies (or the existing object, for update requests),
  so it could not restrict access based on fields in the incoming or existing object. On the other
  hand, admission alone is not enough because admission is only called for mutating requests, so it
  could not restrict read access.

In order to be authorized by the Node authorizer, kubelets must use a credential that identifies
them as being in the `system:nodes` group, with a username of `system:node:<nodeName>`. This group
and user name format match the identity created for each kubelet as part of kubelet TLS bootstrapping.
- To enable the Node authorizer, start the apiserver with `--authorization-mode=Node,...`
- To limit the API objects kubelets are able to write, enable the NodeRestriction admission plugin
  by starting the apiserver with `--admission-control=...,NodeRestriction,...`

*References*

- [kubelet-authorizer design doc](https://github.com/kubernetes/community/blob/a616ab2966ce4caaf5e9ff3f71117e5be5d9d5b4/contributors/design-proposals/node/kubelet-authorizer.md)

## limit node object self control

- *Date: 03/10/2018, v1.9, proposal*
- *Date: 06/23/2019, v1.15, moved to KEP*

The proposal is related to node authorizer. Node authorizer allows a node to have total authority
over its own Node object; however, we want to limit its access of its own object to some degree.

The proposal is moved to KEP:bounding self labeling kubelets.

*References*

- https://github.com/kubernetes/community/pull/911

## what is service account

*Date: 05/02/2016, v1.1, stable*

When you (a human) access the cluster (e.g. using kubectl), you are authenticated by the apiserver
as a particular User Account (currently this is usually admin, unless your cluster administrator
has customized your cluster). Processes in containers inside pods can also contact the apiserver.
When they do, they are authenticated as a particular Service Account (e.g. default). Service account
only does authentication, upon creation, a username is created which can be used for ABAC
authorization plugin. Using the plugin, admin can restrict cluster access per service account.

## security context and pod security context

*Date: 05/10/2017, v1.7, stable*

A security context defines the operating system security settings (uid, gid, capabilities, SELinux
role, etc..) applied to a container. There are two levels of security context: pod level security
context, and container level security context. Usually, users provide either `Pod.Spec.Containers[i].SecurityContext`
or `Pod.Spec.SecurityContext`, then kubelet will be responsible to setup pods and containers; e.g.
for SELinux option, kubelet will pass the option to container runtime to relabel container processes.
There is also a `SecurityContextProvider` defined which help kubelet modify security settings.

*References*

- [security context design doc](https://github.com/kubernetes/community/blob/a616ab2966ce4caaf5e9ff3f71117e5be5d9d5b4/contributors/design-proposals/auth/security_context.md)
- [pod security context design doc](https://github.com/kubernetes/community/blob/a616ab2966ce4caaf5e9ff3f71117e5be5d9d5b4/contributors/design-proposals/auth/pod-security-context.md)
- [selinux design doc](https://github.com/kubernetes/community/blob/930ce65595a3f7ce1c49acfac711fee3a25f5670/contributors/design-proposals/node/selinux.md)
- [volume design doc](https://github.com/kubernetes/community/blob/a616ab2966ce4caaf5e9ff3f71117e5be5d9d5b4/contributors/design-proposals/storage/volumes.md)

## pod security policy

*Date: 03/10/2018, v1.10, beta*

A Pod Security Policy is a cluster-level resource that controls security sensitive aspects of the
pod specification (e.g. HostIPC, SecurityContext, etc). The PodSecurityPolicy objects define a set
of conditions that a pod must run with in order to be accepted into the system, as well as defaults
for the related fields. As of kuberentes 1.10 planning, Pod Security Policy moves to its own API
group (policy group) and is in beta phase. PSP is implemented as an in-tree admission plugin.

PodSecurityPolicy, once created, act as `deny all`, just like NetworkPolicy. That is, creating Pod
will be rejected unless either the User (User Role) or Pod (ServiceAccount Role) has access to at
least one PodSecurityPolicy. The preferred method for authorizing policies is to grant access to the
Pod's service account.

- [pod security policy design doc](https://github.com/kubernetes/community/blob/a616ab2966ce4caaf5e9ff3f71117e5be5d9d5b4/contributors/design-proposals/auth/pod-security-policy.md)
- [pod security policy example](https://github.com/kubernetes/examples/tree/dfc12dd772da8010ea543a7444c5d9bfa51eb9cf/staging/podsecuritypolicy/rbac)

## encryption for secrets

*Date: 07/28/2017, v1.7*

This feature allows sensitive data such as passwords, API keys, or other resources stored in the etcd
key-value store to be encrypted. A config file must be passed to apiserver; the config file contains
what resources are to be encrypted, and for each resource, what encryption algorithm to use.

```yaml
kind: EncryptionConfig
apiVersion: v1
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: c2VjcmV0IGlzIHNlY3VyZQ==
        - name: key2
          secret: dGhpcyBpcyBwYXNzd29yZA==
    - identity: {}
    - secretbox:
        keys:
        - name: key1
          secret: YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=
    - aesgcm:
        keys:
        - name: key1
          secret: c2VjcmV0IGlzIHNlY3VyZQ==
        - name: key2
          secret: dGhpcyBpcyBwYXNzd29yZA==
```

Note this is a config file passed to apiserver, not an API object like Pod. Handling of this
option can be found at https://github.com/kubernetes/apiserver/tree/release-1.7/pkg/server/options/encryptionconfig

## tls certificates in kubernetes

*Date: 03/10/2018, v1.9*

Every Kubernetes cluster has a cluster root Certificate Authority (CA). The CA is generally used by
cluster components to validate the API server's certificate, by the API server to validate kubelet
client certificates, etc. To support this, the CA certificate bundle is distributed to every node in
the cluster and is distributed as a secret attached to default service accounts.

TLS certificate is a new API in kubernetes, where user workloads can also use this CA to establish
trust in kubernetes cluster. Your application can request a certificate signing using the `certificates.k8s.io`
API using a protocol that is similar to the ACME draft. Using the API involves following steps:
- Create key and CSR: create a private key and csr (server.key, server.csr)
- Send the CSR to kubernetes via `certificates.k8s.io/v1beta1.CertificateSigningRequest`
- Cluster admin review the CSR and approve it (a certificate controller is listening the request)
- User can know download the certificate from CertificateSigningRequest.Status

Note since controller manager is responsible to facilitate signing the certificate, it requires
certificate authority's keypair (passed via flag). Also note that this API is introduced for
requesting certificates from a cluster-level Certificate Authority (CA), i.e. it's not a generic
certificate signing service.

The main use case for certificates API is kubelet tls bootstrapping, see below.

*References*

- https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/
- https://github.com/kubernetes/website/blob/snapshot-initial-v1.9/docs/tasks/tls/managing-tls-in-a-cluster.md

## kubelet tls bootstrapping

*Date: 03/10/2018, v1.9, beta*

In kubernetes, node communication with master is secured; this requires kubelet to have tls certificates
configured properly. However, this turns out to be quite painful for cluster admins, and the same
process must be repeated not just during cluster provisioning, but also adding new node to existing
cluster. The kubelet tls bootstrapping feature simplifies the process using a few constructs:
- apiserver certificate API: Kubernetes api server provides a cert API to CRUD, approve and deny csr.
- bootstrap token: A static token provided to API server (via token file), to allow kubelet to connect.
  An unauthenticated kubelet will connect to API server using this bootstrap token, which has a very
  minimal set of access scope. Kubelet uses the this bootstrap token (in another sense, bootstrap
  user) to send CSR.
- controller: kube-controller-manager is responsible for signing all CSRs and thus plays a critical
  role in the process.
- RBAC: this is to limit access scope of bootstrap user; there will be a cluster role `node-bootstrapper`.

TLS bootstrapping is mainly used for Kubelet to retrieve *client* certificate, it's also possible to
use the process to retrive *serving* certificate.

For detailed usage, see:
- https://kubernetes.io/docs/admin/kubelet-tls-bootstrapping/
- https://medium.com/@toddrosner/kubernetes-tls-bootstrapping-cf203776abc7

*References*

- https://github.com/kubernetes/features/issues/43
- [kubelet-tls-bootstrap design doc](https://github.com/kubernetes/community/blob/930ce65595a3f7ce1c49acfac711fee3a25f5670/contributors/design-proposals/cluster-lifecycle/kubelet-tls-bootstrap.md)

## aggregated cluster role

*Date: 03/16/2018, v1.9*

As of 1.9, it's possible to aggregate multiple cluster roles into one role, reference [here](https://kubernetes.io/docs/admin/authorization/rbac/#aggregated-clusterroles).

For example, following is a simple aggregated `ClusterRole`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring
aggregationRule:
  clusterRoleSelectors:
  - matchLabels:
      rbac.example.com/aggregate-to-monitoring: "true"
rules: [] # Rules are automatically filled in by the controller manager.
```

## image provenance

Image policy aims to provide a more sophasticated way to check container images used in Pods.

A new Admission Controller `ImagePolicyWebhook` is added to Kubernetes, which examines all pod
objects that are created or updated. It can either admit the pod, or reject it. The admission
controller code does not contain logic to make an admit/reject decision. Instead, it extracts
relevant fields from the Pod creation/update request and sends those fields to a Backend, i.e.
Webhook. Note the policy, like many others, works on Pod level, so controllers (deployment, job,
etc) are responsible to handle Pod creation failure.

The whole system will work similarly to the **Authentication WebHook** or the **Authorization
WebHook**. Just like `TokenReview` and `SubjectAccessReview` in AuthN/Z, image policy webhook
contains a `ImageReview` API object, located at `imagepolicy.k8s.io` group.

All annotations on a Pod that match `*.image-policy.k8s.io/*` are sent to the webhook. Sending
annotations allows users who are aware of the image policy backend to send extra information to
it, and for different backends implementations to accept different information.

As with other admission webhook, its behavior can be configured via `--admission-control-config-file`
API server flag, i.e.

```
apiVersion: apiserver.k8s.io/v1alpha1
kind: AdmissionConfiguration
plugins:
- name: ImagePolicyWebhook
  path: imagepolicyconfig.yaml
...
```

The yaml can be:

```yaml
imagePolicy:
  kubeConfigFile: /path/to/kubeconfig/for/backend
  # time in s to cache approval
  allowTTL: 50
  # time in s to cache denial
  denyTTL: 50
  # time in ms to wait between retries
  retryBackoff: 500
  # determines behavior if the webhook backend fails
  defaultAllow: true
```

*References*

- [image provenance design doc](https://github.com/kubernetes/community/blob/59a27a2c4e3f58b0d88a7f37fc2c00f6ad74ed59/contributors/design-proposals/auth/image-provenance.md)

# Workflow

## how authn/z works

*Date: 07/18/2017, v1.7*

**Preclude: user in kubernetes**

API requests are tied to either a normal user or a service account, or are treated as anonymous
requests. This means every process inside or outside the cluster, from a human user typing kubectl
on a workstation, to kubelets on  nodes, to members of the control plane, must authenticate when
making requests to the API server, or be treated as an anonymous user.

Users are represented by strings. These can be plain usernames, like "alice", email-style names,
like "bob@example.com", or numeric ids represented as a string. It is up to the Kubernetes admin
to configure the authentication modules to produce usernames in the desired format. The RBAC
authorization system does not require any particular format. However, the prefix `system:` is
reserved for Kubernetes system use, and so the admin should ensure usernames do not contain this
prefix by accident. Service Accounts have usernames with the `system:serviceaccount:` prefix and
belong to groups with the `system:serviceaccounts` prefix. A service account automatically generates
a user. The user's name is generated according to the naming convention:
```
system:serviceaccount:<namespace>:<serviceaccountname>
```

**Authentication**

Authentication is the first step in kubernetes API (others being authorization, admission control
and built-in validation). Authentication finds out who is accessing kubernetes API and extract the
'user' to be used in later steps. Following is a list of current Authentication methods:
- _X509 Client Certs_. Basically, api-server is started with '--client-ca-file' flag. When requesting,
  client presents its certificate; if the certificate is validated, then the common name of the
  subject is used as the user name for the request, and organization fields are used as group
  memberships.
- _Static Token File_. The API server reads bearer tokens from a file when given the `--token-auth-file=SOMEFILE`
  option on the command line. Currently, tokens last indefinitely, and the token list cannot be
  changed without restarting API server. The token file is a csv file with a minimum of 3 columns:
  token, user name, user uid, followed by optional group names; e.g.
  ```
  31ada4fd-adec-460c-809a-9e56ceb75269,ddysher,jva8hkzjhf92yh4h,"caicloud,china"
  ```
  When using bearer token authentication from an http client, the API server expects an Authorization
  header with a value of `Bearer THETOKEN`. Example header:
  ```
  Authorization: Bearer 31ada4fd-adec-460c-809a-9e56ceb75269
  ```
- _Bootstrap Tokens_. Bootstrap tokens are stored as secrets in the Kubernetes cluster, and then
  issued to the individual kubelet for initial cluster bootstrap process. From the kubelet's
  perspective, one token is like another and has no special meaning. From the kube-apiserver's
  perspective, however, the bootstrap token is special. Due to its `Type`, `namespace` and `name`,
  kube-apiserver recognizes it as a special token, and grants anyone authenticating with that token
  special bootstrap rights, notably treating them as a member of the `system:bootstrappers` group
  which has access to certificates APIs. A bootstrap token looks like the following:
  ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     # Name MUST be of form "bootstrap-token-<token id>"
     name: bootstrap-token-07401b
     namespace: kube-system

   # Type MUST be 'bootstrap.kubernetes.io/token'
   type: bootstrap.kubernetes.io/token
   stringData:
     # Human readable description. Optional.
     description: "The default bootstrap token generated by 'kubeadm init'."

     # Token ID and secret. Required.
     token-id: 07401b
     token-secret: f395accd246ae52d

     # Expiration. Optional.
     expiration: 2017-03-10T03:22:11Z

     # Allowed usages.
     usage-bootstrap-authentication: "true"
     usage-bootstrap-signing: "true"

     # Extra groups to authenticate the token as. Must start with "system:bootstrappers:"
     auth-extra-groups: system:bootstrappers:worker,system:bootstrappers:ingress
  ```
- _Static Password File_. Basic authentication is enabled by passing the `--basic-auth-file=SOMEFILE`
  option to API server. Currently, the basic auth credentials last indefinitely, and the password
  cannot be changed without restarting API server. Static password file is very similar to static
  token file, where a minimum of 3 columns are required, e.g.
  ```
  password,user,uid,"group1,group2,group3"
  ```
  When using static password file, an Authorization header is required, e.g.
  ```
  Authorization: Basic BASE64ENCODED(USER:PASSWORD)
  ```
- _Service Account Tokens_. A service account is an automatically enabled authenticator that uses
  signed bearer tokens to verify requests. Service accounts are usually created automatically by
  the API server and associated with pods running in the cluster through the ServiceAccount Admission
  Controller. Bearer tokens are mounted into pods at well-known locations, and allow in-cluster
  processes to talk to the API server. Service account bearer tokens are perfectly valid to use
  outside the cluster and can be used to create identities for long standing jobs that wish to talk
  to the Kubernetes API.
- _OpenID Connect Tokens_. OpenID is a protocol built on top of OAuth2 to provide authentication
  service. Client first authenticate to the OpenID service (e.g. dex from CoreOS) and receives a
  token with a `id_token`, which is a JWT token containing identity. To identify the user, the
  authenticator uses the `id_token` (not the access_token) from the OAuth2 token response as a
  bearer token. kubernetes doesn't need to contact OpenID provider to verify the token; instead,
  it uses OpenID provider's certificate to verify JWT signature (think of certificate chain).
- _Webhook Token Authentication_. As its name suggests, a request sent to kubernetes is sent to an
  external authentication service. Kubernetes uses the same API versioning semantics for such
  request as well, i.e. a request of the following form is sent to the external service (spec);
  the external service is responsible to fill the status field.
  ```
  {
    "apiVersion": "authentication.k8s.io/v1beta1",
    "kind": "TokenReview",
    "spec": {
      "token": "(BEARERTOKEN)"
    }
  }
  ```
  As shown in the json fields, `TokenReview` is part of authentication API group, see `pkg/apis/authentication`.
- _Authenticating Proxy_. The API server can be configured to identify users from request header
  values, such as `X-Remote-User`. It is designed for use in combination with an authenticating
  proxy. That is, when an authenticating proxy successfully authenticates the user, it sets header
  `X-Remote-User: user`. Other headers are also possible, e.g. `X-Remote-Group`. Kubernetes provides
  flags to configure the headers. In order to prevent header spoofing, the authenticating proxy is
  required to present a valid client certificate to the API server for validation against the
  specified CA before the request headers are checked.

**Authorization**

In Kubernetes, you must be authenticated (logged in) before your request can be authorized (granted
permission to access). Authorization is based on several attributes, which are pre-defined in
kubernetes. Following is a list of current authorization methods.
- _AlwaysDeny_
- _AlwaysAllow_
- _ABAC_. For ABAC mode, apiserver is started with `--authorization-policy-file=SOME_FILENAME`. The
  policy file is typically one policy per line, e.g.
  ```json
  {"apiVersion": "abac.authorization.kubernetes.io/v1beta1", "kind": "Policy", "spec": {"user": "alice", "namespace": "*", "resource": "*", "apiGroup": "*"}}
  ```
- _RBAC_. Major concepts in RBAC are Role, RoleBinding, ClusterRole, ClusterRoleBinding. When
  enabled, a set of default cluster roles are pre-defined for cluster components. Refer to https://kubernetes.io/docs/admin/authorization/rbac/
- _Webhook_. Webhook causes Kubernetes to query an outside REST service when determining user
  privileges; similar to webhook token authentication, the external REST service is responsible to
  fill the status field. Following is an example request sent from kubernetes:
  ```json
  {
    "apiVersion": "authorization.k8s.io/v1beta1",
    "kind": "SubjectAccessReview",
    "spec": {
      "resourceAttributes": {
        "namespace": "kittensandponies",
        "verb": "get",
        "group": "unicorn.example.org",
        "resource": "pods"
      },
      "user": "jane",
      "group": [
        "group1",
        "group2"
      ]
    }
  }
  ```
  As shown in the json fields, `SubjectAccessReview` is part of authorization API group, see `pkg/apis/authorization`.
- _Node_. Node authorization is a special-purpose authorization mode that specifically authorizes
  API requests made by kubelets. To use node authorization, apiserver must start with `--authorization-mode=Node,$others`,
  and an admission controller called `NodeRestriction` is required, i.e. `--admission-control=...,NodeRestriction,...`.
  More detail: Node authorizer and admission control plugin provides a control of what resources a
  node can access. In previous versions of Kubernetes nodes had access to global resources while
  controlling only small portion of resources on the cluster. In Kubernetes 1.7 nodes are limited to
  access resources for pods that are scheduled to run on them. Every kubelet has a system service
  account, e.g. `system:node:127.0.0.1` for node `127.0.0.1`.

**Notes**

- Webook in authn/z can only be configured through commandline flag: no dynamic webhook registration
  is allowed (unlike admission control). This is by design, to avoid security issues.

*References*

- https://kubernetes.io/docs/admin/authentication
- https://kubernetes.io/docs/admin/authorization/
- https://kubernetes.io/docs/admin/authorization/rbac
