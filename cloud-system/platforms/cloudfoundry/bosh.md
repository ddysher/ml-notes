<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Projects](#projects)
  - [Kubo](#kubo)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

From the official website:

> [BOSH](https://bosh.io/docs/) is a project that unifies release engineering, deployment, and
> lifecycle management of small and large-scale cloud software. BOSH can provision and deploy
> software over hundreds of VMs. It also performs monitoring, failure recovery, and software updates
> with zero-to-minimal downtime.

BOSH is originally created to deploy CloudFoundry, but then evolved to manage many other cloud
softwares. BOSH stands for `Borg (r+1=s, g+1=h)`, so it's clear that BOSH intends to be a cluster
management tool. BOSH provides following features:
- Package: an opinioned format to package applications
- Provision: create & manages cloud resources from different providers
- Deploy: deploy applications using a client/server architecture
- Monitor: built-in monitoring and third-party tool integration
- Upgrade: offers easy scaling, zero-downtime rolling update

*References*

- https://content.pivotal.io/blog/comparing-bosh-ansible-chef-part-1
- https://content.pivotal.io/blog/comparing-bosh-ansible-chef-part-2

# Projects

## Kubo

Kubo is a project to deploy Kubernetes using BOSH, i.e. Kubo treats Kubernetes as a cloud software
just like other softwares. [Here](https://github.com/cloudfoundry-incubator/kubo-release/tree/master/releases/kubo)
is the kubo release (release is a first-class concept in BOSH to represent a release of a software)
for Kubernetes.

Kubo has been renamed to [CFCR (CloudFoundry Container Runtime)](https://www.cloudfoundry.org/container-runtime/)
to better capture its scope.
> Formerly known as Project Kubo, an incubating project within the Cloud Foundry Foundation initiated
> by engineers at Google and Pivotal, the Kubernetes-powered, Kubernetes-certified CF Container
> Runtime offers a uniform way to instantiate, deploy, and manage highly available Kubernetes
> clusters on a cloud platform using CF BOSH.
