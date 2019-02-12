<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Runtime spec](#runtime-spec)
  - [Overview](#overview)
  - [Details](#details)
- [Image spec](#image-spec)
  - [Overview](#overview-1)
- [Distribution spec](#distribution-spec)
- [Artifacts spec](#artifacts-spec)
- [OCI specs expriments](#oci-specs-expriments)
  - [Build and work with skopeo](#build-and-work-with-skopeo)
  - [Build and work with image-tools](#build-and-work-with-image-tools)
  - [Create container using runc](#create-container-using-runc)
  - [Other projects](#other-projects)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# [Runtime spec](https://github.com/opencontainers/runtime-spec)

*Date: 03/18/2017, v1.0.0-rc5*

## Overview

oci runtime spec is a specification that defines what a software container is and its attributes in
a cross platform way. runc is an implementation of the specification. Use cases targeted by this spec:

**Application bundle builder**

Application bundle builder is the person who wants to create containers. He or she defines bundle
information that conforms to runtime spec, then feed the information to any runtime implementation
to launch a container.

**Hook Developers**

Hook developers can extend the functionality of an OCI-compliant runtime by hooking into a container's
lifecycle with an external application. Example use cases include sophisticated network configuration,
volume garbage collection, etc.

**Runtime Developers**

Runtime developers can build runtime implementations that run OCI-compliant bundles and container
configuration, containing low-level OS and host specific details, on a particular platform.

## Details

The content of runtime spec is three fold:

**Filesystem bundle**

At its core, it defines the directory structure that application bundle builder must conform so that
runtime can extract information. It consists of:
- config.json : contains configuration data.
- A directory representing the root filesystem of the container.

**Runtime and lifecycle**

Runtime and lifecycle defines operations that can be performed on OCI-compliant container, e.g.
start, kill. In addition to operations, it also defines error handling, hooks, container state
management. Runtime is platform specific: there is a general one, with platform additions on top
of it.

**Configuration**

The configuration file contains metadata necessary to implement standard operations against the
container. Configuration is also platform specific: a general config across all platforms, with
platform additions on top of it. General configuration contains things like hostname, container
root path, container hooks, oci version, process information, etc. For linux specific configuration,
there is namespace, cgroups, mount propagation options, etc.

# [Image spec](https://github.com/opencontainers/image-spec)

*Date: 03/18/2017, v1.0.0-rc5*

## Overview

This specification defines how to create an OCI Image, which will generally be done by a build
system, and output an image manifest, a filesystem serialization, and an image configuration.

The runtime specification above outlines how to run a "filesystem bundle" that is unpacked on
disk. At a high-level an OCI implementation would download an OCI Image then unpack that image
into an OCI Runtime filesystem bundle. At this point the OCI Runtime bundle would be run by an
OCI Runtime.

The combination of the image manifest, image configuration, and one or more filesystem serializations
is called the "OCI Image". Once built, the OCI Image can then be discovered by name, downloaded,
verified by hash, trusted through a signature, and unpacked into an OCI Runtime Bundle. At a high
level:
- Image manifest contains metadata about the contents and dependencies of the image including the
  content-addressable identity of one or more filesystem serialization archives that will be unpacked
  to make up the final runnable filesystem.
- Filesystem serialization contains the actual content. It contains things like layer, diff, etc;
  similar to docker term.
- Image configuration includes information such as application arguments, environments, etc.

# [Distribution spec](https://github.com/opencontainers/distribution-spec/)

This specification defines an API protocol to facilitate distribution of images.

The goal of this specification is to standardize container image distribution based on the
specification for the Docker Registry HTTP API V2 protocol.

# [Artifacts spec](https://github.com/opencontainers/artifacts)

Apart from contaienr image, applications and services typically require additional artifacts to
deploy and manage, including helm for deployment and Open Policy Agent (OPA) for policy enforcement.
The goal of artifacts is to extend the OCI registry specification and store other cloud native
artifacts.

The artifacts specification seeks to re-uses most of the distribution spec, i.e. utilizing the
manifest and index definitions, new artifacts, such as the Singularity project, can be stored
and served using the distribution-spec.

# OCI specs expriments

*Date: 03/18/2017, v1.0.0-rc5*

There are a few tools used here:

- https://github.com/projectatomic/skopeo
- https://github.com/opencontainers/image-tools

## Build and work with skopeo

`skopeo` is a command line utility for various operations on container images and image repositories.
Recent version doesn't build properly, we have to  to older version (v0.1.17), then build it using
`make binary-local`.

    $ git checkout v0.1.17
    & sudo apt-get install go-md2man libgpgme11-dev libassuan-dev
    $ make binary-local && sudo mv skopeo /usr/local/bin
    $ skopeo inspect docker://docker.io/busybox

`skopeo inspect` command is a simple wrapper of https://github.com/containers/image.

Now we translate docker image to oci layout. Internally, skopeo also depends on 'containers/image'
project, which abstracts different image specification into a `Image` interface; the copy operation
is accomplished by copying layer by layer.

    $ cd ~
    $ skopeo copy docker://busybox:latest oci:busybox-oci

## Build and work with image-tools

The image-tools is a collection of tools for working with OCI image format sepc. In release v0.1.0,
there are multiple commands; it was then merged into a single command (working on commit 1f4874510501730a417a7137ccae21582985c793).

Now that we have the busybox oci layout (~/busybox_ocilayout), we can use image-tools to create
runtime bundle, i.e. from oci image spec to runtime bundle; this can be achieved via command:

    $ oci-image-tool create --ref latest busybox-oci busybox-bundle

Now we can use `runc` to create container based on the runtime bundle.

## Create container using runc

Now build runc (working on commit c266f1470c25d9001a133000123e89f0a59d0571):

    $ make && sudo make install

Based on image-tools documentation, we should be able to run container with:

    $ cd busybox-bundle && sudo runc run busybox

But this doesn't work for me (ubuntu 14.04 virtualbox). However, using unpack works:

    $ rm -rf busybox-bundle
    $ oci-image-tool unpack --ref latest busybox-oci rootfs
    $ mkdir busybox && mv rootfs busybox
    $ cd busybox && runc spec
    $ sudo runc run busybox

## Other projects

`umoci` is another project to modify oci image, see its README.
