<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Components](#components)
  - [Whisper](#whisper)
  - [Carbon](#carbon)
  - [Graphite-Web](#graphite-web)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Graphite does two things:
- Store numeric time-series data
- Render graphs of this data on demand

Graphite is not a collection agent, it is usually used with statsD (mostly for application metrics)
and collectd (mostly for system metrics). Graphite consists of three software components (written in
Python):
- carbon: a high-performance service that listens for time-series data
- whisper: a simple database library for storing time-series data
- graphite-web: Graphite's user interface & API for rendering graphs and dashboards

Metrics get fed into the stack via the Carbon service, which writes the data out to Whisper databases
for long-term storage. Users interact with the Graphite web UI or API, which in turn queries Carbon
and Whisper for the data needed to construct the requested graphs.

# Components

## Whisper

Whisper is a fixed-size database, similar in design and purpose to RRD (round-robin-database). It
provides fast, reliable storage of numeric data over time. Data points in Whisper are stored on-disk
as big-endian double-precision floats. Each value is paired with a timestamp in seconds since the
UNIX Epoch (01-01-1970). Whisper databases contain one or more archives, each with a specific data
resolution (seconds per point) and retention (defined in number of points or max timestamp age).

Note, Whisper is not a daemon process, but rather a database library. Whisper uses Python's `struct`
module to store data on disk; following is the basic layout:

```
File = Header,Data
  Header = Metadata,ArchiveInfo+
      Metadata = aggregationType,maxRetention,xFilesFactor,archiveCount
      ArchiveInfo = Offset,SecondsPerPoint,Points
  Data = Archive+
      Archive = Point+
          Point = timestamp,value
```

## Carbon

Carbon is responsible for receiving metrics over the network, caching them in memory for "hot queries"
from the Graphite-Web application, and persisting them to disk using the Whisper time-series library.
It is written in Python with twisted library.
- carbon-cache.py accepts metrics over various protocols and writes them to disk as efficiently as
  possible. [required]
- carbon-relay.py serves two distinct purposes: replication and sharding. [optional]
- carbon-aggregator.py can be run in front of carbon-cache.py to buffer metrics over time before
  reporting them into whisper. [optional]

## Graphite-Web

Graphite-Web is a Django-based web application that renders graphs and dashboards.

# References

- https://graphiteapp.org/
- https://github.com/graphite-project/
- http://www.aosabook.org/en/graphite.html
