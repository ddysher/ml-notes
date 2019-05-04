<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Feature & Design](#feature--design)
  - [operatorkit](#operatorkit)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> A collection of proposals, designs, features in Kubernetes APIs.

- [SIG-Apps Community](https://github.com/kubernetes/community/tree/master/sig-apps)
- [SIG-Apps Proposals](https://github.com/kubernetes/community/tree/master/contributors/design-proposals/apps)

# Feature & Design

## operatorkit

*Date (07/28/2017, k8s 1.7)*

Operator aims to unify the effort for implementing operators. Scopes of the project includes:
- setup, configuration, and validation of a CLI framework
- common logging handlers
- setup of common clients such as for CRD APIs, kube-apiserver API, leader election and analytics
- code for easy leadership election management
- easy management of k8s resources, such as reconciliation loops for CRDs and utility function to set up common cluster resources possibly at a later stage
- boilerplate code for registering, validating and configuring CRD specs
- resource monitoring, providing utilities to handle channels, decoding, caching and error handling
- enforce and supply best practices for disaster recovery, e.g. if the operator is on a rebooting node
- allow easy exposure of APIs if the operator wants to export data

*References*

- https://docs.google.com/document/d/1NJhFcNezJyLM952eaYVcdfIQFQYWsAx4oTaA82-Frdk/edit
