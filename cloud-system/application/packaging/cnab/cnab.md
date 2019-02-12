<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Projects](#projects)
  - [duffle](#duffle)
  - [cnab-to-oci](#cnab-to-oci)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[Cloud Native Application Bundles (CNAB)](https://cnab.io/) are a package format specification that
describes a technology for bundling, installing, and managing distributed applications, that are by
design, cloud agnostic. It aims to be the equivalent of a deb (or MSI) package but for all things
Cloud Native.

The project is initiated from Docker and Microsoft.

# Projects

## duffle

[duffle (cnab implementation)](https://duffle.sh/) is an implementation of cnab specification.

## cnab-to-oci

There is an [ongoing effort](https://github.com/cnabio/cnab-to-oci) to convert cnab package into oci
distribution, as stated in the document:

> There is a clear trend towards more types of artifacts being stored in container registries. While
> it's too early to predict exactly what will be stored in registries, a couple of observations can
> be made.
