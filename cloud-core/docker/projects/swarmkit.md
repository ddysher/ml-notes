<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
- [Loadbalance](#loadbalance)
- [Workflow (docker swarm)](#workflow-docker-swarm)
- [Workflow (swarmctl)](#workflow-swarmctl)
- [swarmkit vs swarm](#swarmkit-vs-swarm)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 08/01/2016*

SwarmKit is a toolkit for orchestrating distributed systems at any scale. It includes primitives for
node discovery, raft-based consensus, task scheduling and more. SwarmKit is tightly integrated with
Docker Engine, and it's not running as a separate daemon or process; rather, docker codebase imports
swarmkit as a library. However, you can also use swarmkit in standalone mode, that is, using binaries
`swarmd`, `swarmctl`. In fact, `swarmctl` is a subset of `docker` commands, e.g. both of them has
`node` subcommand:

      deyuandeng at Deyuans-MacBook-Pro in ~/code/workspace/src/github.com/docker/swarmkit on master
      $ docker service

      Usage:  docker service COMMAND

      Manage Docker services

      Options:
            --help   Print usage

      Commands:
        create      Create a new service
        inspect     Inspect a service
        tasks       List the tasks of a service
        ls          List services
        rm          Remove a service
        scale       Scale one or multiple services
        update      Update a service

      Run 'docker service COMMAND --help' for more information on a command.

      deyuandeng at Deyuans-MacBook-Pro in ~/code/workspace/src/github.com/docker/swarmkit on master
      $ ./bin/swarmctl service
      Service management

      Usage:
        ./bin/swarmctl service [command]

      Aliases:
        service, svc


      Available Commands:
        inspect     Inspect a service
        ls          List services
        create      Create a service
        update      Update a service
        remove      Remove a service

      Flags:
        -h, --help   help for service

      Global Flags:
        -n, --no-resolve      Do not try to map IDs to Names when displaying them
        -s, --socket string   Socket to connect to the Swarm manager (default "./swarmkitstate/swarmd.sock")

      Use "./bin/swarmctl service [command] --help" for more information about a command.

Similar to swarm, swarmkit also use master and nodes architecture. See: https://docs.docker.com/engine/swarm/

# Architecture

Looks similar to kubernetes in some aspects, apart from:
- Built-in raft for master to master communication , and there is no need for an external store like
  etcd. Read is primarily from cache, similar to k8s; but write is batched and performed only when
  necessary. Quote:
- Workers uses gossip network to communicate with each other. A node accepts a task, starts a container
  and then it tells the other nodes that a container has started on the specified overlay network.
  Master to node communication uses gRPC.

Quote:

> Caching gives fast reads, but what happens when a write comes in? Of course the cache on each machine
> must be invalidated and updated.  Our solution to that problem was to design the rest of the
> orchestration system in ways that are read-intensive but only write to the Raft store when absolutely
> necessary.

*References*

- https://blog.docker.com/2016/07/docker-built-in-orchestration-ready-for-production-docker-1-12-goes-ga/

# Loadbalance

**DNS based load balance**

When query, DNS based load balance returns all backends that resolve to the DNS name. However, caution
must be taken to avoid destination address selection.

**VIP based load balance**

Concept is similar to kubernetes: a VIP mapped to various backends, while DNS resolves to the virtual IP.

    root@node1:/var/run/docker/netns# iptables -nvL -t mangle
    Chain OUTPUT (policy ACCEPT 2265 packets, 189K bytes)
     pkts bytes target     prot opt in     out     source               destination
       14   880 MARK       all  --  *      *       0.0.0.0/0            10.0.0.4             MARK set 0x117
        0     0 MARK       all  --  *      *       0.0.0.0/0            10.0.0.2             MARK set 0x10b
        0     0 MARK       all  --  *      *       0.0.0.0/0            10.0.0.2             MARK set 0x116

    Chain POSTROUTING (policy ACCEPT 2251 packets, 188K bytes)
     pkts bytes target     prot opt in     out     source               destination

    root@node1:/var/run/docker/netns# ipvsadm
    IP Virtual Server version 1.2.1 (size=4096)
    Prot LocalAddress:Port Scheduler Flags
      -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
    FWM  267 rr
      -> 10.0.0.3:0                   Masq    1      0          0
    FWM  278 rr
      -> 10.0.0.3:0                   Masq    1      0          0
    FWM  279 rr
      -> 10.0.0.5:0                   Masq    1      0          0
      -> 10.0.0.6:0                   Masq    1      0          0

Here, 10.0.0.4 service IP gets marking of 0x117(279) using iptables OUTPUT chain. ipvs uses this
marking and load balances it to containers 10.0.0.5 and 10.0.0.6.

**Routing mesh**

Using routing mesh, the exposed service port gets exposed in all the worker nodes in the Swarm cluster.
All nodes belongs to an overlay network called `ingress`, and all exposed services are also added to
the overlay network.

    vagrant@server1:~$ docker network ls
    NETWORK ID          NAME                DRIVER              SCOPE
    80f60e4f706e        bridge              bridge              local
    29f5b984821f        docker_gwbridge     bridge              local
    b5ca878ac83b        host                host                local
    byazsxl6fdyn        ingress             overlay             swarm
    b8c8aad692d8        none                null                local

E.g. if a service exposes port 8080, then an iptable rule is created in all nodes which redirect the
traffic to "ingress" overlay network; then ipvs module will then load balance the traffic to containers
using their endpoints in "ingress" overlay network.

*References*

- https://sreeninet.wordpress.com/2016/07/29/service-discovery-and-load-balancing-internals-in-docker-1-12/

# Workflow (docker swarm)

Compared with swarm, working with swarmkit is simpler as it is built into docker and a lot of setup
processes have been automated.

**Init swarm manager**

On master, run:

    $ docker swarm init

**Join cluster**

On nodes, run:

    $ docker swarm join HOST:PORT

**Playing with swarm cluster**

On master, we can now play with swarm cluster:

     $ docker node ls
     $ docker service create --replicas 1 --name helloworld alpine ping docker.com
     $ docker service ls

*References*

- https://docs.docker.com/engine/swarm/swarm-tutorial/
- http://www.skippbox.com/swarm-reboot-in-docker-1-12/

# Workflow (swarmctl)

**Run swarmd daemon on master**

    $ swarmd -d /tmp/node-1 --listen-control-api /tmp/manager1/swarm.sock --hostname node-1

**Run swarmd daemon on nodes**

    $ swarmd -d /tmp/node-2 --hostname node-2 --join-addr master:4242
    $ swarmd -d /tmp/node-3 --hostname node-3 --join-addr master:4242

**List nodes**

    $ export SWARM_SOCKET=/tmp/manager1/swarm.sock
    $ swarmctl node ls

*References*

- https://github.com/docker/swarmkit
- https://blog.replicated.com/2016/06/08/first-look-at-swarmkit/

# swarmkit vs swarm

Docker swarm is a standalone project for orchestration. Some articles about the differences:
- https://github.com/docker/swarmkit
- http://stackoverflow.com/questions/38474424/the-relation-between-docker-swarm-and-docker-swarmkit/38483429
- https://sreeninet.wordpress.com/2016/07/14/comparing-swarm-swarmkit-and-swarm-mode/

The basic difference is that in swarm, you must run swarm agents in every node (master or node) to
form a swarm cluster. The agents will coordinate and talk to docker engine for running container. In
swarm, docker engine doesn't care about any orchestration, as if it is running alone.

However, in swarmkit, docker daemon coordinates with each other to form the cluster. It has builtin
raft consensus, filtering, scheduling capabilities etc. There is no need for any agents.
