<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 08/14/2016, v0.6.0*

runv is an implementation of oci runtime with vm hypervisor as its runtime. When starting a container
using:

```
runv --kernel /path/to/kernel --initrd /path/to/initrd.img run mycontainer
```

runv first validates config.json, then starts a 'runv-namespaced' daemon that listens on "namespace.sock".
runv then interacts with the daemon using grpc. 'runv-namespaced' is responsible to launch container,
e.g. for xen, it uses libxl.
