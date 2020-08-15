<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Projects](#projects)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

- *Date: 05/05/2020, v0.8.1*

[ORAS (OCI Registry As Storage)](https://github.com/deislabs/oras) enables various client libraries
with a way to push artifacts to OCI Spec Compliant registries. The OCI Spec mentioned here includes:
- [image spec](https://github.com/opencontainers/image-spec)
- [distribution spec](https://github.com/opencontainers/distribution-spec/)
- [artifacts spec](https://github.com/opencontainers/artifacts)

ORAS is not a registry itself, rather, it is both a CLI for initial testing and a Go Module to be
included with other tools.

As of v0.8.1, the supported registries are (we can't use push/pull with unsupported registries):
- docker/distribution - local/offline verification
- Azure Container Registry

Using `oras` CLI is very similar to `docker pull/push`, e.g.

```
oras login -u myuser -p mypass --insecure <registry-ip>:5000

oras push <registry-ip>:5000/library/hello:latest hi.txt

oras pull <registry-ip>:5000/library/hello:latest
```

# Projects

Following is a list of projects utilizing ORAS:

- [wasm-to-oci](https://github.com/engineerd/wasm-to-oci)
- [helm v3 experimental feature](https://v3.helm.sh/docs/topics/registries/), code [here](https://github.com/helm/helm/tree/v3.2.0/internal/experimental/registry)
- [singularity](https://sylabs.io/guides/3.1/user-guide/cli/singularity_push.html), code [here](https://github.com/sylabs/singularity/tree/4dd6353b71229c5afcf00053237c79d68ab7d1e0/internal/pkg/client/oras)

In addition, there are projects with similar goals but not yet utilizing ORAS:
- [cnab-to-oci](https://github.com/cnabio/cnab-to-oci)
