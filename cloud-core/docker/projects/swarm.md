<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
- [Workflow](#workflow)
- [Scheduling](#scheduling)
- [Overlay with swarm (docker 1.11)](#overlay-with-swarm-docker-111)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 07/23/2016

Docker Swarm is native clustering for Docker. It turns a pool of Docker hosts into a single, virtual
Docker host. Because Docker Swarm serves the standard Docker API, any tool that already communicates
with a Docker daemon can use Swarm to transparently scale to multiple hosts.

# Architecture

<p align="center"><img src="./assets/swarm-architecture.jpg" height="480px" width="auto"></p>

As shown in the diagram, swarm cluster consists of master and node. All docker operations go through
swarm master. The master has scheduler, discovery service, etc. Master alse uses docker APIs to dispatch
work to swarm nodes.

# Workflow

**Run/configure docker engine**

In order for swarm master to dispatch work, node docker daemon must listen on tcp port, e.g.

     $ sudo docker daemon -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock

**Setup a discovery backend**

The Swarm managers and nodes use this backend to authenticate themselves as members of the cluster.
The Swarm managers also use this information to identify which nodes are available to run containers.
In production, we should run a dedicate backend store, e.g. using consul:

     $ docker run -d -p 8500:8500 --name=consul progrium/consul -server -bootstrap

During test/dev, it's also possible to use dockerhub hosted discovery:

     $ docker run --rm swarm create

This will contact dockerhub and generate a token for us. There are other discovery backends as well,
e.g. etcd, zookeeper, static file, etc.

**Create swarm master**

After creating the discovery backend, we can create the Swarm managers.

     $ docker run -d -p 4000:4000 swarm manage -H :4000 --replication \
         --advertise <manager0_ip>:4000 consul://<consul_ip>:8500

Where `manager0_ip` is the master's ip address, while `consul_ip` is the ip of the instance running
consul (usually the same as master). Note if we use token as our discovery backend, we need to use:

     $ docker run -d -p 4000:4000 swarm manage -H :4000 --replication \
         --advertise <manager0_ip>:4000 token://<token_value>

**Join swarm node**

Adding swarm node into the cluster is easy, just run a docker container.

     $ docker run -d swarm join --advertise=<node_ip>:2375 consul://<consul_ip>:8500

This will create an entry in the discovery backend. Note the container is running as daemon.

**Communicate with swarm cluster**

When all hosts are registered, we'll start the management API with `swarm manage`. Run the command
locally will start a local swarm manager:

     $ swarm manage --discovery=token://TOKEN --host=0.0.0.0:4243

This will start a local swarm manager on port 4243, when running containers, supply this address to
docker client, e.g.

     $ docker run -H 0.0.0.0:4243 -d -P run nginx

All of the above commands are running on local machine. On the other hands, we can issue commands on
the master, e.g.

     $ docker -H :4000 info

Note if using TLS, swarm, docker commands both need tls flag: https://github.com/docker/swarm/issues/296

# Scheduling

**Strategies**

The Docker Swarm scheduler features multiple strategies for ranking nodes. The strategy we choose
determines how Swarm computes ranking. To choose a ranking strategy, pass the `--strategy` flag and
a strategy value to the swarm manage command. That is, strategy is defined at cluster level - when
we the manager is created.

**Filters**

Filters tell Docker Swarm scheduler which nodes to use when creating and running a container. Filters
are divided into two categories, node filters and container configuration filters. Node filters operate
on characteristics of the Docker host or on the configuration of the Docker daemon. Container
configuration filters operate on characteristics of containers, or on the availability of images on
a host.

**Rescheduling**

A rescheduling policy determines what the Swarm scheduler does for containers when the nodes they are
running on fail. Reschedule policy is set when starting a container: can be done using the reschedule
environment variable or the `com.docker.swarm.reschedule-policies` label. e.g.

     $ docker run -d -e reschedule:on-node-failure redis
     $ docker run -d -l 'com.docker.swarm.reschedule-policies=["on-node-failure"]' redis

*References*

- https://docs.docker.com/swarm/scheduler/strategy/
- https://docs.docker.com/swarm/scheduler/filter/
- https://docs.docker.com/swarm/scheduler/rescheduling/
- https://docs.docker.com/swarm/scheduler/

# Overlay with swarm (docker 1.11)

To connect containers across different hosts in a swarm cluster, we can use docker's overlay networking,
for details, see ./network.md. In short, it is as easy as:

    $ docker network create --driver overlay --subnet=10.0.9.0/24 my-net
    $ docker run -itd --name=web --network=my-net --env="constraint:node==mhs-demo0" nginx
    $ docker run -it --rm --network=my-net --env="constraint:node==mhs-demo1" busybox wget -O- http://web

Assuming docker is connected to swarm master.

*References*

- https://docs.docker.com/engine/userguide/networking/get-started-overlay/
