<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Architecture](#architecture)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Apache Flume is a distributed, reliable, and available system for efficiently collecting, aggregating
and moving large amounts of log data from many different sources to a centralized data store.

The use of Apache Flume is not only restricted to log data aggregation. Since data sources are
customizable, Flume can be used to transport massive quantities of event data including but not
limited to network traffic data, social-media-generated data, email messages and pretty much any
data source possible.

It's easier to understand flume if we compare it with two different types of system
- fluend or logstash
- kafka

**vs logstash/fluentd**

logstash/fluentd is log collection and aggregation agent.

**vs kafka**

For kafka, here is a [comparison](https://www.quora.com/What-are-the-most-significant-differences-between-Flume-and-Kafka-as-a-messaging-backbone-with-Hbase-or-Cassandra-clusters-as-syncs/answer/Allen-Wittenauer).
In short, kafka is more general than flume. Kafka can be used anywhere when distributed messaging
and pub-sub are needed; where as flume is built around hodoop ecosystem with the primary goal to
sink data into hdfs.

One of the key difference is that with kafka you pull data, so each consumer has and manages it's
own read pointer, which allows a large number of consumers of each kafka queue, that pull data at
their own pace; whereas flume pushes data to sinks, so it must keep track of push state, also,
configuration are needed in order to push data to different sinks.

# Architecture

The architecture of flume is simple, the core agent has three components:
- source: source can either receives data from client, e.g. arvo source where arvo client send data
  to agent, or proactively parses data, e.g. log directory source where agent parses log files.
- channel: channel is a passive store that keeps the event until it's consumed by a flume sink, e.g.
  file channel is backed by local file, memory channel is backed by agent memory.
- sink: sink removes the event from the channel and puts it into different sinks, e.g. to HDFS via
  flume HDFS sink, or forwards it to the Flume source of the next Flume agent (next hop) in the flow.

In the simplest scenario, we have a dataflow:

<p align="center"><img src="./assets/dataflow.png" height="200" width="auto"></p>

A multi-agent flow:

<p align="center"><img src="./assets/multistage.png" height="120" width="auto"></p>

A consolidation flow:

<p align="center"><img src="./assets/consolidation.png" height="320" width="auto"></p>

A multiplexing flow

<p align="center"><img src="./assets/multiplexing.png" height="360" width="auto"></p>

# Experiment

Download flume and start it using example configuration:

```
cp ./experiments/example.conf /tmp

# Under flume distribution directory
./bin/flume-ng agent --conf conf --conf-file /tmp/example.conf --name a1 -Dflume.root.logger=INFO,console
```

In another terminal, start telnet:

```
telnet localhost 44444
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
```

Now that if we type in telnet, we'll see output from flume's stdout.
