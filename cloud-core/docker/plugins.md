<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Docker plugin](#docker-plugin)
- [Docker volume plugin](#docker-volume-plugin)
- [Docker network plugin](#docker-network-plugin)
- [Docker IPAM plugin](#docker-ipam-plugin)
- [Docker auth plugin](#docker-auth-plugin)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Docker plugin

*Date: 12/19/2016*

**Overview**

Docker plugins extends docker's capabilities, e.g. volume plugin, network plugin, auth plugin, ipam plugin.

**Plugin API**

A plugin is a process running on the same or a different host as the docker daemon, which registers
itself by placing a file on the same docker host in one of the plugin discovery directories (pre-defined,
default `/run/docker/plugins`).

When a plugin is referred to, docker looks for the named directory and activates it with a handshake.
The plugin API is RPC-style JSON over HTTP, much like webhooks.

*References*

- https://docs.docker.com/engine/extend/plugins/
- https://docs.docker.com/engine/extend/plugin_api/
- https://github.com/docker/go-plugins-helpers

# Docker volume plugin

If a plugin registers itself as a VolumeDriver when activated, then it is expected to provide writeable
paths on the host filesystem for the Docker daemon to provide to containers to consume. Note the plugin
requires that we provide a host path to consume, even if we just want to intercept requests to blob
storage, say. s3. In such case, we can use fuse to do so, e.g. s3fs

*References*

- overview: https://docs.docker.com/engine/extend/plugins_volume/
- [experimental S3 volume plugin](http://blog.scottlogic.com/2016/05/30/writing-a-docker-volume-plugin.html)
- [fake volume plugin example](http://blog.csdn.net/halcyonbaby/article/details/47325177)

# Docker network plugin

Since docker network component has been moved to libnetwork; the plugin API is of course integrated
in libnetwork. Libnetwork provides a few builtin drivers, i.e. none, bridge, overlay, host, remote.
The remote driver is the 'plugin'. Remote driver provides the integration point for dynamically-registered
drivers. Unlike the other driver packages, it does not provide a single implementation  of a driver;
rather, it provides a proxy for remote driver processes, which are registered and communicate with
libnetwork via the Docker plugin package.

*References*

- https://github.com/docker/libnetwork/blob/master/docs/remote.md
- https://docs.docker.com/engine/extend/plugins_network/

# Docker IPAM plugin

*References*

- https://github.com/docker/libnetwork/blob/master/docs/ipam.md

# Docker auth plugin

You are responsible for registering your plugin as part of the Docker daemon startup. You can install
multiple plugins and chain them together. This chain can be ordered. Each request to the daemon passes
in order through the chain. Only when all the plugins grant access to the resource, is the access
granted.

When an HTTP request is made to the Docker daemon through the CLI or via the Engine API, the
authentication subsystem passes the request to the installed authentication plugin(s). The request
contains the user (caller) and command context. The plugin is responsible for deciding whether to
allow or deny the request. Each plugin should implement the following two methods:
- /AuthZPlugin.AuthZReq: This method is called before the Docker daemon processes the client request.
- /AuthZPlugin.AuthZRes: This method is called before the response is returned from Docker daemon to the client.

*References*

- https://docs.docker.com/engine/extend/plugins_authorization/
