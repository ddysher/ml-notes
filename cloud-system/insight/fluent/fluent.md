<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Fluentd](#fluentd)
- [Fluentbit](#fluentbit)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Fluentd

*Date: 12/08/2017, fluentd v1*

[Fluentd](https://github.com/fluent/fluentd) is an event agent which reads configurations about
input sources, output endpoints, filters, tags, etc, and start forwarding from inputs to outputs
with filters, tags applied. The core idea of Fluentd is to be the unifying layer between different
types of log inputs and outputs.

From GitHub:

> Fluentd collects events from various data sources and writes them to files, RDBMS, NoSQL, IaaS,
> SaaS, Hadoop and so on. Fluentd helps you unify your logging infrastructure.

> An event consists of tag, time and record. Tag is a string separated with '.' (e.g. myapp.access).
> It is used to categorize events. Time is a UNIX time recorded at occurrence of an event. Record is
> a JSON object.

Fluentd is written in Ruby with performance critical path in C. On average, fluentd processes around
10000~15000 lines/s, using around 200~300M memory.

Process Model: when you launch fluentd, it creates two processes: supervisor and worker. The supervisor
process controls the life cycle of the worker process. Please make sure to send any signals to the
supervisor process.

*References*

- [fluentd example config](https://github.com/fluent/fluentd/tree/v1.2.6/example)
- https://www.fluentd.org/architecture
- https://docs.fluentd.org/v1.0/articles/plugin-development

# Fluentbit

*Date: 12/08/2017, fluentbit v0.12*

[Fluentbit](https://github.com/fluent/fluent-bit) is written in C with low memory footprint (~150KB
vs ~20MB in fluentd). Fluentbit has similar architecture as fluentd with different use cases, targeting
at Embedded & IoT devices.

Fluentbit is not a replacement of fluentd, in fact, it's common to setup fluentbit on each host as
log forwarder, and setup central fluentd instances as log aggregator, i.e.

```
fluentbit --
             \
fluentbit ---- fluentd
             /
fluentbit --
```

- http://fluentbit.io/documentation/0.12/about/fluentd_and_fluentbit.html
- https://logz.io/blog/fluentd-vs-fluent-bit/
