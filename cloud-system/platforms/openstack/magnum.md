<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
- [Magnum vs Murano](#magnum-vs-murano)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Magnum is an OpenStack project which offers container orchestration engines for deploying and managing
containers as first class resources in OpenStack. Two binaries work together to compose the magnum
system. The first binary (accessed by the python-magnumclient code) is the magnum-api REST server.
The REST server may run as one process or multiple processes. When a REST request is sent to the
client API, the request is sent via AMQP to the magnum-conductor process. The magnum-conductor process
runs on a controller machine and connects to a Kubernetes or Docker REST API endpoint. The Kubernetes
and Docker REST API endpoints are managed by the bay object. When service or pod objects are created,
Kubernetes may be directly contacted via the Kubernetes REST API. When container objects are acted
upon, the Docker REST API may be directly contacted.

# Architecture

There are several different types of objects in the magnum system:
- Bay: A collection of node objects where work is scheduled
- BayModel: An object stores template information about the bay which is usedn to create new bays consistently
- Pod: A collection of containers running on one physical or virtual machine
- Service: An abstraction which defines a logical set of pods and a policy by which to access them
- Container: A Docker container

The features include:
- Abstractions for Clusters
- Integration with Kubernetes, Swarm, Mesos for backend container technology
- Integration with Keystone for multi-tenant security
- Integration with Neutron for Kubernetes multi-tenancy network security
- Integration with Cinder to provide volume service for containers

# Magnum vs Murano

When considering Murano for a container-based application, we need to make a distinction: Murano
itself isn’t a container environment. Instead, it’s an application catalog that happens to have a
Kubernetes application for deploying containers.

# References

- http://docs.openstack.org/developer/magnum/
- https://www.mirantis.com/blog/magnum-vs-murano-openstack-container-strategy/
