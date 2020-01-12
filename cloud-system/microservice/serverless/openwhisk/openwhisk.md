<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Apache OpenWhisk (Incubating) is an open source, distributed Serverless platform that executes functions
(fx) in response to events at any scale. OpenWhisk manages the infrastructure, servers and scaling using
Docker containers so you can focus on building amazing and efficient applications.

The OpenWhisk platform supports a programming model in which developers write functional logic (called
`Actions`), in any supported programming language, that can be dynamically scheduled and run in response
to associated events (via `Triggers`) from external sources (`Feeds`) or from HTTP requests. The project
includes a REST API-based Command Line Interface (CLI) along with other tooling to support packaging,
catalog services and many popular container deployment options.

OpenWhisk itself mainly consists of only two custom components: the `Controller` and the `Invoker`.
Everything else is already there, i.e. Nginx, Kafka, Docker, CouchDB, Consul.

# References

- https://thenewstack.io/behind-scenes-apache-openwhisk-serverless-platform/
- https://github.com/apache/incubator-openwhisk/blob/0.9.0-incubating/docs/about.md
