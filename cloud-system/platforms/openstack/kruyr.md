<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Kuryr is a Docker network plugin that uses Neutron to provide networking services to Docker containers.
It provides containerised images for the common Neutron plugins.

Background: it is a common problem in docker based solutions running on openstack that you run overlay
(like flannel) on top of openstack overlay (e.g. ovs). Kuryr tries to solve the problem.

# References

- https://github.com/openstack/kuryr
