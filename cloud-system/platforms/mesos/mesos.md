<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Architecture](#architecture)
- [Frameworks](#frameworks)
- [DC/OS](#dcos)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Architecture

Mesos consists of a master daemon that manages agent daemons running on each cluster node, and Mesos
frameworks that run tasks on these agents. A framework running on top of Mesos consists of two
components: a scheduler that registers with the master to be offered resources, and an executor
process that is launched on agent nodes to run the framework's tasks.

*References*

- http://mesos.apache.org/documentation/latest/architecture/

# Frameworks

The guide describes the callback interfaces. After 1.0 release, http API is considered stable so we
can write framework in any language that can speak http.

*References*

- http://mesos.apache.org/documentation/latest/app-framework-development-guide/

# DC/OS

DC/OS derives from Mesosphere's Datacenter Operating System, a commercial product built around Apache
Mesos. At the heart of DC/OS is the Mesos distributed systems kernel, and DC/OS utilizes Mesos to
handle job scheduling, resource management and abstraction, high availability, and other infrastructure-level
processes. However, it's the technologies built on top of and around Mesos that combine with Mesos to
make DC/OS what it is. These include the native container-orchestration and application platform
(Marathon); the DC/OS installer and Universe experience; the powerful but intuitive user interfaces
for management and monitoring; and improvements around networking, security, load balancing, service
discovery and much more. Interesting projects in dcos:
- https://github.com/dcos/minuteman
- https://github.com/dcos/lashup
- https://github.com/mesosphere/mesos-dns

*References*

- https://dcos.io/docs
- https://mesosphere.com/blog/2016/04/19/open-source-dcos/

# References

- https://github.com/dcos
- http://mesos.apache.org/documentation/latest/
- http://mesos.apache.org/blog/mesos-1-0-0-released/
