<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [NATS Server](#nats-server)
  - [Overview](#overview-1)
  - [Messaging Model](#messaging-model)
  - [Clustering](#clustering)
- [NATS Streaming](#nats-streaming)
  - [Overview](#overview-2)
  - [Features](#features)
  - [Clustering](#clustering-1)
  - [Fault Tolerance](#fault-tolerance)
  - [Partitioning](#partitioning)
- [Implementation](#implementation)
  - [Protocol](#protocol)
  - [NATS Server Implementation](#nats-server-implementation)
- [Tools](#tools)
  - [nats-top](#nats-top)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

NATS is an open-source, cloud-native messaging system. The core principles underlying NATS are
performance, scalability, and ease-of-use. Based on these principles, NATS is designed around the
following core features:
- Highly performant (fast)
- Always on and available (dial tone)
- Extremely lightweight (small footprint)
- Support for multiple qualities of service (including guaranteed “at-least-once” delivery with NATS Streaming)
- Support for various messaging models and use cases (flexible)

NATS server is a single binary, and can be extended with NATS streaming. For more information, see
(pay attention to use case section): https://nats.io/documentation/

# NATS Server

*Date: 04/05/2018, v1.1.0*

## Overview

https://nats.io/documentation/server/gnatsd-intro/

## Messaging Model

NATS provide three basic messaging models: PubSub, Queueing and Req/Reply.

## Clustering

Clustering allows multiple NATS server to form a mesh for better processing ability and fault tolerance.
Suppose that server srvA is connected to server srvB. A bi-directional route exists between srvA and
srvB. A new server, srvC, connects to srvA. When accepting the connection, srvA will gossip the address
of srvC to srvB so that srvB connects to srvC, completing the full mesh. The URL that srvB will use
to connect to srvC is the result of the TCP remote address that srvA got from its connection to srvC.

After forming the cluster, client can connect to any of the NATS instance. Note that NATS clustered
servers have a forwarding limit of one hop. This means that each gnatsd instance will only forward
messages that it has received from a client to the immediately adjacent gnatsd instances to which it
has routes. Messages received from a route will only be distributed to local clients. Therefore a full
mesh cluster, or complete graph, is recommended for NATS to function as intended and as described
throughout the documentation.

Pay attention here, message is forwarded between different NATS instance, not via client redirecting,
etc. The interest graph (subscriptions) propagates automatically across servers so messages are only
sent when they are needed on the remote server and they are sent once regardless of the interest on
the other side. Since interest propagates automatically at subscribe time there is no need to poll,
servers know which other servers they need to forward the message to.

*References*

- https://groups.google.com/forum/#!topic/natsio/eFvk7nQTb4c
- https://groups.google.com/forum/#!topic/natsio/8UMX5sXeXa8
- https://github.com/nats-io/gnatsd/issues/303

# NATS Streaming

*Date: 04/05/2018, v0.9.2*

## Overview

[NATS Streaming](https://nats.io/documentation/streaming/nats-streaming-intro/) embeds, extends, and
interoperates seamlessly with the core NATS platform (NATS server). When you run the NATS Streaming
Server, the embedded NATS Server is automatically started and listening for client connections on the
default port 4222. Hence you don’t need to manually run the NATS server with NATS Streaming. Because
of this, NATS Streaming also has its own client library, separated from NATS Server client.

## Features

NATS Streaming provides several core features seen in messaging systems that are not provided in NATS
Server, e.g.
- At-least-once-delivery
- Durable subscriptions
- Historical message replay by subject

NATS Streaming can persist state in memory, file or SQL, depending on startup option.

## Clustering

NATS Streaming Server supports clustering and data replication, implemented with the Raft consensus
algorithm, for the purposes of high availability. The setup is similar to etcd and zookeeper, where
each node has an ID and forms a quorum.

*References*

- https://github.com/nats-io/nats-streaming-server/tree/v0.9.2#clustering

## Fault Tolerance

To minimize the single point of failure, NATS Streaming server can be run in Fault Tolerance mode.
It works by having a group of servers with one acting as the active server (accessing the store) and
handling all communication with clients, and all others acting as standby servers. Note this
active-standby mode is different from clustering.

*References*

- https://github.com/nats-io/nats-streaming-server/tree/v0.9.2#fault-tolerance

## Partitioning

It is possible to limit the list of channels a server can handle; that is, split all channels to
different servers, e.g. server A handles "foo.*" while server B handles "bar.*". Partitioning can
work together with fault tolerance mode; for example, we can run four NATS streaming servers, two
of them handle "foo.*" with active-standby mode, the other two of them handle "bar.*" with
active-standby mode as well.

*References*

- https://github.com/nats-io/nats-streaming-server/tree/v0.9.2#partitioning

# Implementation

## Protocol

- https://nats.io/documentation/internals/nats-protocol/
- https://nats.io/documentation/internals/nats-server-protocol/

## NATS Server Implementation

For every client, server spawns two goroutines: one blocks on reading data from client, the other
blocks on writing data to client, all via the same tcp connection.

Once NATS server receives data from a client, it uses a parser to parse input data. As mentioned in
NATS document, NATS has a simple text-based protocol on top of TCP - the parser will parse the input
for both control message and user data.

Internally, NATS doesn't differentiates publisher or subscriber: everything is connection from clients.
You can subscribe to multiple topics as well as publishing topics in a single client. NATS connection
with one client tracks pending clients that have data to be flushed after nats processes inbound msgs
from a connection, based on subscriptions.

# Tools

## nats-top

- https://nats.io/documentation/tutorials/nats-top/
- http://github.com/nats-io/nats-top
