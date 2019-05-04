<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [nginx configuration](#nginx-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 03/07/2017, v0.9

[Ingress controller](https://github.com/kubernetes/ingress) is a standalone repository in kubernetes
(previously under contrib). The `core/` directory contains general ingress code, e.g.
- generic ingress controller framework
- general configuration for ingress configuration
 - proxy settings

When starting an ingress controller, it is the generic ingress controller that gets started; this
generic ingress controller in turn calls specific backend (e.g. nginx, haproxy, gce) to handle config
update, reload, etc. There is an interface `Controller` that defines several methods like Reload,
OnUpdate, etc, to be implemented by an ingress backend.

*Updates on 04/07/2018, v0.12*

Repository moved from [ingress](https://github.com/kubernetes/ingress) to [ingress-nginx](https://github.com/kubernetes/ingress-nginx)

# nginx configuration

We can create a configmap to customize nginx, and when starting nginx controller, tell it where to
look for the [configs](https://github.com/kubernetes/ingress/blob/2ddf6c91dfe6b899dcfa28fb39469de2170779bf/controllers/nginx/configuration.md), e.g.

```yaml
containers:
- image: gcr.io/google_containers/nginx-ingress-controller:0.9.0-beta.3
  name: nginx-ingress-controller
  args:
  - /nginx-ingress-controller
  - --default-backend-service=$(POD_NAMESPACE)/default-http-backend
  - --configmap=$(POD_NAMESPACE)/nginx-custom-configuration
```

The above config is a global config, to override any specific config, use annotation for an individual
ingress rule, e.g.

```yaml
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: nginx-test
  annotations:
    kubernetes.io/ingress.class: "nginx"
    ingress.kubernetes.io/affinity: "cookie"
    ingress.kubernetes.io/session-cookie-name: "route"
    ingress.kubernetes.io/session-cookie-hash: "sha1"
spec:
  rules:
  - host: stickyingress.example.com
    http:
      paths:
      - backend:
          serviceName: nginx-service
          servicePort: 80
        path: /
```
