<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [API](#api)
  - [DNS annotation](#dns-annotation)
  - [Ownership management](#ownership-management)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Inspired by Kubernetes DNS, Kubernetes' cluster-internal DNS server, [ExternalDNS](https://github.com/kubernetes-incubator/external-dns)
makes Kubernetes resources discoverable via public DNS servers. Like KubeDNS, it retrieves a list of
resources (Services, Ingresses, etc.) from the Kubernetes API to determine a desired list of DNS
records. Unlike KubeDNS, however, it's not a DNS server itself, but merely configures other DNS
providers accordingly, e.g. AWS Route 53, Google CloudDNS, etc.

In a broader sense, ExternalDNS allows you to control DNS records dynamically via Kubernetes resources
in a DNS provider agnostic way.

# API

## DNS annotation

The annotation key is `external-dns.alpha.kubernetes.io/hostname`, e.g.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx
  annotations:
    external-dns.alpha.kubernetes.io/hostname: nginx.external-dns-test.gcp.zalan.do.
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: nginx
```

## Ownership management

From release v0.3, ExternalDNS can become aware of the records it is managing (enabled via `--registry=txt`).
Therefore, ExternalDNS can safely manage non-empty hosted zones, e.g. if a LoadBalancer type service
has IP `104.155.60.49` and the dns is `nginx.external-dns-test.gcp.zalan.do.`, then apart from an A
record, there will be a TXT record for this dns, i.e.

```
NAME                                   TYPE  TTL  DATA
nginx.external-dns-test.gcp.zalan.do.  A     300  104.155.60.49
nginx.external-dns-test.gcp.zalan.do.  TXT   300  "heritage=external-dns,external-dns/owner=my-identifier"
```

*References*
- [design doc](https://github.com/kubernetes-incubator/external-dns/blob/6285b2c38dd371c44a95547835a9c1b5058d3e61/docs/initial-design.md)
